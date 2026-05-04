"""Generate an HTML preview of generated texts for a month."""

import html
import json
from collections import defaultdict
from pathlib import Path

SLOT_COLORS = {
    "declarative_statement": {"bg": "#3B82F6", "label": "Declarative"},
    "excerpt": {"bg": "#10B981", "label": "Excerpt"},
    "process_note": {"bg": "#F59E0B", "label": "Process Note"},
    "unanswered_question": {"bg": "#8B5CF6", "label": "Question"},
    "reframing": {"bg": "#EF4444", "label": "Reframing"},
    "quiet_observation": {"bg": "#14B8A6", "label": "Observation"},
    "human_intentional": {"bg": "#6B7280", "label": "Human"},
}

WEEKDAY_SHORT = {
    "Monday": "Mon",
    "Tuesday": "Tue",
    "Wednesday": "Wed",
    "Thursday": "Thu",
    "Friday": "Fri",
    "Saturday": "Sat",
    "Sunday": "Sun",
}

MONTH_NAMES = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}


def _slot_pill(slot_type: str) -> str:
    info = SLOT_COLORS.get(slot_type, {"bg": "#6B7280", "label": slot_type})
    return (
        f'<span style="background:{info["bg"]};color:#fff;'
        f'padding:2px 8px;border-radius:9999px;font-size:11px;'
        f'font-weight:600;letter-spacing:0.5px;text-transform:uppercase;">'
        f'{info["label"]}</span>'
    )


def _date_display(date_str: str) -> str:
    parts = date_str.split("-")
    return f"{int(parts[1])}/{int(parts[2])}"


def _infer_week_number(date_str: str, year: int, month: int) -> int:
    from datetime import date, timedelta

    d = date.fromisoformat(date_str)
    monday = d - timedelta(days=d.weekday())
    first_day = date(year, month, 1)
    first_monday = first_day
    while first_monday.weekday() != 0:
        first_monday += timedelta(days=1)
    delta_weeks = (monday - first_monday).days // 7
    return delta_weeks + 1


def generate_preview(plan_dir: Path, year: int | None = None, month: int | None = None) -> Path:
    plans_dir = plan_dir / "plans"
    plan_files = sorted(
        [f for f in plans_dir.glob("*_plan.json") if not f.name.startswith("temp_")]
    )
    if not plan_files:
        raise FileNotFoundError(f"No plan file found in {plans_dir}")

    if year is not None and month is not None:
        target = f"{year}-{month:02d}_plan.json"
        match = [f for f in plan_files if f.name == target]
        if not match:
            raise FileNotFoundError(
                f"No plan file for {year}-{month:02d} in {plans_dir}"
            )
        plan_file = match[0]
    else:
        plan_file = plan_files[-1]

    texts_files = list(plans_dir.glob("*_texts.json"))
    if not texts_files:
        raise FileNotFoundError(f"No texts file found in {plans_dir}")

    plan_stem = plan_file.stem.replace("_plan", "")
    matching_texts = [f for f in texts_files if f.name.startswith(plan_stem)]
    texts_file = matching_texts[0] if matching_texts else texts_files[0]

    with open(plan_file, "r", encoding="utf-8") as f:
        plan = json.load(f)

    with open(texts_file, "r", encoding="utf-8") as f:
        texts = json.load(f)

    generated_texts = texts.get("texts", {})
    monthly_theme = plan["monthly_theme"]
    year = plan["year"]
    month = plan["month"]
    schedule = plan.get("schedule_summary", [])
    weekly_subthemes = plan.get("weekly_subthemes", [])
    weekly_subtitles = plan.get("weekly_subtitles", {})

    slot_plan = plan.get("slot_plan", {})

    weeks: dict[int, list[dict]] = defaultdict(list)
    for slot in schedule:
        wn = slot.get("week_number")
        if wn is None:
            date_str = slot["date"]
            wn = _infer_week_number(date_str, year, month)
            slot["week_number"] = wn
        weeks[slot["week_number"]].append(slot)

    cards_html = ""
    for week_num in sorted(weeks.keys()):
        subtheme = weekly_subthemes[week_num - 1] if week_num <= len(weekly_subthemes) else ""
        subtitle = weekly_subtitles.get(str(week_num), "")

        cards_html += f"""
        <div class="week-section">
          <div class="week-header">
            <div class="week-number">Week {week_num}</div>
            <div class="week-subtheme">{html.escape(subtheme)}</div>
            {f'<div class="week-subtitle">{html.escape(subtitle)}</div>' if subtitle else ''}
          </div>
          <div class="cards">
"""

        for slot in weeks[week_num]:
            date_str = slot["date"]
            weekday = slot["weekday"]
            slot_type = slot["slot_type"]
            is_auto = slot["is_automated"]
            text = generated_texts.get(date_str, "")

            if is_auto:
                card_class = "card"
                content_html = f'<div class="card-text">{html.escape(text)}</div>'
            else:
                card_class = "card card-human"
                content_html = (
                    '<div class="card-human-label">Human Intentional</div>'
                    '<div class="card-text-muted">No automated text. Write your own.</div>'
                )

            cards_html += f"""
            <div class="{card_class}">
              <div class="card-top">
                <span class="card-date">{_date_display(date_str)}</span>
                <span class="card-weekday">{WEEKDAY_SHORT.get(weekday, weekday)}</span>
                {_slot_pill(slot_type)}
              </div>
              {content_html}
            </div>
"""

        cards_html += """
          </div>
        </div>
"""

    total_auto = sum(1 for s in schedule if s["is_automated"])
    total_human = sum(1 for s in schedule if not s["is_automated"])

    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(monthly_theme)} &mdash; {MONTH_NAMES.get(month, str(month))} {year}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
    background: #111111;
    color: #E5E5E5;
    padding: 32px 16px 64px;
    max-width: 900px;
    margin: 0 auto;
    line-height: 1.6;
  }}
  .header {{
    text-align: center;
    margin-bottom: 48px;
    padding-bottom: 32px;
    border-bottom: 1px solid #2A2A2A;
  }}
  .header-theme {{
    font-size: 28px;
    font-weight: 700;
    color: #FFFFFF;
    margin-bottom: 8px;
    letter-spacing: -0.5px;
  }}
  .header-month {{
    font-size: 15px;
    color: #888888;
    font-weight: 500;
  }}
  .stats {{
    display: flex;
    justify-content: center;
    gap: 24px;
    margin-top: 16px;
    font-size: 13px;
    color: #666666;
  }}
  .stats span {{ color: #AAAAAA; font-weight: 600; }}
  .week-section {{
    margin-bottom: 48px;
  }}
  .week-header {{
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid #1E1E1E;
  }}
  .week-number {{
    font-size: 13px;
    font-weight: 600;
    color: #666666;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 4px;
  }}
  .week-subtheme {{
    font-size: 17px;
    font-weight: 600;
    color: #CCCCCC;
  }}
  .week-subtitle {{
    font-size: 13px;
    color: #888888;
    margin-top: 2px;
    font-style: italic;
  }}
  .cards {{
    display: flex;
    flex-direction: column;
    gap: 10px;
  }}
  .card {{
    background: #1A1A1A;
    border: 1px solid #2A2A2A;
    border-radius: 8px;
    padding: 16px 20px;
  }}
  .card-human {{
    background: #141414;
    border-style: dashed;
  }}
  .card-top {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;
  }}
  .card-date {{
    font-size: 14px;
    font-weight: 700;
    color: #FFFFFF;
    min-width: 36px;
  }}
  .card-weekday {{
    font-size: 12px;
    color: #666666;
    font-weight: 500;
    min-width: 30px;
  }}
  .card-text {{
    font-size: 15px;
    color: #D4D4D4;
    line-height: 1.65;
  }}
  .card-text-muted {{
    font-size: 14px;
    color: #444444;
    font-style: italic;
  }}
  .card-human-label {{
    font-size: 12px;
    color: #555555;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-weight: 600;
    margin-bottom: 4px;
  }}
</style>
</head>
<body>
  <div class="header">
    <div class="header-theme">{html.escape(monthly_theme)}</div>
    <div class="header-month">{MONTH_NAMES.get(month, str(month))} {year}</div>
    <div class="stats">
      <div>{total_auto} <span>posts</span></div>
      <div>{total_human} <span>human</span></div>
      <div>{len(weekly_subthemes)} <span>weeks</span></div>
    </div>
  </div>
{cards_html}
</body>
</html>"""

    output_path = plan_dir / "preview.html"
    output_path.write_text(full_html, encoding="utf-8")
    return output_path
