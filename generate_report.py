#!/usr/bin/env python3
"""
Reads Checklist.ods, logs today's snapshot into checklist-history.json,
and rebuilds 30-day-report.ods (items x last-30-days grid) in the same folder.

Run this from within the Checklist folder, or pass the folder as argv[1].
"""
import sys, os, json, re, zipfile
from datetime import date, datetime, timedelta

FOLDER = sys.argv[1] if len(sys.argv) > 1 else "."
CHECKLIST_PATH = os.path.join(FOLDER, "checklist.ods")
HISTORY_PATH = os.path.join(FOLDER, "checklist-history.json")
REPORT_PATH = os.path.join(FOLDER, "30-day-report.ods")


def read_checklist_rows(path):
    import pandas as pd
    df = pd.read_excel(path, engine="odf", header=0)
    df = df.fillna("")
    rows = []
    for _, r in df.iterrows():
        item = str(r.get("Item", "")).strip()
        if not item:
            continue
        completed_raw = str(r.get("Completed", "")).strip().lower()
        completed = completed_raw in ("yes", "true")
        time_completed = str(r.get("Time Completed", "")).strip()
        rows.append({"name": item, "completed": completed, "time": time_completed})
    return rows


def parse_time_to_minutes(s):
    if not s:
        return None
    m = re.match(r"^(\d{1,2}):(\d{2})\s*([AaPp][Mm])?$", s.strip())
    if not m:
        return None
    hh = int(m.group(1))
    mm = int(m.group(2))
    ampm = m.group(3).upper() if m.group(3) else None
    if ampm == "PM" and hh != 12:
        hh += 12
    if ampm == "AM" and hh == 12:
        hh = 0
    return hh * 60 + mm


def format_duration(mins):
    if mins is None or mins < 0:
        return None
    if mins < 60:
        return f"{mins} min"
    h, rem = divmod(mins, 60)
    return f"{h}h" if rem == 0 else f"{h}h {rem}m"


def compute_records(rows):
    records = []
    last_minutes = None
    for r in rows:
        value = None
        if r["completed"]:
            cur = parse_time_to_minutes(r["time"])
            if cur is not None and last_minutes is not None:
                diff = cur - last_minutes
                if diff < 0:
                    diff += 24 * 60
                value = format_duration(diff)
            elif r["time"]:
                value = r["time"]
            if cur is not None:
                last_minutes = cur
        records.append({"name": r["name"], "completed": r["completed"], "value": value})
    return records


def load_history():
    if os.path.exists(HISTORY_PATH):
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_history(hist):
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(hist, f, ensure_ascii=False, indent=2)


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_content_xml(items, days):
    p = []
    p.append('<?xml version="1.0" encoding="UTF-8"?>')
    p.append('<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
              'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" '
              'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" '
              'xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" '
              'xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0" office:version="1.2">')
    p.append('<office:automatic-styles>')
    p.append('<style:style style:name="ceHeader" style:family="table-cell"><style:table-cell-properties fo:background-color="#2b2b2b"/><style:text-properties fo:color="#ffffff" fo:font-weight="bold"/></style:style>')
    p.append('<style:style style:name="ceItem" style:family="table-cell"><style:text-properties fo:font-weight="bold"/></style:style>')
    p.append('<style:style style:name="ceNone" style:family="table-cell"><style:text-properties fo:color="#ff0000"/></style:style>')
    p.append('<style:style style:name="ceNull" style:family="table-cell"><style:text-properties fo:color="#bbbbbb" fo:font-style="italic"/></style:style>')
    p.append('<style:style style:name="ceDone" style:family="table-cell"><style:text-properties fo:color="#000000"/></style:style>')
    p.append('<style:style style:name="coWide" style:family="table-column"><style:table-column-properties style:column-width="1.8in"/></style:style>')
    p.append('<style:style style:name="coDay" style:family="table-column"><style:table-column-properties style:column-width="0.85in"/></style:style>')
    p.append('</office:automatic-styles>')
    p.append('<office:body><office:spreadsheet>')
    p.append('<table:table table:name="30-Day Report">')
    p.append('<table:table-column table:style-name="coWide"/>')
    p.append(f'<table:table-column table:style-name="coDay" table:number-columns-repeated="{len(days)}"/>')

    p.append('<table:table-row>')
    p.append('<table:table-cell table:style-name="ceHeader" office:value-type="string"><text:p>Item</text:p></table:table-cell>')
    for d in days:
        p.append(f'<table:table-cell table:style-name="ceHeader" office:value-type="string"><text:p>{esc(d["label"])}</text:p></table:table-cell>')
    p.append('</table:table-row>')

    for item in items:
        p.append('<table:table-row>')
        p.append(f'<table:table-cell table:style-name="ceItem" office:value-type="string"><text:p>{esc(item)}</text:p></table:table-cell>')
        for d in days:
            rec = d["records"].get(item)
            if rec is None:
                p.append('<table:table-cell table:style-name="ceNull" office:value-type="string"><text:p>null</text:p></table:table-cell>')
            elif rec["completed"]:
                val = rec["value"] or "✓"
                p.append(f'<table:table-cell table:style-name="ceDone" office:value-type="string"><text:p>{esc(val)}</text:p></table:table-cell>')
            else:
                p.append('<table:table-cell table:style-name="ceNone" office:value-type="string"><text:p>None</text:p></table:table-cell>')
        p.append('</table:table-row>')

    p.append('</table:table></office:spreadsheet></office:body></office:document-content>')
    return "".join(p)


MANIFEST_XML = '''<?xml version="1.0" encoding="UTF-8"?>
<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" manifest:version="1.2">
<manifest:file-entry manifest:full-path="/" manifest:version="1.2" manifest:media-type="application/vnd.oasis.opendocument.spreadsheet"/>
<manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>
</manifest:manifest>'''


def build_report(hist):
    keys = sorted(hist.keys())
    if not keys:
        return None
    latest_key = keys[-1]
    items = []
    seen = set()
    for rec in hist[latest_key]["items"]:
        if rec["name"] not in seen:
            items.append(rec["name"])
            seen.add(rec["name"])
    for k in keys:
        for rec in hist[k]["items"]:
            if rec["name"] not in seen:
                items.append(rec["name"])
                seen.add(rec["name"])

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

    content_xml = build_content_xml(items, days)
    with zipfile.ZipFile(REPORT_PATH, "w") as z:
        z.writestr("mimetype", "application/vnd.oasis.opendocument.spreadsheet", compress_type=zipfile.ZIP_STORED)
        z.writestr("META-INF/manifest.xml", MANIFEST_XML)
        z.writestr("content.xml", content_xml)
    return REPORT_PATH


def main():
    if not os.path.exists(CHECKLIST_PATH):
        print(f"ERROR: {CHECKLIST_PATH} not found")
        sys.exit(1)

    rows = read_checklist_rows(CHECKLIST_PATH)
    records = compute_records(rows)

    hist = load_history()
    today_key = date.today().isoformat()
    hist[today_key] = {"loggedAt": datetime.now().isoformat(), "items": records}
    save_history(hist)

    report_path = build_report(hist)
    done = sum(1 for r in records if r["completed"])
    print(f"Logged {today_key}: {done}/{len(records)} completed.")
    print(f"History now has {len(hist)} day(s) logged.")
    print(f"Report written to {report_path}")


if __name__ == "__main__":
    main()
