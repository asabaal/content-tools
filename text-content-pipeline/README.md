# Text Content Pipeline

A deterministic pipeline for converting monthly themes into daily publishable images without requiring daily judgment.

## Installation

```bash
pip install -e .
playwright install chromium
```

## Usage

### Run full pipeline (multiple ways)

```bash
# Method 1: Using existing payload file
python tcp.py run-all --payload 2026-02_payload.json

# Method 2: Using inline theme (recommended)
python tcp.py run-all --theme "Evolving in Christ" --year 2026 --month 2

# With weekly subthemes
python tcp.py run-all --theme "Evolving in Christ" --year 2026 --month 2 --subthemes "Faith, Hope, Love"

# Skip rendering or text generation
python tcp.py run-all --theme "Evolving in Christ" --year 2026 --month 2 --skip-rendering
python tcp.py run-all --theme "Evolving in Christ" --year 2026 --month 2 --skip-text
```

### Initialize a new month

```bash
python tcp.py init-month 2026 2 --theme "Evolving in Christ"
```

### Demo

```bash
# Mode A: With explicit weekly subthemes
tcp demo --theme "faith, hope, love" --with-subthemes

# Mode B: AI-derived weekly subthemes
tcp demo --theme "faith, hope, love"
```

### Other commands

```bash
tcp validate 2026-02_payload.json
tcp resolve-calendar 2026-02_payload.json
tcp list-presets
tcp inspect-plan 2026-02_payload.json
```

## Requirements

- Python 3.11+
- Ollama with gpt-oss:20b model (or other compatible model)
- Playwright Chromium (for image rendering)

## License

[To be determined]
