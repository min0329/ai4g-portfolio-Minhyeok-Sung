"""From the filtered iNaturalist dump, pick photos per class and download them into class folders."""
import csv, random, sys, subprocess, collections, concurrent.futures as cf
from pathlib import Path

csv.field_size_limit(10**9)
D = Path(__file__).resolve().parent.parent / "out"
DEST = Path(sys.argv[1]); PER_CLASS = int(sys.argv[2]) if len(sys.argv) > 2 else 150
CLASSES = {
    "asian_hornet": ["Vespa velutina"],
    "european_hornet": ["Vespa crabro"],
    "wasp": ["Vespula vulgaris", "Vespula germanica"],
    "hornet_hoverfly": ["Volucella zonaria"],
    "honeybee": ["Apis mellifera"],
}
MAX_PER_OBSERVER = 5
UNSEEN_EVERY = 10
LIC = {"CC0": "CC0", "CC-BY": "CC BY 4.0", "CC-BY-NC": "CC BY-NC 4.0", "CC-BY-SA": "CC BY-SA 4.0",
       "CC-BY-ND": "CC BY-ND 4.0", "CC-BY-NC-SA": "CC BY-NC-SA 4.0", "CC-BY-NC-ND": "CC BY-NC-ND 4.0"}

def rows(name):
    with open(D / name, newline="", encoding="utf-8") as f:
        yield from csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE)

name_to_cls = {n: c for c, ns in CLASSES.items() for n in ns}
taxon_cls = {}
for t in rows("taxa.tsv"):
    if t["name"] in name_to_cls and t["rank"] == "species":
        taxon_cls[t["taxon_id"]] = name_to_cls[t["name"]]
        # include subspecies (e.g. Vespa velutina nigrithorax)
for t in rows("taxa.tsv"):
    anc = t.get("ancestry", "").split("/")
    for tid, c in list(taxon_cls.items()):
        if tid in anc and t["rank"] in ("subspecies", "variety", "form"):
            taxon_cls[t["taxon_id"]] = c
print("taxa:", taxon_cls)

obs = {o["observation_uuid"]: o for o in rows("nl_obs.tsv") if o["taxon_id"] in taxon_cls}
# the dump filter used a bounding box; keep only points whose nearest town is in the Netherlands
import reverse_geocode
keys = list(obs)
cc = reverse_geocode.search([(float(obs[k]["latitude"]), float(obs[k]["longitude"])) for k in keys])
before = len(obs)
obs = {k: obs[k] for k, r in zip(keys, cc) if r["country_code"] == "NL"}
print(f"kept {len(obs)} of {before} observations inside the Netherlands")
photos = collections.defaultdict(list)
for p in rows("nl_photos.tsv"):
    if p["observation_uuid"] in obs and p["position"] in ("0", ""):
        photos[taxon_cls[obs[p["observation_uuid"]]["taxon_id"]]].append(p)
observers = {}
want = {p["observer_id"] for ps in photos.values() for p in ps}
for o in rows("observers.tsv"):
    if o["observer_id"] in want:
        observers[o["observer_id"]] = o.get("name") or o["login"]

random.seed(15)
picked = []
for c, ps in photos.items():
    random.shuffle(ps)
    per_obs, chosen = collections.Counter(), []
    for p in ps:
        if per_obs[p["observer_id"]] < MAX_PER_OBSERVER:
            per_obs[p["observer_id"]] += 1
            chosen.append(p)
        if len(chosen) >= PER_CLASS:
            break
    print(f"{c:22s} available {len(ps):6d}  picked {len(chosen):4d}  observers {len(per_obs)}")
    for i, p in enumerate(chosen, 1):
        split = "unseen" if i % UNSEEN_EVERY == 0 else "train"
        picked.append((c, split, p))

def fetch(item):
    c, split, p = item
    ext = p["extension"] or "jpg"
    out = DEST / split / c / f"{c}_{p['photo_id']}.{ext.lower()}"
    out.parent.mkdir(parents=True, exist_ok=True)
    if not out.exists():
        url = f"https://inaturalist-open-data.s3.amazonaws.com/photos/{p['photo_id']}/medium.{ext}"
        r = subprocess.run(["curl", "-sS", "-f", "-m", "60", "-o", str(out), url])
        if r.returncode:
            return None
    return out

with cf.ThreadPoolExecutor(16) as ex:
    results = list(ex.map(fetch, picked))

with open(DEST / "attribution.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["file", "class", "split", "taxon_id", "observed_on", "latitude", "longitude",
                "license", "author", "photo_url", "observation_url"])
    for (c, split, p), out in zip(picked, results):
        if out is None:
            continue
        o = obs[p["observation_uuid"]]
        w.writerow([out.relative_to(DEST).as_posix(), c, split, o["taxon_id"], o["observed_on"],
                    round(float(o["latitude"]), 2), round(float(o["longitude"]), 2),
                    LIC.get(p["license"], p["license"]), observers.get(p["observer_id"], p["observer_id"]),
                    f"https://www.inaturalist.org/photos/{p['photo_id']}",
                    f"https://www.inaturalist.org/observations/{p['observation_uuid']}"])
print("downloaded", sum(r is not None for r in results), "of", len(picked))
