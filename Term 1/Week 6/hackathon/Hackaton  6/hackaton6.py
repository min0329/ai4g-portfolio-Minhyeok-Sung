import hashlib, html, json, re, sqlite3, sys, threading, time
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo
import pandas as pd
DB = Path(__file__).resolve().with_name('database.db')
MODEL = 'cardiffnlp/twitter-xlm-roberta-base-sentiment'
PRODUCTS = ['ChatGPT', 'Claude', 'Gemini']
LABELS = ['negative', 'neutral', 'positive']
APPS = dict(zip(PRODUCTS, ['6448311069', '6473753684', '6477489729']))
SOURCES = ['Bluesky', 'Hacker News', 'App Store']
FILTER = "(p.id LIKE 'bsky:%' OR p.id LIKE 'hn:%' OR p.id LIKE 'appstore:%')"
LOCAL_TZ = ZoneInfo('Europe/Amsterdam')
def now():
    return datetime.now(timezone.utc)
def database():
    db = sqlite3.connect(DB, timeout=30)
    db.execute('PRAGMA journal_mode=WAL')
    db.executescript('\n        CREATE TABLE IF NOT EXISTS posts(\n            id TEXT PRIMARY KEY,project TEXT,kind TEXT,issue_number INTEGER,\n            created_at TEXT,updated_at TEXT,collected_at TEXT,text TEXT,\n            text_hash TEXT,source_url TEXT,is_history INTEGER);\n        CREATE TABLE IF NOT EXISTS sentiments(\n            post_id TEXT PRIMARY KEY,label TEXT,score REAL,model TEXT,\n            text_hash TEXT,analysed_at TEXT,truncated INTEGER);\n        CREATE TABLE IF NOT EXISTS ig_explanations(\n            post_id TEXT,model TEXT,text_hash TEXT,method TEXT,status TEXT,\n            payload TEXT,error TEXT,requested_at TEXT,\n            PRIMARY KEY(post_id,model,text_hash,method));\n        CREATE TABLE IF NOT EXISTS state(key TEXT PRIMARY KEY,value TEXT);\n        CREATE TABLE IF NOT EXISTS source_polls(\n            id INTEGER PRIMARY KEY AUTOINCREMENT,source TEXT,timestamp TEXT,\n            success INTEGER,new_posts INTEGER,edited_posts INTEGER,message TEXT);\n    ')
    if "priority" not in {row[1] for row in db.execute("PRAGMA table_info(ig_explanations)")}:
        db.execute("ALTER TABLE ig_explanations ADD COLUMN priority INTEGER DEFAULT 0")
    db.commit()
    return db
def state(db, key, value=None):
    if value is not None:
        db.execute('INSERT OR REPLACE INTO state VALUES(?,?)', (key, value))
        db.commit()
    row = db.execute('SELECT value FROM state WHERE key=?', (key,)).fetchone()
    return row[0] if row else None
class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
    def handle_data(self, data):
        self.parts.append(data)
    def handle_starttag(self, tag, attrs):
        if tag in ('p', 'br', 'div'):
            self.parts.append(' ')
def clean(text):
    text = re.sub('<!--[\\s\\S]*?-->|```[\\s\\S]*?```', ' ', text or '')
    text = re.sub('[\\w.+-]+@[\\w.-]+\\.[A-Za-z]{2,}', '[email]', text)
    text = re.sub('(?<!\\w)@[\\w.-]+', '@user', text)
    text = re.sub('https?://\\S+', 'http', text)
    return re.sub('\\s+', ' ', text).strip()
def products(text):
    context = re.search('\\b(ai|llm|chatbots?|assistants?|prompts?|tokens?|coding|chatgpt|openai|anthropic|sonnet|opus|haiku|google|deepmind|flash|models?)\\b', text, re.I)
    context = context or (re.search('\\bclaude\\b', text, re.I) and re.search('\\bgemini\\b', text, re.I) and re.search('\\b(vs|versus|better|worse|prefer|compare)\\b', text, re.I))
    found = ['ChatGPT'] if re.search('\\bchat\\s*gpt\\b', text, re.I) else []
    for name, excluded in [('Claude', '\\b(monet|debussy|van\\s*damme)\\b'), ('Gemini', '\\b(horoscopes?|zodiac|astrology|constellation|exchange)\\b')]:
        if context and re.search('\\b' + name + '\\b', text, re.I):
            if not re.search(excluded, text, re.I):
                found.append(name)
    return found
def fetch(url, **params):
    request = Request(url + ('?' + urlencode(params) if params else ''), headers={'User-Agent': 'AIReceptionPulse/1.0'})
    with urlopen(request, timeout=30) as response:
        result = json.load(response)
    time.sleep(0.2)
    return result
def search(source, query, start, end):
    if source == 'Bluesky':
        data = fetch('https://api.bsky.app/xrpc/app.bsky.feed.searchPosts', q=query, lang='en', sort='latest', limit=100, since=start.isoformat(), until=end.isoformat())
        full = len(data.get('posts', [])) >= 100
    else:
        params = dict(query=query, tags='comment', hitsPerPage=100, numericFilters=f'created_at_i>={int(start.timestamp())},created_at_i<={int(end.timestamp())}')
        data = fetch('https://hn.algolia.com/api/v1/search_by_date', **params, page=0)
        full = data.get('nbHits', 0) >= 1000
    if full:
        left, right = (int(start.timestamp()), int(end.timestamp()))
        if right - left <= 2:
            raise RuntimeError('Search window full; cursor not advanced.')
        boundary = datetime.fromtimestamp((left + right) // 2, timezone.utc)
        yield from search(source, query, start, boundary)
        next_start = boundary if source == 'Bluesky' else boundary + timedelta(seconds=1)
        yield from search(source, query, next_start, end)
    elif source == 'Bluesky':
        for item in data.get('posts', []):
            uri, record = (item['uri'], item['record'])
            parts = uri.split('/')
            yield ('bsky:' + hashlib.sha256(uri.encode()).hexdigest(), record['text'], record['createdAt'], f'https://bsky.app/profile/{parts[2]}/post/{parts[4]}')
    else:
        for page in range(data.get('nbPages', 0)):
            batch = data if page == 0 else fetch('https://hn.algolia.com/api/v1/search_by_date', **params, page=page)
            for item in batch.get('hits', []):
                parser = Text()
                parser.feed(item.get('comment_text') or '')
                yield ('hn:' + item['objectID'], html.unescape(''.join(parser.parts)), item['created_at'], 'https://news.ycombinator.com/item?id=' + item['objectID'])
def reviews(product):
    app = APPS[product]
    entries = fetch(f'https://itunes.apple.com/us/rss/customerreviews/id={app}/sortBy=mostRecent/json').get('feed', {}).get('entry', [])
    for item in [entries] if isinstance(entries, dict) else entries:
        if 'im:rating' in item and item.get('updated') and item.get('id'):
            text = item.get('title', {}).get('label', '') + ' ' + item.get('content', {}).get('label', '')
            yield ('appstore:' + app + ':' + item['id']['label'], text, item['updated']['label'], f'https://apps.apple.com/us/app/id{app}?see-all=reviews')
def save(db, item, source, product, started):
    identifier, raw, timestamp, url = item
    text = clean(raw)
    mentioned = set(products(text)) | ({product} if source == 'App Store' else set())
    if not text or not mentioned:
        return 'excluded'
    stamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    if stamp > now() + timedelta(minutes=5):
        return 'excluded'
    topic = next(iter(mentioned)) if len(mentioned) == 1 else 'Comparisons'
    digest = hashlib.sha256(text.encode()).hexdigest()
    old = db.execute('SELECT text_hash FROM posts WHERE id=?', (identifier,)).fetchone()
    if old and old[0] == digest:
        return 'duplicate'
    if old:
        db.execute('UPDATE posts SET text=?,text_hash=?,project=?,updated_at=? WHERE id=?', (text, digest, topic, now().isoformat(), identifier))
    else:
        kind = {'Bluesky': 'post', 'Hacker News': 'comment', 'App Store': 'review'}[source]
        db.execute('INSERT INTO posts VALUES(?,?,?,?,?,?,?,?,?,?,?)', (identifier, topic, kind, None, stamp.isoformat(), stamp.isoformat(), now().isoformat(), text, digest, url, int(stamp < datetime.fromisoformat(started))))
    db.commit()
    return 'edited' if old else 'new'
def collect(status):
    db = database()
    while True:
        for source in SOURCES:
            started = state(db, 'started:' + source) or state(db, 'started_at') or now().isoformat()
            state(db, 'started:' + source, started)
            errors, counts = ([], {'new': 0, 'edited': 0})
            for product in PRODUCTS:
                try:
                    key = ('cursor:' if source == 'Bluesky' else 'cursor:hn:') + product
                    cursor, end = (state(db, key), now())
                    start = datetime.fromisoformat(cursor) - timedelta(hours=1) if cursor else datetime.fromisoformat(started) - timedelta(hours=6)
                    items = reviews(product) if source == 'App Store' else search(source, product, start, end)
                    for item in items:
                        result = save(db, item, source, product, started)
                        if result in counts:
                            counts[result] += 1
                    if source != 'App Store':
                        state(db, key, end.isoformat())
                except Exception as error:
                    errors.append(product + ': ' + str(error)[:200])
            db.execute('INSERT INTO source_polls\n                   (source,timestamp,success,new_posts,edited_posts,message)\n                   VALUES(?,?,?,?,?,?)', (source, now().isoformat(), int(not errors), counts['new'], counts['edited'], '; '.join(errors) or 'ok'))
            db.commit()
            status['collector'] = 'Last source checked: ' + source + ' at ' + now().astimezone(LOCAL_TZ).strftime('%d %b %Y, %H:%M:%S %Z')
        time.sleep(300)
def load_model():
    from transformers import pipeline
    return pipeline('sentiment-analysis', model=MODEL, tokenizer=MODEL, device=-1)
def predict(model, texts):
    return model(texts, truncation=True, max_length=512, batch_size=4)
def analyse(status):
    model, db = (load_model(), database())
    status['model'] = 'Model ready; analysing automatically.'
    while True:
        rows = db.execute(f'\n            SELECT p.id,p.text,p.text_hash FROM posts p\n            LEFT JOIN sentiments s ON p.id=s.post_id\n            WHERE {FILTER} AND\n              (s.post_id IS NULL OR s.text_hash!=p.text_hash OR s.model!=?)\n            LIMIT 4\n        ', (MODEL,)).fetchall()
        results = predict(model, [row[1] for row in rows]) if rows else []
        for row, prediction in zip(rows, results):
            db.execute('INSERT OR REPLACE INTO sentiments VALUES(?,?,?,?,?,?,?)', (row[0], prediction['label'].lower(), prediction['score'], MODEL, row[2], now().isoformat(), int(len(model.tokenizer.encode(row[1])) > 512)))
        db.commit()
        queue_next_explanation(db)
        explain_requested(db, model)
        time.sleep(1 if rows else 5)
IG_METHOD = 'layer-ig-pad-fixed-position-v1'
def explain_integrated_gradients(pipeline, text):
    import torch
    from captum.attr import LayerIntegratedGradients
    tokenizer, model = (pipeline.tokenizer, pipeline.model)
    if not tokenizer.is_fast:
        raise ValueError('Integrated Gradients needs a fast tokenizer.')
    model.eval()
    device = next(model.parameters()).device
    encoded = tokenizer(text, return_tensors='pt', return_offsets_mapping=True, truncation=True, max_length=512)
    offsets = encoded.pop('offset_mapping')[0].tolist()
    ids = encoded['input_ids'].to(device)
    attention = encoded['attention_mask'].to(device)
    pad = tokenizer.pad_token_id
    if pad is None:
        raise ValueError('Tokenizer has no padding reference token.')
    baseline = ids.clone()
    for index, (start, end) in enumerate(offsets):
        if end > start:
            baseline[0, index] = pad
    positions = ids.ne(pad).long().cumsum(dim=1) * ids.ne(pad).long() + pad
    def forward(input_ids, attention_mask, position_ids):
        return model(input_ids=input_ids, attention_mask=attention_mask, position_ids=position_ids).logits
    with torch.no_grad():
        logits = forward(ids, attention, positions)
        target = int(logits.argmax(dim=-1).item())
        confidence = float(logits.softmax(dim=-1)[0, target])
    with torch.enable_grad():
        attribution, delta = LayerIntegratedGradients(forward, model.get_input_embeddings()).attribute(ids, baselines=baseline, additional_forward_args=(attention, positions), target=target, n_steps=32, internal_batch_size=2, return_convergence_delta=True)
    scores = attribution.sum(dim=-1)[0].detach().cpu().tolist()
    spans = [{'start': m.start(), 'end': m.end(), 'word': m.group(), 'value': 0.0} for m in re.finditer('\\S+', text)]
    for (start, end), score in zip(offsets, scores):
        if end <= start:
            continue
        overlaps = [(span, max(0, min(end, span['end']) - max(start, span['start']))) for span in spans]
        total = sum((length for _, length in overlaps))
        if total:
            for span, length in overlaps:
                span['value'] += float(score) * length / total
    covered_end = max((end for start, end in offsets), default=0)
    spans = [span for span in spans if span['start'] < covered_end]
    label = str(model.config.id2label[target]).lower()
    if label.startswith('label_'):
        label = LABELS[target]
    return {'label': label, 'confidence': confidence, 'spans': spans, 'covered_end': covered_end, 'delta': float(delta.item()), 'method': IG_METHOD}
def queue_next_explanation(db):
    """Automatically explain stored positive/negative messages, newest first."""
    db.execute(f"\n        INSERT OR IGNORE INTO ig_explanations\n        (post_id,model,text_hash,method,status,requested_at)\n        SELECT p.id,s.model,p.text_hash,?,'pending',? FROM posts p\n        JOIN sentiments s ON s.post_id=p.id AND s.text_hash=p.text_hash\n        WHERE {FILTER} AND s.model=? AND s.label IN ('positive','negative')\n          AND NOT EXISTS (\n            SELECT 1 FROM ig_explanations q WHERE q.post_id=p.id\n            AND q.model=s.model AND q.text_hash=p.text_hash AND q.method=?\n          )\n        ORDER BY p.created_at DESC LIMIT 1\n    ", (IG_METHOD, now().isoformat(), MODEL, IG_METHOD))
    db.commit()
DISPLAY_STOPWORDS = frozenset('\na an the is am are was were be been being and or but because if then than\nas at by for from in into of on to with it its this that these those\ni me my we us our you your he him his she her they them their\nwho which what when where why how have has had do does did\ncan could would should will may might must also just very so too\nde het een is zijn was waren en of maar omdat als dan dat dit die deze\nik mij mijn wij ons onze je jij jouw hij zij ze haar hun hen er\nvan voor met op aan naar om door bij uit ook nog wel wordt worden\nheb hebt heeft hebben kan kunnen zou zal moet wat wie hoe waar\n'.split())
def is_assistant_name(word):
    name = re.sub(r"[^a-z0-9]", "", word.casefold())
    names = {"chatgpt", "chat", "gpt", "claude", "gemini", "openai", "anthropic",
             "google", "deepmind", "sonnet", "opus", "haiku", "deepseek", "llama", "copilot"}
    return name in names or bool(re.fullmatch(
        r"(?:chatgpt|gpt|claude|gemini|sonnet|opus|haiku|deepseek|llama)[0-9][a-z0-9]*", name))

def contributing_word_counts(payloads, limit_per_message=5):
    """Count occurrences of the five strongest supporting words per message."""
    from collections import Counter
    counts = Counter()
    stop_words = DISPLAY_STOPWORDS
    for payload in payloads:
        result = json.loads(payload) if isinstance(payload, str) else payload
        contributions = Counter()
        occurrences = Counter()
        for span in result['spans']:
            word = span['word'].casefold().strip(' .,!?:;"\'’“”()[]{}<>/\\|*_#~')
            value = float(span['value'])
            if not word or is_assistant_name(word) or word.replace('’', "'") in stop_words or (not any((character.isalpha() for character in word))) or (value <= 0):
                continue
            contributions[word] += value
            occurrences[word] += 1
        strongest = sorted(contributions, key=lambda word: (-contributions[word], word))[:limit_per_message]
        for word in strongest:
            counts[word] += occurrences[word]
    return pd.DataFrame(sorted(counts.items(), key=lambda item: (-item[1], item[0])), columns=['Word', 'Occurrences'])
def sentiment_word_counts(payloads, sentiment, lexicon):
    """Filter the IG overview by lexical polarity, preserving its counts."""
    matching = [p for p in payloads
                if (json.loads(p) if isinstance(p, str) else p)["label"] == sentiment]
    table = contributing_word_counts(matching)
    direction = 1 if sentiment == "positive" else -1
    return table[table["Word"].map(lambda word: lexicon.get(word, 0) * direction > 0)].reset_index(drop=True)


def load_sentiment_lexicon():
    """Download VADER's published English word scores once; no extra package."""
    path = DB.with_name("vader_lexicon.txt")
    if not path.exists():
        url = "https://raw.githubusercontent.com/cjhutto/vaderSentiment/master/vaderSentiment/vader_lexicon.txt"
        with urlopen(Request(url, headers={"User-Agent": "AIReceptionPulse/1.0"}), timeout=20) as response:
            text = response.read().decode("utf-8")
        rows = [line.split("\t") for line in text.splitlines() if line.strip()]
        if len(rows) < 1000 or any(len(row) < 2 for row in rows):
            raise ValueError("Invalid VADER lexicon download.")
        temporary = path.with_suffix(".tmp")
        temporary.write_text(text, encoding="utf-8")
        temporary.replace(path)
    return {parts[0]: float(parts[1]) for line in path.read_text(encoding="utf-8").splitlines()
            if len(parts := line.split("\t")) >= 2}


def explain_requested(db, model):
    row = db.execute("SELECT q.post_id,p.text,p.text_hash FROM ig_explanations q JOIN posts p ON p.id=q.post_id AND p.text_hash=q.text_hash WHERE q.model=? AND q.method=? AND q.status='pending' ORDER BY q.priority DESC,q.requested_at LIMIT 1", (MODEL, IG_METHOD)).fetchone()
    if row is None:
        return
    try:
        result = explain_integrated_gradients(model, row[1])
        status, payload, error = ('done', json.dumps(result), None)
    except Exception as exc:
        status, payload, error = ('error', None, str(exc))
    db.execute('UPDATE ig_explanations SET status=?,payload=?,error=? WHERE post_id=? AND model=? AND text_hash=? AND method=?', (status, payload, error, row[0], MODEL, row[2], IG_METHOD))
    db.commit()
def baseline(text):
    words = re.findall('[a-z]+', text.lower())
    good = {'good', 'great', 'love', 'helpful', 'useful', 'better', 'easy', 'fast'}
    bad = {'bad', 'hate', 'broken', 'annoying', 'worse', 'slow', 'crash', 'useless'}
    score = sum((word in good for word in words)) - sum((word in bad for word in words))
    return 'positive' if score > 0 else 'negative' if score < 0 else 'neutral'
def read_labels(path):
    frame = pd.read_csv(path, sep=None, engine='python', encoding='utf-8-sig', keep_default_na=False)
    frame.columns = frame.columns.str.strip().str.lstrip('\ufeff')
    cleaned = pd.DataFrame(index=frame.index)
    for index, column in enumerate(frame.columns):
        if not column or column.lower().startswith('unnamed'):
            continue
        name = re.sub('\\.\\d+$', '', column)
        if name.lower() == 'human explanation':
            name = 'explanation'
        values = frame.iloc[:, index].astype(str)
        if name not in cleaned:
            cleaned[name] = values
        else:
            empty = cleaned[name].str.strip().eq('')
            cleaned.loc[empty, name] = values.loc[empty]
    return cleaned
def test():
    db, path = (database(), DB.with_name('human_labels.csv'))
    if '--make-test' in sys.argv:
        if path.exists():
            db.close()
            raise ValueError('Preserve existing labels; rename the CSV first.')
        frame = pd.read_sql_query(f'\n            SELECT p.id AS post_id,p.project AS topic,p.text,p.source_url\n            FROM posts p WHERE {FILTER} ORDER BY p.id\n        ', db)
        db.close()
        if len(frame) < 50:
            raise ValueError('Collect at least 50 items first.')
        frame = frame.sample(min(75, len(frame)), random_state=42)
        frame['relevant'], frame['human_label'], frame['explanation'] = ('', '', '')
        frame.to_csv(path, index=False, encoding='utf-8-sig')
        print('Fill relevant=yes/no and human_label=positive/neutral/negative.')
        print('Keep IDs and text unchanged. Write your reasoning in explanation.')
        return
    position = sys.argv.index('--test') + 1
    try:
        frame = read_labels(sys.argv[position] if position < len(sys.argv) else path)
        required = {'post_id', 'text', 'relevant', 'human_label'}
        if (missing := (required - set(frame.columns))):
            raise ValueError(f'Missing columns: {sorted(missing)}')
        frame['relevant'] = frame['relevant'].str.strip().str.lower()
        if frame['post_id'].duplicated().any():
            raise ValueError('Unique post IDs required.')
        if not frame['relevant'].isin(['yes', 'no']).all():
            raise ValueError('Fill relevant with yes/no for every item.')
        frame = frame[frame['relevant'] == 'yes'].copy()
        frame['human_label'] = frame['human_label'].str.strip().str.lower()
        if len(frame) < 50 or not frame['human_label'].isin(LABELS).all():
            raise ValueError('Label at least 50 relevant items with valid labels.')
        original = dict(db.execute('SELECT id,text FROM posts'))
        if any((original.get(row.post_id) != row.text for row in frame.itertuples())):
            raise ValueError('Do not change original IDs or text.')
    finally:
        db.close()
    print(f'Testing RoBERTa on {len(frame)} items...')
    frame['transformer_label'] = [item['label'].lower() for item in predict(load_model(), frame['text'].tolist())]
    frame['baseline_label'] = frame['text'].map(baseline)
    for column in ['transformer_label', 'baseline_label']:
        frame[column + '_correct'] = frame[column] == frame['human_label']
    order = ['post_id', 'topic', 'text', 'relevant', 'human_label', 'transformer_label', 'transformer_label_correct', 'baseline_label', 'baseline_label_correct', 'explanation', 'source_url']
    output = DB.with_name('test_results.csv')
    if output.exists():
        backup = output.with_name('test_results_backup_' + now().strftime('%Y%m%d_%H%M%S_%f') + '.csv')
        output.rename(backup)
        print('Previous results preserved as ' + backup.name)
    frame[[column for column in order if column in frame]].to_csv(output, index=False, encoding='utf-8-sig')
    for name, column in [('RoBERTa', 'transformer_label'), ('Baseline', 'baseline_label')]:
        correct = frame[column + '_correct']
        print(f'\n{name}: {correct.sum()}/{len(frame)} ({correct.mean():.1%})')
    matrix = pd.crosstab(frame['human_label'], frame['transformer_label']).reindex(index=LABELS, columns=LABELS, fill_value=0)
    matrix.index.name = 'Human'
    matrix.columns.name = 'Transformer'
    print('\nHuman vs transformer: rows = human, columns = transformer')
    print(matrix.to_string())
    print('\nSaved: test_results.csv')
    print('Explain three transformer failures in your README.')
def export_csv(limit=2000):
    """Export the newest stored items, with source and collection timestamps."""
    if not DB.exists():
        raise FileNotFoundError(f'Database not found: {DB}')
    db = sqlite3.connect(f'{DB.as_uri()}?mode=ro', uri=True, timeout=30)
    try:
        frame = pd.read_sql_query(f"\n            SELECT p.id AS post_id,p.project AS topic,p.kind,\n              p.created_at AS source_time,p.collected_at,p.is_history,\n              p.text,p.source_url,s.label AS sentiment,s.score,\n              CASE WHEN p.id LIKE 'bsky:%' THEN 'Bluesky'\n                   WHEN p.id LIKE 'hn:%' THEN 'Hacker News'\n                   ELSE 'App Store' END AS source\n            FROM posts p LEFT JOIN sentiments s\n              ON p.id=s.post_id AND p.text_hash=s.text_hash AND s.model=?\n            WHERE {FILTER}\n            ORDER BY julianday(p.collected_at) DESC,p.id LIMIT ?\n        ", db, params=[MODEL, limit])
    finally:
        db.close()
    for column in ['source_time', 'collected_at']:
        frame[column + '_amsterdam'] = pd.to_datetime(frame[column], format='ISO8601', utc=True, errors='coerce').dt.tz_convert('Europe/Amsterdam').map(lambda value: value.isoformat() if pd.notna(value) else '')
    output = DB.with_name('entries_2000_' + now().strftime('%Y%m%d_%H%M%S_%f') + '.csv')
    frame.to_csv(output, index=False, encoding='utf-8-sig')
    print(f'Exported {len(frame)} entries to {output}')
    if len(frame) < limit:
        print(f'Only {len(frame)} matching entries are available; no rows were invented.')
def run():
    status = {}
    def worker(function):
        try:
            function(status)
        except Exception as error:
            status[function.__name__ + '_error'] = str(error)
            print(f'{function.__name__} stopped: {error}', flush=True)
    threads = [threading.Thread(target=worker, args=(function,), daemon=True) for function in [collect, analyse]]
    for thread in threads:
        thread.start()
    print('Collecting and analysing. Open dashboard.py with Streamlit. Ctrl+C to stop.', flush=True)
    try:
        while all((thread.is_alive() for thread in threads)):
            time.sleep(1)
        raise RuntimeError('A worker stopped. See the error above and restart after fixing it.')
    except KeyboardInterrupt:
        print('Stopped.')
if __name__ == '__main__':
    if '--export' in sys.argv:
        export_csv()
    elif '--make-test' in sys.argv or '--test' in sys.argv:
        test()
    else:
        run()
