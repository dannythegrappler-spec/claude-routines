#!/usr/bin/env python3
"""
Reads checklist-history.json and writes a full, self-contained, light-mode
HTML document (with the cowork-artifact-meta tag) rendering the 30-day
item x day grid (latest day first). This file is meant to be passed as
html_path to mcp__cowork__update_artifact so the persisted "Checklist 30
Day Trends" artifact in the Artifacts tab stays current.

Usage: python3 generate_artifact_html.py <folder>   (folder defaults to ".")
Writes <folder>/artifact_grid.html and also prints its path to stdout.
"""
import sys, os, json
from datetime import date, timedelta

FOLDER = sys.argv[1] if len(sys.argv) > 1 else "."
HISTORY_PATH = os.path.join(FOLDER, "checklist-history.json")
OUT_PATH = os.path.join(FOLDER, "artifact_grid.html")


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main():
    if not os.path.exists(HISTORY_PATH):
        print(f"ERROR: {HISTORY_PATH} not found", file=sys.stderr)
        sys.exit(1)

    with open(HISTORY_PATH, "r", encoding="utf-8") as f:
        hist = json.load(f)

    keys = sorted(hist.keys())
    if not keys:
        print("ERROR: history is empty", file=sys.stderr)
        sys.exit(1)

    latest_key = keys[-1]
    items = []
    seen = set()
    for rec in hist[latest_key]["items"]:
        if rec["name"] not in seen:
            items.append(rec["name"]); seen.add(rec["name"])
    for k in keys:
        for rec in hist[k]["items"]:
            if rec["name"] not in seen:
                items.append(rec["name"]); seen.add(rec["name"])

    today = date.today()
    days = []
    for i in range(0, 30):
        d = today - timedelta(days=i)
        key = d.isoformat()
        label = d.strftime("%b %d").replace(" 0", " ")
        day_log = hist.get(key)
        records = {}
        if day_log:
            for rec in day_log["items"]:
                records[rec["name"]] = rec
        days.append({"label": label, "records": records})

    rows_html = []
    for item in items:
        cells = [f'<td class="ic">{esc(item)}</td>']
        for d in days:
            rec = d["records"].get(item)
            if rec is None:
                cells.append('<td><span class="nu">null</span></td>')
            elif rec["completed"]:
                val = rec["value"] or "check"
                cells.append(f'<td><span class="dn">{esc(val)}</span></td>')
            else:
                cells.append('<td><span class="no">None</span></td>')
        rows_html.append("<tr>" + "".join(cells) + "</tr>")

    header_cells = "".join(f'<th>{esc(d["label"])}</th>' for d in days)
    cols = "".join('<col style="width:74px;">' for _ in days)
    today_str = today.strftime("%B %d, %Y")

    html = f'''<!DOCTYPE html>
<script type="application/json" id="cowork-artifact-meta">
{{
  "name": "Checklist 30 Day Grid",
  "schemaVersion": 1,
  "description": "30-day checklist grid: items down the left, last 30 days across the top (latest first), showing elapsed time for completed tasks, None in red for incomplete, null in grey for unlogged days. Data comes from Checklist.ods via the daily 6am/11pm log jobs."
}}
</script>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Checklist 30-day grid</title>
<style>
  :root {{ color-scheme: light; }}
  * {{ box-sizing: border-box; }}
  html, body {{ margin: 0; padding: 0; background: #f7f6f2; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; padding: 32px 20px; color: #1f1e1b; }}
  .wrap {{ max-width: 1100px; margin: 0 auto; }}
  h1 {{ font-size: 20px; font-weight: 500; margin: 0 0 4px; }}
  .subtitle {{ font-size: 13px; color: #6b6a63; margin: 0 0 20px; }}
  .card {{ background: #ffffff; border: 1px solid #e4e2da; border-radius: 12px; padding: 8px; overflow-x: auto; }}
  table {{ border-collapse: collapse; font-size: 12px; table-layout: fixed; }}
  th, td {{ padding: 7px 6px; text-align: center; border-bottom: 1px solid #eeece5; white-space: nowrap; }}
  thead th {{ font-weight: 500; color: #6b6a63; border-bottom: 1px solid #e4e2da; }}
  tbody tr:last-child td {{ border-bottom: none; }}
  .ic {{ position: sticky; left: 0; background: #ffffff; text-align: left !important; padding-left: 12px !important; font-weight: 500; color: #1f1e1b; overflow: hidden; text-overflow: ellipsis; z-index: 1; box-shadow: 1px 0 0 #e4e2da; }}
  thead th.ic {{ z-index: 2; }}
  .nu {{ color: #b3b1a8; font-size: 11px; font-style: italic; }}
  .no {{ background: #fbe9e7; color: #b3261e; font-size: 11px; padding: 2px 7px; border-radius: 6px; }}
  .dn {{ color: #1f1e1b; }}
  .updated {{ font-size: 12px; color: #9c9a92; margin-top: 14px; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>Checklist 30-day grid</h1>
  <p class="subtitle">Items down the left, last 30 days across the top (latest first). Elapsed time for completed tasks, <span style="color:#b3261e;">None</span> for incomplete, <span style="color:#b3b1a8;">null</span> for unlogged days.</p>
  <div class="card">
    <table>
      <colgroup><col style="width:200px;">{cols}</colgroup>
      <thead><tr><th class="ic">Item</th>{header_cells}</tr></thead>
      <tbody>{"".join(rows_html)}</tbody>
    </table>
  </div>
  <p class="updated">Last regenerated {today_str}. Refreshed automatically at 6am and 11pm daily by the checklist report task.</p>
</div>
</body>
</html>
'''

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print(OUT_PATH)


if __name__ == "__main__":
    main()
