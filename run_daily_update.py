import csv
import io
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from datetime import date

CSV_FILE = "checklist_input.csv"
ODS_FILE = "checklist.ods"

NS = {
    "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
    "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
    "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
}
for prefix, uri in NS.items():
    ET.register_namespace(prefix, uri)

EXPECTED_HEADER = ["Item", "Completed", "Priority", "Time Completed", "Goals", "Improvements"]


def q(tag):
    prefix, local = tag.split(":")
    return "{%s}%s" % (NS[prefix], local)


def parse_time_to_duration(value):
    m = re.match(r"^\s*(\d{1,2}):(\d{2})\s*([AaPp][Mm])\s*$", value)
    if not m:
        return None
    hour, minute, ampm = int(m.group(1)), int(m.group(2)), m.group(3).upper()
    if ampm == "AM":
        if hour == 12:
            hour = 0
    else:
        if hour != 12:
            hour += 12
    return "PT%02dH%02dM00S" % (hour, minute)


def build_cell(col_name, value):
    cell = ET.Element(q("table:table-cell"))
    if col_name == "Time Completed":
        cell.set(q("table:style-name"), "TimeCell")
        value = value.strip()
        if value:
            duration = parse_time_to_duration(value)
            if duration is None:
                raise ValueError(f"Could not parse time value: {value!r}")
            cell.set(q("office:value-type"), "time")
            cell.set(q("office:time-value"), duration)
            p = ET.SubElement(cell, q("text:p"))
            p.text = value
        else:
            cell.set(q("office:value-type"), "string")
            ET.SubElement(cell, q("text:p"))
    else:
        cell.set(q("office:value-type"), "string")
        p = ET.SubElement(cell, q("text:p"))
        if value:
            p.text = value
    return cell


def update_content_xml(content_bytes, csv_text):
    reader = csv.reader(io.StringIO(csv_text))
    rows = list(reader)
    header = rows[0]
    if header != EXPECTED_HEADER:
        raise ValueError(f"Header mismatch.\nExpected: {EXPECTED_HEADER}\nGot:      {header}")
    data_rows = rows[1:]

    root = ET.fromstring(content_bytes)
    table = root.find(f".//{q('table:table')}[@{q('table:name')}='Checklist']")
    if table is None:
        raise ValueError("Could not find table named 'Checklist'")

    all_rows = table.findall(q("table:table-row"))
    for r in all_rows[1:]:
        table.remove(r)

    for data_row in data_rows:
        row_el = ET.Element(q("table:table-row"))
        for col_name, value in zip(EXPECTED_HEADER, data_row):
            row_el.append(build_cell(col_name, value))
        table.append(row_el)

    xml_bytes = ET.tostring(root, encoding="UTF-8", xml_declaration=False)
    return b"<?xml version='1.0' encoding='UTF-8'?>\n" + xml_bytes


def update_ods(path, csv_text):
    with zipfile.ZipFile(path, "r") as zin:
        infos = zin.infolist()
        contents = {info.filename: zin.read(info.filename) for info in infos}

    contents["content.xml"] = update_content_xml(contents["content.xml"], csv_text)

    with zipfile.ZipFile(path, "w") as zout:
        for info in infos:
            data = contents[info.filename]
            compress_type = zipfile.ZIP_STORED if info.filename == "mimetype" else zipfile.ZIP_DEFLATED
            new_info = zipfile.ZipInfo(info.filename, date_time=info.date_time)
            new_info.compress_type = compress_type
            new_info.external_attr = info.external_attr
            zout.writestr(new_info, data)


REPORT_OUTPUT_FILES = [
    ODS_FILE,
    "checklist-history.json",
    "30-day-report.ods",
    "Checklist Timeline.html",
    "table_widget.html",
    "artifact_grid.html",
]


def git(*args):
    result = subprocess.run(["git", *args], capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit(f"git {' '.join(args)} failed:\n{result.stdout}\n{result.stderr}")
    return result.stdout


def run_script(script_name):
    print(f"Running {script_name}...")
    result = subprocess.run([sys.executable, script_name], capture_output=True, text=True)
    if result.stdout:
        print(result.stdout, end="")
    if result.returncode != 0:
        sys.exit(f"{script_name} failed:\n{result.stderr}")


def read_csv_from_prompt():
    print("Paste your checklist CSV update (header + rows), then press Enter on a blank line when done:")
    lines = []
    while True:
        line = input()
        if line.strip() == "" and lines:
            break
        lines.append(line)
    csv_text = "\n".join(lines) + "\n"
    with open(CSV_FILE, "w", encoding="utf-8") as f:
        f.write(csv_text)
    return csv_text


def main():
    csv_text = read_csv_from_prompt()

    print(f"Updating {ODS_FILE}...")
    update_ods(ODS_FILE, csv_text)

    run_script("generate_report.py")
    run_script("build_timeline.py")
    run_script("generate_table_html.py")
    run_script("generate_artifact_html.py")

    print("Committing and pushing...")
    git("add", *REPORT_OUTPUT_FILES)
    status = git("status", "--porcelain", *REPORT_OUTPUT_FILES)
    if not status.strip():
        print("No changes to commit.")
    else:
        git("commit", "-m", f"Update checklist - {date.today().isoformat()}")
        git("push")
        print("Pushed.")

    print("\n=== DONE — checklist and reports updated ===")


if __name__ == "__main__":
    main()
