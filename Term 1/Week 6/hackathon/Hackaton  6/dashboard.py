import html
import json
from datetime import timedelta
import pandas as pd
from hackaton6 import DB, MODEL, PRODUCTS, LABELS, SOURCES, FILTER, database, now, IG_METHOD, contributing_word_counts, sentiment_word_counts, load_sentiment_lexicon
def dashboard():
    import altair as alt
    import streamlit as st
    st.set_page_config(page_title='AI Reception Pulse', layout='wide')
    st.title('AI Reception Pulse')
    st.caption('ChatGPT · Claude · Gemini | Bluesky + Hacker News + US App Store')
    status = {'model': 'Analysis runs in hackaton6.py.', 'collector': 'Run hackaton6.py in a separate terminal to collect items.'}
    st.sidebar.header('Display settings')
    window = st.sidebar.selectbox('Time range', ['Last 24 hours', 'Last 7 days', 'All collected', 'Custom dates'], index=1)
    period = st.sidebar.radio('Group reactions by', ['Hourly', 'Daily'], index=1)
    display = st.sidebar.radio('Show', ['Percentages', 'Counts'])
    history = st.sidebar.checkbox('Include historical items', value=True)
    dates = None
    if window == 'Custom dates':
        today = pd.Timestamp.now(tz='Europe/Amsterdam').date()
        dates = st.sidebar.date_input('Start and end date', value=(today - timedelta(days=6), today))
        if not isinstance(dates, (tuple, list)) or len(dates) != 2:
            st.info('Select both a start and an end date.')
            return
    st.sidebar.caption('All dates and times use Europe/Amsterdam.')
    @st.fragment(run_every='15s')
    def refresh():
        db = database()
        try:
            data = pd.read_sql_query(f"\n                SELECT p.id AS post_id,p.project AS product,p.kind,p.created_at AS source_time,\n                  p.collected_at,p.is_history,p.text,p.source_url,\n                  s.label AS sentiment,s.score,\n                  CASE WHEN p.id LIKE 'bsky:%' THEN 'Bluesky'\n                       WHEN p.id LIKE 'hn:%' THEN 'Hacker News'\n                       ELSE 'App Store' END AS source\n                FROM posts p LEFT JOIN sentiments s\n                  ON p.id=s.post_id AND p.text_hash=s.text_hash AND s.model=?\n                WHERE {FILTER} ORDER BY p.created_at DESC\n            ", db, params=[MODEL])
            checks = pd.read_sql_query('SELECT source,timestamp,success,new_posts,message\n                   FROM source_polls WHERE source IN (?,?,?) ORDER BY id', db, params=SOURCES)
        finally:
            db.close()
        for key in ['collect_error', 'analyse_error']:
            if key in status:
                st.error(status[key] + ' — restart after fixing this.')
        if not checks.empty:
            for row in checks.groupby('source').tail(1).itertuples():
                if not row.success:
                    st.error(row.source + ': ' + row.message)
        if data.empty:
            st.info(status['model'] + ' Waiting for collected items.')
            return
        for field in ['source_time', 'collected_at']:
            data[field] = pd.to_datetime(data[field], format='ISO8601', utc=True).dt.tz_convert('Europe/Amsterdam')
        current_utc = now()
        current = pd.Timestamp(current_utc).tz_convert('Europe/Amsterdam')
        view = data.copy() if history else data[data['is_history'] == 0].copy()
        if window in ['Last 24 hours', 'Last 7 days']:
            hours = 24 if window == 'Last 24 hours' else 168
            cutoff = pd.Timestamp(current_utc - timedelta(hours=hours)).tz_convert('Europe/Amsterdam')
            view = view[(view['source_time'] >= cutoff) & (view['source_time'] <= current)].copy()
        elif dates:
            first = pd.Timestamp(dates[0]).tz_localize('Europe/Amsterdam')
            end = pd.Timestamp(dates[1] + timedelta(days=1)).tz_localize('Europe/Amsterdam')
            view = view[(view['source_time'] >= first) & (view['source_time'] < end)].copy()
        selected = view[view['sentiment'].notna() & view['product'].isin(PRODUCTS)].copy()
        metrics = [('All collected', len(data)), ('Items in selected period', len(view)), ('Analysed in selected period', view['sentiment'].notna().sum())]
        for column, (label, value) in zip(st.columns(3), metrics):
            column.metric(label, int(value))
        st.divider()
        st.subheader('All assistants together')
        st.caption('ChatGPT + Claude + Gemini, including comparison messages once each. Uses the selected time range and history setting.')
        combined = view[view['sentiment'].isin(LABELS)].copy()
        combined_counts = combined['sentiment'].value_counts().reindex(LABELS, fill_value=0)
        for column, label in zip(st.columns(3), LABELS):
            count = int(combined_counts[label])
            column.metric(label.title(), count, help=f'{100 * count / len(combined):.1f}% of analysed messages' if len(combined) else 'No analysed messages')
        if not combined.empty:
            combined['bucket'] = combined['source_time'].dt.tz_convert('UTC').dt.floor('h').dt.tz_convert('Europe/Amsterdam') if period == 'Hourly' else combined['source_time'].dt.normalize()
            buckets_all = pd.date_range(combined['bucket'].min(), combined['bucket'].max(), freq='h' if period == 'Hourly' else 'D')
            total_trend = combined.groupby(['bucket', 'sentiment']).size().unstack(fill_value=0).reindex(index=buckets_all, columns=LABELS, fill_value=0)
            total_trend.index.name = 'bucket'
            total_trend = total_trend.reset_index().melt(id_vars='bucket', var_name='sentiment', value_name='count')
            per_bucket = total_trend.groupby('bucket')['count'].transform('sum')
            total_trend['percentage'] = (100 * total_trend['count'] / per_bucket.where(per_bucket != 0)).fillna(0)
            fmt_all = '%d %b %Y %H:%M %Z' if period == 'Hourly' else '%d %b %Y'
            total_trend['period'] = total_trend['bucket'].dt.strftime(fmt_all)
            chart_all = alt.Chart(total_trend).mark_bar().encode(x=alt.X('period:O', sort=[b.strftime(fmt_all) for b in buckets_all], title=None, axis=alt.Axis(labelAngle=-45, labelOverlap=True)), y=alt.Y('percentage:Q' if display == 'Percentages' else 'count:Q', stack='zero', title='Percentage (%)' if display == 'Percentages' else 'Items'), color=alt.Color('sentiment:N', scale=alt.Scale(domain=LABELS, range=['#dc2626', '#9ca3af', '#16a34a'])), tooltip=['period:N', 'sentiment:N', 'count:Q', alt.Tooltip('percentage:Q', format='.1f')]).properties(height=320)
            st.altair_chart(chart_all, width='stretch')
            st.caption('Counts are messages, not people. Blank periods contain no analysed messages. The current period may be incomplete.')
        else:
            st.info('No analysed messages in this period.')
        st.divider()
        st.subheader('Compare the assistants')
        st.caption(f'{period} · {window} · Amsterdam time | Green: positive · Grey: neutral · Red: negative')
        if not selected.empty:
            selected['bucket'] = selected['source_time'].dt.tz_convert('UTC').dt.floor('h').dt.tz_convert('Europe/Amsterdam') if period == 'Hourly' else selected['source_time'].dt.normalize()
            buckets = pd.date_range(selected['bucket'].min(), selected['bucket'].max(), freq='h' if period == 'Hourly' else 'D')
            grid = pd.MultiIndex.from_product([PRODUCTS, buckets], names=['product', 'bucket'])
            counts = selected.groupby(['product', 'bucket', 'sentiment']).size().unstack(fill_value=0).reindex(index=grid, columns=LABELS, fill_value=0)
            trend = counts.reset_index().melt(id_vars=['product', 'bucket'], var_name='sentiment', value_name='count')
            totals = trend.groupby(['product', 'bucket'])['count'].transform('sum')
            trend['percentage'] = (100 * trend['count'] / totals.where(totals != 0)).fillna(0)
            fmt = '%d %b %Y %H:%M %Z' if period == 'Hourly' else '%d %b %Y'
            trend['period'] = trend['bucket'].dt.strftime(fmt)
            order = [bucket.strftime(fmt) for bucket in buckets]
            maximum = 100 if display == 'Percentages' else max(1, int(totals.max()))
            if period == 'Hourly' and len(buckets) > 48:
                st.info('Choose Last 24 hours or a shorter custom range for clearer hourly charts.')
            for name, column in zip(PRODUCTS, st.columns(3, gap='large')):
                with column:
                    with st.container(border=True):
                        st.subheader(name)
                        st.caption(f"{int((selected['product'] == name).sum())} analysed items")
                        chart = alt.Chart(trend[trend['product'] == name]).mark_bar().encode(x=alt.X('period:O', sort=order, title=None, axis=alt.Axis(labelAngle=-45, labelOverlap=True, labelLimit=140)), y=alt.Y('percentage:Q' if display == 'Percentages' else 'count:Q', title='Percentage (%)' if display == 'Percentages' else 'Items', stack='zero', scale=alt.Scale(domain=[0, maximum])), color=alt.Color('sentiment:N', legend=None, scale=alt.Scale(domain=LABELS, range=['#dc2626', '#9ca3af', '#16a34a'])), tooltip=[alt.Tooltip('period:N', title='Period'), 'sentiment', alt.Tooltip('count:Q', title='Items'), alt.Tooltip('percentage:Q', title='Percentage (%)', format='.1f')]).properties(height=300)
                        st.altair_chart(chart, width='stretch')
            st.caption("All charts use the same scale. Percentages use each assistant's item count per period. Blank periods have no analysed items. The current period may be incomplete.")
        else:
            st.info('No analysed items in this period. Try a wider range or wait for the model.')
        st.divider()
        st.subheader(f'Most common contributing words · {window}')
        st.caption("Words that Integrated Gradients estimates supported RoBERTa's predicted positive or negative sentiment. Per message, we select the five words with the largest positive contributions to that predicted label, then count their supporting occurrences across messages. Common English/Dutch words are hidden; contributions come from RoBERTa.")
        scope = st.selectbox('Words for', ['All assistants'] + PRODUCTS + ['Comparisons'], key='ig_scope')
        word_view = combined if scope == 'All assistants' else combined[combined['product'] == scope]
        word_view = word_view.drop_duplicates('post_id')
        db = database()
        try:
            stored = pd.read_sql_query("SELECT q.post_id,q.payload FROM ig_explanations q\n                JOIN posts p ON p.id=q.post_id AND p.text_hash=q.text_hash\n                JOIN sentiments s ON s.post_id=p.id AND s.text_hash=p.text_hash\n                  AND s.model=q.model\n                WHERE q.model=? AND q.method=? AND q.status='done'", db, params=[MODEL, IG_METHOD])
        finally:
            db.close()
        explained = word_view.merge(stored, on='post_id', how='inner')
        for sentiment, column in zip(['negative', 'positive'], st.columns(2, gap='large')):
            with column:
                st.markdown('**' + sentiment.title() + ' messages**')
                eligible = word_view[word_view['sentiment'] == sentiment]
                group = explained[explained['sentiment'] == sentiment]
                payloads = [payload for payload in group['payload'] if json.loads(payload)['label'] == sentiment]
                st.caption(f'Explanation available for {len(payloads)} of {len(eligible)} messages.')
                frequencies = contributing_word_counts(payloads) if payloads else pd.DataFrame(columns=['Word', 'Occurrences'])
                if frequencies.empty:
                    st.info('No contributing words available yet. Keep hackaton6.py running.')
                else:
                    st.dataframe(frequencies.head(20), hide_index=True, width='stretch')
        st.caption('Each word appears once per table. Counts include only occurrences selected by the contribution analysis, not every occurrence in the database. Existing and new positive/negative messages are processed automatically. Results can change while processing continues. Contributions depend on context and the padding reference; this is an approximate explanation. Stopwords are filtered only for display, after contributions have been calculated.')
        st.divider()
        st.subheader(f"Sentiment words from the contribution overview · {window}")
        st.caption(
            "Filters the Integrated Gradients overview above using VADER's English "
            "sentiment lexicon. Keeps negative words from the negative-message list "
            "and positive words from the positive-message list. Counts stay unchanged; "
            "uses the same period, assistant selection and explained messages."
        )
        @st.cache_data(show_spinner=False)
        def sentiment_lexicon():
            return load_sentiment_lexicon()
        try:
            lexicon = sentiment_lexicon()
        except Exception as error:
            st.warning("Sentiment word list unavailable: " + str(error))
        else:
            for sentiment, column in zip(["negative", "positive"], st.columns(2, gap="large")):
                with column:
                    st.markdown("**" + sentiment.title() + " sentiment words**")
                    payloads = explained.loc[explained["sentiment"] == sentiment, "payload"].tolist()
                    table = sentiment_word_counts(payloads, sentiment, lexicon)
                    if table.empty:
                        st.info("No matching sentiment words in this selection.")
                    else:
                        st.dataframe(table, hide_index=True, width="stretch")
            st.caption(
                "VADER is an existing English lexicon, not RoBERTa's own vocabulary. "
                "This filters word types, not sentence meaning; negation can change their meaning. "
                "Original contribution lists and full-message explanations remain above/below."
            )

        st.divider()
        st.subheader(f"Words behind RoBERTa's prediction · {window}")
        st.caption('Integrated Gradients estimates contributions to the predicted class. Blue supports that prediction; orange opposes it. Stronger colour means a larger contribution within this message. No words are manually filtered. This is an approximation relative to a padding reference, not an exact reason.')
        scope = st.selectbox('Assistant', ['All assistants'] + PRODUCTS + ['Comparisons'], key='detail_ig_scope')
        candidates = combined if scope == 'All assistants' else combined[combined['product'] == scope]
        sentiment = st.selectbox('Message sentiment', ['All sentiments'] + LABELS, key='detail_ig_sentiment')
        if sentiment != 'All sentiments':
            candidates = candidates[candidates['sentiment'] == sentiment]
        candidates = candidates.drop_duplicates('post_id')
        if candidates.empty:
            st.info('No analysed messages in this selection.')
        else:
            indexed = candidates.set_index('post_id')
            chosen = st.selectbox('Message to explain', indexed.index.tolist(), key='detail_ig_message', format_func=lambda key: str(indexed.loc[key, 'sentiment']).title() + ' · ' + str(indexed.loc[key, 'text'])[:110])
            row = indexed.loc[chosen]
            st.write(str(row['text']))
            db = database()
            try:
                post = db.execute('SELECT text_hash FROM posts WHERE id=?', (chosen,)).fetchone()
                explanation = db.execute('SELECT status,payload,error FROM ig_explanations WHERE post_id=? AND model=? AND text_hash=? AND method=?', (chosen, MODEL, post[0], IG_METHOD)).fetchone()
                if st.button('Explain with RoBERTa', key='detail_ig_request'):
                    db.execute('INSERT OR REPLACE INTO ig_explanations (post_id,model,text_hash,method,status,requested_at,priority) VALUES(?,?,?,?,?,?,1)', (chosen, MODEL, post[0], IG_METHOD, 'pending', now().isoformat()))
                    db.commit()
                    explanation = ('pending', None, None)
            finally:
                db.close()
            if explanation and explanation[0] == 'pending':
                st.info('Priority request queued. Keep hackaton6.py running. The current calculation finishes first.')
            elif explanation and explanation[0] == 'error':
                st.error('Explanation failed: ' + str(explanation[2]))
            elif explanation and explanation[0] == 'done':
                result = json.loads(explanation[1])
                st.markdown(f"**Predicted sentiment: {result['label'].title()}** · Confidence: {result['confidence']:.1%}")
                maximum = max((abs(span['value']) for span in result['spans']), default=0)
                pieces, cursor = ([], 0)
                text = str(row['text'])
                for span in result['spans']:
                    pieces.append(html.escape(text[cursor:span['start']]))
                    strength = abs(span['value']) / maximum if maximum else 0
                    colour = '37, 99, 235' if span['value'] >= 0 else '234, 88, 12'
                    pieces.append(f"""<span style="background:rgba({colour},{0.65 * strength:.3f});border-radius:3px" title="Contribution: {span['value']:+.5f}">""" + html.escape(text[span['start']:span['end']]) + '</span>')
                    cursor = span['end']
                pieces.append(html.escape(text[cursor:]))
                st.markdown('<div style="white-space:pre-wrap;line-height:2">' + ''.join(pieces) + '</div>', unsafe_allow_html=True)
                if result['covered_end'] < len(text.rstrip()):
                    st.caption('Only the first 512 model tokens were analysed. The remaining text is uncoloured.')
                with st.expander('Contributions and method'):
                    st.dataframe(pd.DataFrame(result['spans'])[['word', 'value']].rename(columns={'word': 'Word', 'value': 'Contribution'}), hide_index=True, width='stretch')
                    st.caption(f"32 integration steps; predicted-class logit; padding reference; fixed attention and positions. Numerical convergence delta: {result['delta']:.4g}. Values are not percentages. Contributions depend on context and the reference.")
        st.divider()
        st.subheader('Explore the underlying items')
        names = PRODUCTS + ['Comparisons']
        for name, tab in zip(names, st.tabs(names)):
            with tab:
                group = view[view['product'] == name].copy()
                label = st.selectbox('Sentiment', ['All'] + LABELS, key='label_' + name)
                day = st.date_input('Focus on one day (optional)', value=None, key='day_' + name)
                if label != 'All':
                    group = group[group['sentiment'] == label].copy()
                if day:
                    group = group[group['source_time'].dt.date == day].copy()
                st.caption(f'{len(group)} items; showing up to 200.')
                if name == 'Comparisons':
                    st.caption('Mixed-product items are excluded from the three charts.')
                group['source_time'] = group['source_time'].dt.strftime('%d %b %Y, %H:%M %Z')
                st.dataframe(group[['source_time', 'sentiment', 'score', 'text', 'source', 'source_url']].head(200), hide_index=True, width='stretch', column_config={'source_url': st.column_config.LinkColumn('Open source'), 'score': st.column_config.NumberColumn('Score', format='%.2f')})
        with st.expander('Collection status and limitations'):
            st.caption(status['model'] + ' ' + status['collector'])
            st.write(f"New since source started: {int((data['is_history'] == 0).sum())}")
            if not checks.empty:
                checks['timestamp'] = pd.to_datetime(checks['timestamp'], format='ISO8601', utc=True).dt.tz_convert('Europe/Amsterdam').dt.strftime('%d %b %Y, %H:%M %Z')
                st.dataframe(checks.tail(15), hide_index=True)
            st.caption('Required: 48 hours and 300 items. Check source failures and interruptions.')
            st.caption('Score is model confidence, not verified accuracy or sentiment intensity. Counts are items, not people. Changes do not prove causation. App Store feeds are limited and cached; timestamps are review update times.')
    refresh()
if __name__ == '__main__':
    dashboard()
