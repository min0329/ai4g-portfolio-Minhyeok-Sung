"""Unzip the LISS downloads and write an overview of what is in them.

Run from the repository folder:  python scripts/liss_inventory.py

Expected layout (zip files may be nested, file names do not matter):
    data/liss/background/       Background Variables (avars), one file per month
    data/liss/work_schooling/   Core Study Work and Schooling, one file per wave
    data/liss/health/           Core Study Health, one file per wave
    data/liss/economic_income/  Core Study Economic Situation: Income (optional)

Output:
    docs/liss_overview.md        variables per study, aligned across waves, plus panel totals
    docs/liss_variables_per_wave.md   every variable of every wave, as stored in the files

Both files contain only variable names, question texts, answer codes and totals
over the whole panel. They contain no rows of respondents, so they can be shared.
The data files themselves must stay local (data/liss/ is in .gitignore).
"""

import re
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
LISS = ROOT / "data" / "liss"
OUT_OVERVIEW = ROOT / "docs" / "liss_overview.md"
OUT_PER_WAVE = ROOT / "docs" / "liss_variables_per_wave.md"
STUDIES = ["background", "work_schooling", "health", "economic_income"]
MAX_CODES = 40  # answer codes shown per variable

# belbezig (primary occupation) codes used to find unemployment spells
WORK = {1, 2, 3}  # employee, family business, self-employed
UNEMPLOYED = {4, 6, 11}  # job seeker after job loss, exempted, unpaid work with WW
BACKGROUND_KEY_VARS = ["belbezig", "leeftijd", "geslacht", "oplmet", "oplcat", "sted",
                       "aantalhh", "aantalki", "partner", "burgstat", "woonvorm",
                       "nettoink", "brutoink", "herkomstgroep", "positie", "doetmee"]


def unzip_all(folder):
    """Extract every zip (also zips inside zips) next to itself, once."""
    done = set()
    while True:
        zips = [z for z in folder.rglob("*.zip") if z not in done and "__MACOSX" not in z.parts]
        if not zips:
            return
        for z in zips:
            target = z.with_suffix("")
            if not target.exists():
                print(f"  unzip {z.relative_to(ROOT)}")
                with zipfile.ZipFile(z) as zf:
                    zf.extractall(target)
            done.add(z)


def find_dta(folder):
    files = {}
    for p in sorted(folder.rglob("*.dta")):
        if p.name.startswith("._") or "__MACOSX" in p.parts:
            continue
        files.setdefault(p.name, p)  # same file unzipped twice: keep one
    return list(files.values())


def read_meta(path):
    """Variable labels and value labels, without loading the data."""
    with pd.read_stata(path, iterator=True, convert_categoricals=False) as r:
        var_labels = r.variable_labels()
        value_labels = r.value_labels()
        # pandas keeps the variable -> label set link in private attributes
        lbl_of = dict(zip(getattr(r, "_varlist", []), getattr(r, "_lbllist", [])))
    codes = {}
    for var in var_labels:
        name = lbl_of.get(var) or (var if var in value_labels else None)
        if name and name in value_labels:
            codes[var] = value_labels[name]
    return var_labels, codes


def read_columns(path, wanted):
    with pd.read_stata(path, iterator=True, convert_categoricals=False) as r:
        present = list(r.variable_labels())
    lower = {c.lower(): c for c in present}
    cols = [lower[w] for w in wanted if w in lower]
    df = pd.read_stata(path, columns=cols, convert_categoricals=False)
    df.columns = [c.lower() for c in df.columns]
    return df


def fmt_codes(codes):
    items = list(codes.items())
    text = "; ".join(f"{k:g}={v}" if isinstance(k, (int, float)) else f"{k}={v}"
                     for k, v in items[:MAX_CODES])
    if len(items) > MAX_CODES:
        text += f"; ... ({len(items) - MAX_CODES} more)"
    return text


def clean(text):
    return str(text).replace("|", "/").replace("\n", " ").strip()


def wave_prefix(var_names):
    """Core study variables look like cw08a001: prefix cw08a + question number 001."""
    found = Counter(m.group(1) for v in var_names if (m := re.match(r"^([a-z]{2}\d{2}[a-z])\d{3}", v.lower())))
    return found.most_common(1)[0][0] if found else None


def month_index(yyyymm):
    yyyymm = int(yyyymm)
    return (yyyymm // 100) * 12 + (yyyymm % 100) - 1


def month_label(t):
    return f"{t // 12}-{t % 12 + 1:02d}"


# ---------------------------------------------------------------- core studies

def describe_core_study(study, files, out, per_wave):
    out.append(f"\n## {study}\n")
    per_wave.append(f"\n## {study}\n")
    if not files:
        out.append("_No .dta files found._\n")
        return {}

    waves = []  # (prefix, file, n respondents, var_labels, codes)
    for f in files:
        var_labels, codes = read_meta(f)
        ids = read_columns(f, ["nomem_encr"])
        prefix = wave_prefix(var_labels) or f.stem
        waves.append((prefix, f, len(ids), var_labels, codes))
    waves.sort(key=lambda w: w[0][2:4] + w[0])

    out.append("| Wave prefix | File | Respondents | Variables |\n|---|---|---|---|\n")
    for prefix, f, n, var_labels, _ in waves:
        out.append(f"| {prefix} | {f.name} | {n} | {len(var_labels)} |\n")

    # align questions across waves by their number (the last three digits)
    by_number = defaultdict(dict)  # number -> prefix -> (label, codes)
    other = defaultdict(dict)
    for prefix, f, n, var_labels, codes in waves:
        per_wave.append(f"\n### {prefix} ({f.name})\n\n| Variable | Label | Codes |\n|---|---|---|\n")
        for var, label in var_labels.items():
            per_wave.append(f"| {var} | {clean(label)} | {clean(fmt_codes(codes.get(var, {})))} |\n")
            m = re.match(r"^[a-z]{2}\d{2}[a-z](\d{3})$", var.lower())
            if m:
                by_number[m.group(1)][prefix] = (clean(label), codes.get(var, {}))
            else:
                other[var.lower()][prefix] = (clean(label), codes.get(var, {}))

    all_prefixes = [w[0] for w in waves]
    out.append("\n### Questions aligned across waves\n\n"
               "Label and codes are from the most recent wave that has the question. "
               "'Label differs' lists waves where the question text is not identical.\n\n"
               "| No. | Label (latest) | In waves | Label differs | Codes (latest) |\n|---|---|---|---|---|\n")
    for number in sorted(by_number):
        seen = by_number[number]
        present = [p for p in all_prefixes if p in seen]
        latest_label, latest_codes = seen[present[-1]]
        differs = [p for p in present if seen[p][0] != latest_label]
        in_waves = "all" if len(present) == len(all_prefixes) else ", ".join(present)
        out.append(f"| {number} | {latest_label} | {in_waves} | {', '.join(differs)} | "
                   f"{clean(fmt_codes(latest_codes))} |\n")
    if other:
        out.append("\n### Other variables\n\n| Variable | Label | In waves |\n|---|---|---|\n")
        for var in sorted(other):
            present = [p for p in all_prefixes if p in other[var]]
            out.append(f"| {var} | {other[var][present[-1]][0]} | {', '.join(present)} |\n")

    # interview month per person, for the coverage check of spells
    interviews = []
    for prefix, f, *_ in waves:
        m_var = f"{prefix}_m"
        df = read_columns(f, ["nomem_encr", m_var])
        if m_var in df.columns and df[m_var].notna().any():
            t = df[m_var].dropna().astype(int).map(month_index)
            interviews.append(pd.DataFrame({"nomem_encr": df.loc[t.index, "nomem_encr"], "t": t}))
        else:  # no fieldwork month in the file: assume June of the wave year
            year = 2000 + int(prefix[2:4]) if prefix[2:4].isdigit() else None
            if year:
                interviews.append(pd.DataFrame({"nomem_encr": df["nomem_encr"], "t": year * 12 + 5}))
            out.append(f"\n_Note: no `{m_var}` (interview month) in {f.name}; June {year} assumed._\n")
    return pd.concat(interviews) if interviews else pd.DataFrame(columns=["nomem_encr", "t"])


# ------------------------------------------------------------------ background

def describe_background(files, out, per_wave):
    out.append("\n## background\n")
    if not files:
        out.append("_No .dta files found._\n")
        return None

    frames, presence, labels, codes_latest = [], defaultdict(list), {}, {}
    for f in files:
        var_labels, codes = read_meta(f)
        df = read_columns(f, ["nomem_encr", "wave", "belbezig", "leeftijd"])
        if "wave" not in df.columns or df["wave"].isna().all():
            m = re.search(r"(20\d{2})(0[1-9]|1[0-2])", f.name)
            df["wave"] = int(m.group(0)) if m else None
        month = int(df["wave"].dropna().mode().iloc[0])
        for var, label in var_labels.items():
            presence[var.lower()].append(month)
            labels[var.lower()] = clean(label)
            if var in codes:
                codes_latest[var.lower()] = codes[var]
        frames.append(df)

    panel = pd.concat(frames, ignore_index=True)
    panel = panel.dropna(subset=["nomem_encr", "wave"])
    panel["t"] = panel["wave"].astype(int).map(month_index)
    panel = panel.drop_duplicates(["nomem_encr", "t"]).sort_values(["nomem_encr", "t"])

    months = sorted(panel["t"].unique())
    missing = sorted(set(range(months[0], months[-1] + 1)) - set(months))
    out.append(f"- Files: {len(files)}\n- Months: {month_label(months[0])} to {month_label(months[-1])} "
               f"({len(months)} months)\n- Missing months: "
               f"{', '.join(month_label(t) for t in missing) or 'none'}\n"
               f"- Person-months: {len(panel):,}\n- Different persons: {panel['nomem_encr'].nunique():,}\n")

    out.append("\n### Variables\n\n| Variable | Label | Months present | Codes (latest) |\n|---|---|---|---|\n")
    for var in sorted(presence, key=lambda v: (v not in BACKGROUND_KEY_VARS, v)):
        ms = presence[var]
        span = "all" if len(ms) == len(files) else f"{len(ms)} of {len(files)} ({month_label(month_index(min(ms)))} to {month_label(month_index(max(ms)))})"
        out.append(f"| {var} | {labels[var]} | {span} | {clean(fmt_codes(codes_latest.get(var, {})))} |\n")

    if "belbezig" in panel.columns:
        names = codes_latest.get("belbezig", {})
        counts = panel["belbezig"].value_counts(dropna=False).sort_index()
        out.append("\n### belbezig over all person-months\n\n| Code | Label | Person-months |\n|---|---|---|\n")
        for code, n in counts.items():
            out.append(f"| {code} | {names.get(code, '')} | {n:,} |\n")
    per_wave.append("\n## background\n\nSee docs/liss_overview.md (same variables every month).\n")
    return panel


def find_spells(panel):
    """Spell = first month with belbezig 4 directly after a month in paid work."""
    p = panel.copy()
    p["prev_t"] = p.groupby("nomem_encr")["t"].shift()
    p["prev_bel"] = p.groupby("nomem_encr")["belbezig"].shift()
    start = (p["belbezig"] == 4) & p["prev_bel"].isin(WORK) & (p["t"] - p["prev_t"] == 1)
    spells = p.loc[start, ["nomem_encr", "t", "leeftijd"]].copy() if "leeftijd" in p else p.loc[start, ["nomem_encr", "t"]].copy()

    status = dict(zip(zip(p["nomem_encr"], p["t"]), p["belbezig"]))
    last_t = p.groupby("nomem_encr")["t"].max()
    panel_end = p["t"].max()

    outcome, status_m11, gaps = [], [], []
    for pid, t in zip(spells["nomem_encr"], spells["t"]):
        window = [status.get((pid, t + k)) for k in range(1, 12)]
        gaps.append(sum(s is None for s in window))
        if any(s in WORK for s in window if s is not None):
            outcome.append("back to work within 12 months")
            status_m11.append(None)
        elif t + 11 > panel_end:
            outcome.append("too recent (panel ends before month 12)")
            status_m11.append(None)
        elif last_t[pid] < t + 11:
            outcome.append("left the panel before month 12")
            status_m11.append(None)
        else:
            last = next((s for s in reversed(window) if s is not None), None)
            status_m11.append(last)
            outcome.append("12+ months, still unemployed" if last in UNEMPLOYED
                           else "12+ months, other status (retired, disabled, student, ...)")
    spells["outcome"] = outcome
    spells["status_m11"] = status_m11
    spells["missing_months"] = gaps
    return spells


def describe_spells(spells, panel, interviews, out):
    out.append("\n## Feasibility: unemployment spells in the panel\n\n"
               "A spell starts in the first month with belbezig = 4 (job seeker following job loss) "
               "directly after a month with belbezig 1-3 (paid work). Months 1-11 after the start "
               "decide the outcome; belbezig 4, 6 and 11 count as still unemployed.\n\n")
    out.append(f"- Spells: {len(spells):,} (persons: {spells['nomem_encr'].nunique():,})\n")
    usable = spells[spells["outcome"].str.startswith(("back", "12+"))]
    out.append(f"- Spells with a known outcome: {len(usable):,}\n")
    if "leeftijd" in spells:
        aged = usable[usable["leeftijd"].between(18, 66)]
        out.append(f"- ... of which aged 18-66 at the start: {len(aged):,}\n")

    out.append("\n| Outcome | Spells |\n|---|---|\n")
    for k, n in spells["outcome"].value_counts().items():
        out.append(f"| {k} | {n:,} |\n")

    out.append("\n**Status in the last observed month of the window, for spells that lasted 12+ months**\n\n"
               "| belbezig | Spells |\n|---|---|\n")
    for k, n in spells["status_m11"].dropna().astype(int).value_counts().sort_index().items():
        out.append(f"| {k} | {n:,} |\n")

    out.append("\n**Missing months inside the 11-month window (spells with a known outcome)**\n\n"
               "| Missing months | Spells |\n|---|---|\n")
    for k, n in usable["missing_months"].value_counts().sort_index().items():
        out.append(f"| {k} | {n:,} |\n")

    out.append("\n**Spells per start year**\n\n| Year | Spells | Known outcome | 12+ months |\n|---|---|---|---|\n")
    year = spells["t"] // 12
    for y in sorted(year.unique()):
        s = spells[year == y]
        u = s[s["outcome"].str.startswith(("back", "12+"))]
        out.append(f"| {y} | {len(s)} | {len(u)} | {u['outcome'].str.startswith('12+').sum()} |\n")

    if "leeftijd" in usable:
        out.append("\n**Known outcome by age at the start**\n\n| Age | Spells | 12+ months | Share 12+ |\n|---|---|---|---|\n")
        bands = pd.cut(usable["leeftijd"], [0, 17, 29, 49, 66, 200],
                       labels=["<18", "18-29", "30-49", "50-66", "67+"])
        for band, g in usable.groupby(bands, observed=True):
            long = g["outcome"].str.startswith("12+").sum()
            out.append(f"| {band} | {len(g)} | {long} | {long / len(g):.0%} |\n")

    # do we have a core study interview before the job loss?
    out.append("\n**Spells with a core study interview before the start (known outcome)**\n\n"
               "| Study | Within 12 months before | Within 24 months before | Any time before |\n|---|---|---|---|\n")
    for study, iv in interviews.items():
        if iv is None or len(iv) == 0:
            continue
        m = usable[["nomem_encr", "t"]].reset_index().merge(iv, on="nomem_encr", suffixes=("", "_iv"))
        m = m[m["t_iv"] < m["t"]]
        lag = (m["t"] - m["t_iv"]).groupby(m["index"]).min()
        out.append(f"| {study} | {(lag <= 12).sum():,} | {(lag <= 24).sum():,} | {len(lag):,} |\n")


def main():
    if not LISS.exists():
        raise SystemExit(f"Folder not found: {LISS}")
    print("Unzipping ...")
    unzip_all(LISS)

    out = ["# LISS data overview\n\n"
           "Generated by `scripts/liss_inventory.py`. Contains only variable names, question texts, "
           "answer codes and totals over the whole panel; no rows of respondents.\n"]
    per_wave = ["# LISS variables per wave\n\nGenerated by `scripts/liss_inventory.py`.\n"]

    files = {s: find_dta(LISS / s) if (LISS / s).exists() else [] for s in STUDIES}
    for s in STUDIES:
        print(f"{s}: {len(files[s])} .dta files")

    print("Reading background variables (this can take a few minutes) ...")
    panel = describe_background(files["background"], out, per_wave)
    interviews = {}
    for s in STUDIES[1:]:
        print(f"Reading {s} ...")
        interviews[s] = describe_core_study(s, files[s], out, per_wave)

    if panel is not None and "belbezig" in panel.columns:
        print("Counting unemployment spells ...")
        describe_spells(find_spells(panel), panel, interviews, out)

    OUT_OVERVIEW.parent.mkdir(exist_ok=True)
    OUT_OVERVIEW.write_text("".join(out), encoding="utf-8")
    OUT_PER_WAVE.write_text("".join(per_wave), encoding="utf-8")
    print(f"Done: {OUT_OVERVIEW.relative_to(ROOT)} and {OUT_PER_WAVE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
