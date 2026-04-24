"""
watcher.py — automatic golf league score updater

Monitors Scores\Scores.xlsx for changes. When the file is saved, scans
every tab for Calculator-format score data and processes any tab whose
content has changed since the last run.

Tab naming (process_scores.py handles all of these):
  "R1 Scores", "R2 Scores" ... "R9 Scores"  → rounds 1-9
  "Round 3", "R3", "Week 3"                 → round 3

Tab fingerprints stored in processed_files.json ensure that unchanged
tabs are never re-processed.
"""

import os, sys, io, json, time, hashlib, subprocess, openpyxl

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE        = r"C:\Users\ehigh\OneDrive - IMI Companies\Documents\Golf League"
SCORES_FILE = os.path.join(BASE, r"Scores\Scores.xlsx")
MANIFEST    = os.path.join(BASE, "setup", "processed_files.json")
PROCESSOR   = os.path.join(BASE, "setup", "process_scores.py")
POLL_SECS   = 30

BLOCK_STARTS = [1, 14, 27]


# ── Manifest ──────────────────────────────────────────────────────────────────

def load_manifest():
    if os.path.exists(MANIFEST):
        try:
            with open(MANIFEST, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_manifest(manifest):
    with open(MANIFEST, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)


# ── Tab fingerprinting ────────────────────────────────────────────────────────

def tab_fingerprint(ws):
    """
    Hash only the 'Holes Won' summary rows (the rows that carry match results).
    Returns None if no such rows exist (empty / non-score tab).
    """
    key_rows = []
    for row in ws.iter_rows(values_only=True):
        row = list(row)
        if any(
            len(row) > bs + 1 and row[bs + 1] == 'Holes Won'
            for bs in BLOCK_STARTS
        ):
            key_rows.append(str(row))

    if not key_rows:
        return None
    return hashlib.md5('\n'.join(key_rows).encode()).hexdigest()


def scan_score_tabs(wb):
    """Return dict: tab_name → fingerprint for every tab that has score data."""
    result = {}
    for name in wb.sheetnames:
        fp = tab_fingerprint(wb[name])
        if fp is not None:
            result[name] = fp
    return result


# ── Processor runner ──────────────────────────────────────────────────────────

def run_processor(tab_name):
    """Call process_scores.py for the given tab.  Returns True on success."""
    print(f"\n[{time.strftime('%H:%M:%S')}] Score data changed in tab: {tab_name!r}")
    result = subprocess.run(
        ['py', '-3', PROCESSOR, SCORES_FILE, tab_name],
        capture_output=True, text=True, encoding='utf-8', errors='replace',
    )
    for line in result.stdout.splitlines():
        print(f"  {line}")
    if result.stderr.strip():
        print(f"  [STDERR] {result.stderr.strip()}")
    if result.returncode == 0:
        print(f"  [OK] League updated.")
        return True
    print(f"  [FAIL] Processor exited with code {result.returncode}")
    return False


# ── Main loop ─────────────────────────────────────────────────────────────────

def watch():
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║       IMI Golf League — Automatic Score Watcher             ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print(f"  Watching : {SCORES_FILE}")
    print(f"  Interval : every {POLL_SECS} seconds")
    print(f"  Started  : {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("  (Press Ctrl+C to stop)\n")

    manifest   = load_manifest()
    last_mtime = None

    while True:
        # Only open the file when it has actually changed
        try:
            mtime = os.path.getmtime(SCORES_FILE)
        except OSError:
            time.sleep(POLL_SECS)
            continue

        if mtime != last_mtime:
            last_mtime = mtime
            try:
                wb   = openpyxl.load_workbook(SCORES_FILE, data_only=True, read_only=True)
                tabs = scan_score_tabs(wb)
                wb.close()
            except Exception as e:
                print(f"[{time.strftime('%H:%M:%S')}] Could not read scores file: {e}")
                time.sleep(POLL_SECS)
                continue

            for tab_name, fp in tabs.items():
                key = f"tab::{tab_name}"
                if manifest.get(key) != fp:
                    ok = run_processor(tab_name)
                    if ok:
                        manifest[key] = fp
                        save_manifest(manifest)

        time.sleep(POLL_SECS)


if __name__ == '__main__':
    try:
        watch()
    except KeyboardInterrupt:
        print("\n[Stopped by user]")
