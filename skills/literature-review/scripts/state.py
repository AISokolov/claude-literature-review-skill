#!/usr/bin/env python3
"""Local state for the literature-review skill. Standard library only.

All user data lives OUTSIDE the skill/plugin folder, so updates never touch it:
  default  ~/.claude/literature-review-data/
  override with the environment variable LITERATURE_REVIEW_DATA
Contents:
  research-profile.json  the user's research profile (topic, streams, terms, optional sheet)
  library.json      every paper ever surfaced: review status + sheet sync status
  sheet_index.json  DOIs / normalized titles already present in the Google Sheet
  search_log.json   queries run, per source, with result counts (search coverage)
  pdfs/, reports/   cached open-access PDFs and versioned reports

Usage (run with: python state.py <command> ...):
  data-dir                              print the absolute data directory (creates it)
  profile-check                         report a missing profile or missing required fields
  key <doi-or-title>                    print the normalized key
  filter <candidates.json>              print candidates not already known (library or sheet)
  add <paper.json>                      add a paper as pending (refuses duplicates)
  decide <key> accept|reject|skip|reconsider [--note TEXT]
  sync-ok <key> [--row N]               mark an accepted paper as synced to the sheet
  sync-fail <key> --error TEXT          record a failed sync attempt (stays sync_pending)
  list [--status S] [--sync S]          list keys + titles
  show <key>                            print the full record
  stats                                 counts: pending / accepted / rejected / synced / sync_pending
  sheet-index <index.json>              replace sheet_index.json with {"dois": [...], "titles": [...]}
  log-search --source S --query Q --count N [--stream N]
  next-report <name>                    print the next free versioned path in <data>/reports/
"""
import json, os, re, sys, tempfile, unicodedata
from datetime import datetime, timezone

DATA = os.path.abspath(os.path.expanduser(
    os.environ.get("LITERATURE_REVIEW_DATA") or os.path.join("~", ".claude", "literature-review-data")))
PROFILE = os.path.join(DATA, "research-profile.json")
LIB = os.path.join(DATA, "library.json")
SHEET = os.path.join(DATA, "sheet_index.json")
LOG = os.path.join(DATA, "search_log.json")
REPORTS = os.path.join(DATA, "reports")


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load(path, default):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)  # atomic: a crash never leaves a half-written file


def norm_doi(s):
    s = (s or "").strip().lower()
    s = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:\s*)", "", s)
    return s if s.startswith("10.") else ""


def norm_title(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9]+", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def key_of(doi="", title=""):
    d = norm_doi(doi)
    return ("doi:" + d) if d else ("title:" + norm_title(title))


def resolve(lib, k):
    """Accept a raw DOI, a raw title, or an existing key."""
    if k in lib["papers"]:
        return k
    for cand in (key_of(doi=k), key_of(title=k)):
        if cand in lib["papers"]:
            return cand
    sys.exit(f"unknown paper: {k}")


def known(lib, sheet, doi, title):
    """Return why a paper is already known, or None."""
    d, t = norm_doi(doi), norm_title(title)
    for k, p in lib["papers"].items():
        if (d and norm_doi(p.get("doi")) == d) or (t and norm_title(p.get("title")) == t):
            return f"library:{p['status']}"
    if d and d in sheet.get("dois", []):
        return "sheet"
    if t and t in sheet.get("titles", []):
        return "sheet"
    return None


def main(argv):
    if not argv:
        print(__doc__); return
    cmd, args = argv[0], argv[1:]
    lib = load(LIB, {"papers": {}})
    opt = lambda name, default=None: args[args.index(name) + 1] if name in args else default

    if cmd == "data-dir":
        os.makedirs(os.path.join(DATA, "pdfs"), exist_ok=True)
        print(DATA)

    elif cmd == "profile-check":
        if not os.path.exists(PROFILE):
            print("missing profile: run setup"); sys.exit(2)
        try:
            prof = load(PROFILE, {})
        except json.JSONDecodeError as e:
            print(f"invalid profile JSON: {e}"); sys.exit(2)
        missing = []
        if not (prof.get("topic") or {}).get("title"):
            missing.append("topic.title")
        if not [s for s in prof.get("streams", []) if (s.get("name") if isinstance(s, dict) else s)]:
            missing.append("streams")
        if not prof.get("terms"):
            missing.append("terms")
        if missing:
            print("incomplete profile, missing: " + ", ".join(missing)); sys.exit(3)
        sh = prof.get("sheet") or {}
        sheet = ("none" if not sh.get("spreadsheet_id") else
                 "configured" if sh.get("mapping_confirmed") else "mapping not confirmed")
        print(f"profile OK | topic ({(prof['topic'].get('status') or 'unspecified')}): {prof['topic']['title']} | "
              f"{len(prof['streams'])} streams, {len(prof['terms'])} terms | sheet: {sheet}")

    elif cmd == "key":
        print(key_of(doi=args[0], title=args[0]))

    elif cmd == "filter":
        sheet = load(SHEET, {})
        cands = load(args[0], [])
        fresh, skipped = [], []
        for c in cands:
            why = known(lib, sheet, c.get("doi"), c.get("title"))
            (skipped if why else fresh).append({**c, "_known": why} if why else c)
        print(json.dumps({"new": fresh, "skipped": [{"title": s.get("title"), "why": s["_known"]} for s in skipped]},
                         ensure_ascii=False, indent=2))

    elif cmd == "add":
        p = load(args[0], None)
        if not p or not p.get("title"):
            sys.exit("paper.json needs at least a title")
        why = known(lib, load(SHEET, {}), p.get("doi"), p.get("title"))
        if why:
            sys.exit(f"duplicate ({why}): {p['title']}")
        k = key_of(p.get("doi"), p.get("title"))
        p.update(status="pending", sync="n/a", added=now(), history=[])
        lib["papers"][k] = p
        save(LIB, lib); print(k)

    elif cmd == "decide":
        k = resolve(lib, args[0]); action = args[1]; p = lib["papers"][k]
        note = opt("--note", "")
        if action == "accept":
            p["status"] = "accepted"
            if p.get("sync") != "synced":
                p["sync"] = "sync_pending"
        elif action == "reject":
            if p.get("sync") == "synced":
                sys.exit("already in the sheet; rejecting locally would not remove the row")
            p["status"], p["sync"] = "rejected", "n/a"
        elif action == "reconsider":
            if p["status"] != "rejected":
                sys.exit("only rejected papers can be reconsidered")
            p["status"] = "pending"
        elif action == "skip":
            pass  # stays pending, just logged
        else:
            sys.exit("action must be accept|reject|skip|reconsider")
        p["history"].append({"at": now(), "action": action, "note": note})
        save(LIB, lib); print(f"{k}: status={p['status']} sync={p['sync']}")

    elif cmd == "sync-ok":
        k = resolve(lib, args[0]); p = lib["papers"][k]
        if p["status"] != "accepted":
            sys.exit("only accepted papers can be synced")
        p["sync"], p["sheet_row"], p["synced_at"] = "synced", opt("--row"), now()
        save(LIB, lib); print(f"{k}: synced")

    elif cmd == "sync-fail":
        k = resolve(lib, args[0]); p = lib["papers"][k]
        p.setdefault("sync_errors", []).append({"at": now(), "error": opt("--error", "")})
        p["sync"] = "sync_pending"
        save(LIB, lib); print(f"{k}: still sync_pending ({len(p['sync_errors'])} failed attempts)")

    elif cmd == "list":
        st, sy = opt("--status"), opt("--sync")
        for k, p in lib["papers"].items():
            if (not st or p["status"] == st) and (not sy or p.get("sync") == sy):
                print(f"{p['status']:9} {p.get('sync',''):12} {p.get('relevance_score','-'):>3}  {k}  |  {p['title']}")

    elif cmd == "show":
        print(json.dumps(lib["papers"][resolve(lib, args[0])], ensure_ascii=False, indent=2))

    elif cmd == "stats":
        ps = list(lib["papers"].values())
        c = lambda f: sum(1 for p in ps if f(p))
        print(json.dumps({
            "pending": c(lambda p: p["status"] == "pending"),
            "accepted": c(lambda p: p["status"] == "accepted"),
            "rejected": c(lambda p: p["status"] == "rejected"),
            "synced": c(lambda p: p.get("sync") == "synced"),
            "sync_pending": c(lambda p: p.get("sync") == "sync_pending"),
            "sheet_rows_indexed": len(load(SHEET, {}).get("titles", [])),
            "searches_logged": len(load(LOG, [])),
        }, indent=2))

    elif cmd == "sheet-index":
        raw = load(args[0], {})
        idx = {"dois": sorted({norm_doi(d) for d in raw.get("dois", []) if norm_doi(d)}),
               "titles": sorted({norm_title(t) for t in raw.get("titles", []) if norm_title(t)}),
               "updated": now()}
        save(SHEET, idx); print(f"sheet index: {len(idx['titles'])} titles, {len(idx['dois'])} DOIs")

    elif cmd == "log-search":
        log = load(LOG, [])
        log.append({"at": now(), "source": opt("--source"), "query": opt("--query"),
                    "count": int(opt("--count", 0)), "stream": opt("--stream")})
        save(LOG, log); print(f"logged ({len(log)} searches total)")

    elif cmd == "next-report":
        os.makedirs(REPORTS, exist_ok=True)
        n = 1
        while os.path.exists(os.path.join(REPORTS, f"{args[0]}-v{n:03d}.md")):
            n += 1
        print(os.path.normpath(os.path.join(REPORTS, f"{args[0]}-v{n:03d}.md")))

    else:
        print(__doc__); sys.exit(1)


if __name__ == "__main__":
    # Windows consoles default to cp1251/cp1252; titles contain ü, é, etc.
    sys.stdout.reconfigure(encoding="utf-8")
    main(sys.argv[1:])
