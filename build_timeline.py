import pandas as pd

SRC = "checklist.ods"
OUT = "Checklist Timeline.html"

df = pd.read_excel(SRC, engine="odf")

CHECK_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="#0f6e56" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 12.5 9.5 18 20 6"></polyline></svg>'
CLOCK_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="#0f6e56" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"></circle><polyline points="12 7 12 12 16 14"></polyline></svg>'


def is_completed(row):
    val = row.get("Completed")
    if pd.isna(val):
        return False
    return str(val).strip().lower() == "yes"


rows_html = []
n = len(df)
prev_item_name = None

for i, row in df.iterrows():
    item = str(row["Item"]).strip()
    completed = is_completed(row)
    is_last = i == n - 1

    line_div = '<div class="line"></div>' if not is_last else ""

    if completed:
        dot_class = "dot done"
        dot_inner = CHECK_SVG
        time_completed = row.get("Time Completed")
        if pd.isna(time_completed):
            time_text = ""
        else:
            time_text = f'<p class="item-time">Completed at {time_completed}</p>'
        if prev_item_name is None:
            badge = '<p class="start-label">Starting point</p>'
        else:
            elapsed = row.get("Time Elapsed")
            elapsed_str = "" if pd.isna(elapsed) else str(elapsed).strip()
            badge = (
                f'<span class="elapsed-badge">{CLOCK_SVG}'
                f'{elapsed_str} since {prev_item_name}</span>'
            )
        content_extra = time_text + "\n          " + badge
        prev_item_name = item
    else:
        dot_class = "dot pending"
        dot_inner = ""
        content_extra = '<p class="item-time pending-text">Not completed yet</p>\n          '

    rows_html.append(f'''      <div class="row">
        <div class="rail">
          <div class="{dot_class}">{dot_inner}</div>
          {line_div}
        </div>
        <div class="content">
          <p class="item-name">{item}</p>
          {content_extra}
        </div>
      </div>''')

body_rows = "\n".join(rows_html)

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Checklist timeline</title>
<style>
  :root {{
    --bg: #f7f6f2;
    --card: #ffffff;
    --border: #e4e2da;
    --text-primary: #1f1e1b;
    --text-secondary: #6b6a63;
    --text-muted: #9c9a92;
    --accent: #0f6e56;
    --accent-bg: #e1f5ee;
    --accent-line: #5dcaa5;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    padding: 48px 20px;
    background: var(--bg);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    color: var(--text-primary);
  }}
  .wrap {{ max-width: 560px; margin: 0 auto; }}
  h1 {{ font-size: 20px; font-weight: 500; margin: 0 0 4px; }}
  .subtitle {{ font-size: 13px; color: var(--text-secondary); margin: 0 0 32px; }}
  .timeline {{ position: relative; }}
  .row {{ position: relative; display: flex; gap: 16px; padding-bottom: 24px; }}
  .row:last-child {{ padding-bottom: 0; }}
  .rail {{ position: relative; width: 24px; flex: none; display: flex; flex-direction: column; align-items: center; }}
  .dot {{ width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; z-index: 1; flex: none; }}
  .dot.done {{ background: var(--accent-bg); border: 1.5px solid var(--accent-line); }}
  .dot.pending {{ background: var(--card); border: 1.5px solid var(--border); }}
  .dot svg {{ width: 13px; height: 13px; }}
  .line {{ position: absolute; top: 24px; bottom: -24px; width: 2px; background: var(--border); left: 50%; transform: translateX(-50%); }}
  .content {{ flex: 1; padding-top: 2px; }}
  .item-name {{ font-size: 15px; font-weight: 500; margin: 0 0 2px; }}
  .item-time {{ font-size: 13px; color: var(--text-secondary); margin: 0; }}
  .item-time.pending-text {{ color: var(--text-muted); }}
  .elapsed-badge {{ display: inline-flex; align-items: center; gap: 6px; margin: 10px 0 0 0; font-size: 12px; color: var(--accent); background: var(--accent-bg); padding: 3px 10px; border-radius: 100px; font-weight: 500; }}
  .elapsed-badge svg {{ width: 12px; height: 12px; }}
  .start-label {{ font-size: 12px; color: var(--text-secondary); margin-top: 10px; }}
</style>
</head>
<body>
  <div class="wrap">
    <h1>Checklist</h1>
    <p class="subtitle">Items completed, with time elapsed between each</p>
    <div class="timeline">
{body_rows}
    </div>
  </div>
</body>
</html>
'''

with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)

print("wrote", OUT, "rows:", n)
