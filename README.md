# LabelBench

A lightweight Python-based web application for annotating LLM responses to build golden evaluation datasets. LabelBench helps you quickly review prompt-response pairs, capture quality decisions with structured feedback, and analyze error patterns to improve your models.

## What It Does

LabelBench provides a streamlined interface for:
- **Importing** prompt-response pairs from CSV or JSON files
- **Annotating** samples with binary Accept/Reject decisions and detailed rejection notes
- **Analyzing** error patterns through an interactive dashboard
- **Exporting** rejected samples for downstream evaluation and model improvement

## Quick Start

### Prerequisites
- Python 3.10+
- [uv package manager](https://github.com/astral-sh/uv) installed

### Run the Application

```bash
cd labelbench
uv sync --extra dev
uv run streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`.

### Using the Application

1. **Import Data** - Upload CSV/JSON files with `id`, `prompt`, and `response` columns
   - Try the example dataset: `labelbench/data/example_samples.csv`
2. **Annotate** - Review samples and mark Accept ✅ or Reject ❌ with structured feedback
3. **Error Analysis** - Explore error distribution, filter by issue type, and export results

For detailed usage instructions, see [`labelbench/README.md`](labelbench/README.md).

## Repository Structure

```text
coderabbit-trial/
├── labelbench/          # Main application (entry point: app.py)
│   ├── app.py          # Streamlit entry point - START HERE
│   ├── models/         # Data models
│   ├── storage/        # Database & import/export
│   ├── ui/             # UI pages
│   └── README.md       # Complete application documentation
│
├── archive_files/      # Archived development documentation
│   ├── PROJECT_REFERENCE.md
│   └── UI_CHANGES.md
│
└── labelbench_spec.md  # Technical specification
```

## Documentation

- **Application Guide**: [`labelbench/README.md`](labelbench/README.md) - Complete usage guide, architecture, and examples
- **Technical Spec**: `labelbench_spec.md` - Full implementation specification
- **Archived Docs**: `archive_files/` - Historical development documentation and project references

## License

MIT
