"""Prompt templates for AI generation."""

from src.slots.enum import SlotFunction

# Touchpoint 1: Weekly Subtheme Derivation Prompt
WEEKLY_SUBTHEME_PROMPT = """You are assisting in breaking down a monthly theme into weekly subthemes.

Monthly theme: {monthly_theme}
Number of weeks in month: {num_weeks}

Your task:
Generate {num_weeks} ordered weekly subthemes that explore different facets of this theme.

Requirements:
- Output exactly {num_weeks} subthemes
- Each subtheme should be a short phrase (2-6 words)
- Subthemes should be ordered to create a natural progression
- Do not introduce new domains outside the monthly theme
- Keep subthemes focused and thematic

Output format:
Return ONLY a JSON array of strings, for example:
["First facet", "Second facet", "Third facet", "Fourth facet"]

Do not include explanations or any other text."""


# Touchpoint 2: Monthly Slot Planning Prompt
MONTHLY_SLOT_PLANNING_PROMPT = """You are creating a content schedule for a month.

Monthly theme: {monthly_theme}

Weekly subthemes:
{weekly_subthemes_formatted}

Available slot types (you must use only these):
- declarative_statement: A single grounded statement
- excerpt: A quote or passage
- process_note: A reflective note on formation
- unanswered_question: An open-ended question
- reframing: A perspective shift
- quiet_observation: Something noticed, not concluded

Your task:
Decide which slot type should be assigned to each automated day (Monday-Saturday) for each week.

Requirements:
- Each slot type may appear 0, 1, or 2 times per week (never more than 2)
- Each automated day (Monday-Saturday) must be assigned a slot type
- Sundays are excluded (they are reserved for human content)
- Match slot types to the week's subtheme
- Avoid repeating the same slot type on consecutive days when possible
- Only assign slots to dates in the calendar structure below

Calendar structure:
{calendar_structure_formatted}

Expected output:
You must assign a slot type to EVERY date listed in the calendar above that falls on Monday-Saturday.
Do not assign slots to dates not in the calendar.

Output format:
Return ONLY a JSON object mapping date strings to slot type strings, for example:
{{
  "2026-03-02": "declarative_statement",
  "2026-03-03": "excerpt",
  ...
}}

Do not include explanations or any other text."""


# Touchpoint 3: Daily Text Generation Prompts
TEXT_GENERATION_PROMPTS: dict[SlotFunction, str] = {
    SlotFunction.DECLARATIVE_STATEMENT: """Monthly theme: {monthly_theme}
Weekly subtheme: {weekly_subtheme}

Task: Write a single declarative statement related to the theme and subtheme.

Requirements:
- One sentence only
- A grounded, factual statement
- No question marks
- No explanations or elaborations
- Plain text only (no markdown, no emojis, no hashtags)

Output: Just the sentence, nothing else.""",

    SlotFunction.EXCERPT: """Monthly theme: {monthly_theme}
Weekly subtheme: {weekly_subtheme}

Task: Write an excerpt (a short passage, quote, or line) that connects to the theme and subtheme.

Requirements:
- A single paragraph or quote
- Could be from notes, scripture, past writing, or reflection
- No commentary added
- Plain text only (no markdown, no emojis, no hashtags)

Output: Just the excerpt, nothing else.""",

    SlotFunction.PROCESS_NOTE: """Monthly theme: {monthly_theme}
Weekly subtheme: {weekly_subtheme}

Task: Write a reflective process note about formation, effort, slowness, or restraint.

Requirements:
- A brief note about ongoing process
- Acknowledges effort or stillness
- No conclusions or finality
- Plain text only (no markdown, no emojis, no hashtags)

Output: Just the note, nothing else.""",

    SlotFunction.UNANSWERED_QUESTION: """Monthly theme: {monthly_theme}
Weekly subtheme: {weekly_subtheme}

Task: Write an authentic, open-ended question that remains unanswered.

Requirements:
- A single sincere question
- No answer provided
- No leading or rhetorical framing
- Plain text only (no markdown, no emojis, no hashtags)

Output: Just the question, nothing else.""",

    SlotFunction.REFRAMING: """Monthly theme: {monthly_theme}
Weekly subtheme: {weekly_subtheme}

Task: Write a reframing statement (a "not X, but Y" perspective shift).

Requirements:
- A single sentence that reframes something
- Uses "not X, but Y" structure or similar
- No explanation of why
- Plain text only (no markdown, no emojis, no hashtags)

Output: Just the reframing, nothing else.""",

    SlotFunction.QUIET_OBSERVATION: """Monthly theme: {monthly_theme}
Weekly subtheme: {weekly_subtheme}

Task: Write a quiet observation of something noticed.

Requirements:
- A single sentence or short observation
- Describes something noticed, not concluded
- No interpretation or judgment
- Plain text only (no markdown, no emojis, no hashtags)

Output: Just the observation, nothing else.""",
}


def format_weekly_subthemes(subthemes: list[str]) -> str:
    """Format subthemes for prompt display."""
    return "\n".join([f"  Week {i+1}: {subtheme}" for i, subtheme in enumerate(subthemes)])


def format_calendar_structure(calendar_info: list[dict], automated_dates: list[str] | None = None) -> str:
    """Format calendar structure for prompt display."""
    lines = []
    for week_info in calendar_info:
        lines.append(f"  Week {week_info['week_number']}: {week_info.get('monday_date', 'N/A')} - {week_info.get('sunday_date', 'N/A')} ({week_info['month']}-{week_info['year']:02d})")
        lines.append(f"    Subtheme: {week_info['subtheme']}")
        lines.append(f"    Video week: {week_info['is_video_week']}")

    # Add explicit automated dates list
    if automated_dates:
        lines.append(f"\nAutomated dates requiring slot assignments ({len(automated_dates)} total):")
        for date in automated_dates:
            from datetime import datetime
            dt = datetime.strptime(date, "%Y-%m-%d")
            lines.append(f"  - {date} ({dt.strftime('%A')})")

    return "\n".join(lines)
