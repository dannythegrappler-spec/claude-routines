#!/usr/bin/env python3
"""
Reads checklist-history.json and prints a compact, class-based HTML fragment
(no <html>/<body> wrapper) showing the full 30-day item x day grid, styled
with CDS-style CSS variables. Intended to be piped straight into the
mcp__visualize__show_widget widget_code parameter.

Usage: python3 generate_table_html.py <folder>   (folder defaults to ".")
Prints HTML to stdout. Also writes it to <folder>/table_widget.html.
"""
import sys, os, json
from datetime import date, timedelta

FOLDER = sys.argv[1] if len(sys.argv) > 1 else "."
HISTORY_PATH = os.path.join(FOLDER, "checklist-history.json")
OUT_PATH = os.path.join(FOLDER, "table_widget.html")


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

    parts = []
    parts.append('<h2 class="sr-only" style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0);">Checklist 30 day completion table, items by day, showing time taken, none if not completed, or null if not logged</h2>')
    parts.append('''<style>
.rt{border-collapse:collapse;font-size:12px;table-layout:fixed}
.rt th{text-align:center;padding:8px 4px;font-weight:500;color:var(--text-secondary);border-bottom:0.5px solid var(--border);white-space:nowrap}
.rt td{padding:6px 4px;text-align:center;border-bottom:0.5px solid var(--border)}
.rt tr:last-child td{border-bottom:none}
.ic{position:sticky;left:0;z-index:1;background:var(--surface-2);text-align:left!important;padding:6px 10px!important;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.rt th.ic{z-index:2;font-weight:500;color:var(--text-secondary);padding:8px 10px!important}
.nu{color:var(--text-muted);font-size:11px;font-style:italic}
.no{background:var(--bg-danger);color:var(--text-danger);font-size:11px;padding:1px 6px;border-radius:var(--radius)}
.dn{color:var(--text-primary)}
</style>''')
    parts.append('<div style="overflow-x:auto; border:0.5px solid var(--border); border-radius:12px;"><table class="rt"><colgroup><col style="width:190px;">')
    for _ in days:
        parts.append('<col style="width:70px;">')
    parts.append('</colgroup>')
    parts.append('<thead><tr><th class="ic">Item</th>')
    for d in days:
        parts.append(f'<th>{esc(d["label"])}</th>')
    parts.append('</tr></thead><tbody>')

    for item in items:
        parts.append(f'<tr><td class="ic">{esc(item)}</td>')
        for d in days:
            rec = d["records"].get(item)
            if rec is None:
                cell = '<span class="nu">null</span>'
            elif rec["completed"]:
                val = rec["value"] or "check"
                cell = f'<span class="dn">{esc(val)}</span>'
            else:
                cell = '<span class="no">None</span>'
            parts.append(f'<td>{cell}</td>')
        parts.append('</tr>')

    parts.append('</tbody></table></div>')
    html = "".join(parts)

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print(html)


if __name__ == "__main__":
    main()
