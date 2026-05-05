# logslice

Fast log file parser that filters and exports structured output by time range.

---

## Installation

```bash
pip install logslice
```

Or install from source:

```bash
git clone https://github.com/youruser/logslice.git
cd logslice && pip install .
```

---

## Usage

```python
from logslice import LogSlicer

slicer = LogSlicer("app.log", time_format="%Y-%m-%d %H:%M:%S")

results = slicer.slice(
    start="2024-01-15 08:00:00",
    end="2024-01-15 09:00:00"
)

slicer.export(results, output="filtered.json", fmt="json")
```

**CLI usage:**

```bash
logslice app.log --start "2024-01-15 08:00:00" --end "2024-01-15 09:00:00" --output filtered.json
```

### Options

| Flag | Description |
|------|-------------|
| `--start` | Start of time range |
| `--end` | End of time range |
| `--output` | Output file path |
| `--fmt` | Export format: `json`, `csv`, or `txt` (default: `txt`) |
| `--time-format` | Strptime format string for log timestamps |

---

## Features

- ⚡ Fast binary-search-based time range filtering
- 📦 Exports to JSON, CSV, or plain text
- 🔧 Configurable timestamp formats
- 🖥️ Simple CLI and Python API

---

## License

MIT © 2024 youruser