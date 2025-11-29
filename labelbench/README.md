# LabelBench

A lightweight Python-based web application for annotating LLM responses to build golden evaluation datasets. LabelBench provides a streamlined interface for capturing binary quality decisions (Accept/Reject) with structured feedback, stores annotations locally in SQLite, and offers an interactive dashboard focused on error analysis.

## Quick Start

### Prerequisites

- **Python 3.10+** installed
- **uv package manager** installed ([installation guide](https://github.com/astral-sh/uv))

### Installation

```bash
# Clone or navigate to the project directory
cd labelbench

# Install dependencies (creates virtual environment automatically)
uv sync --extra dev

# Run the application
uv run streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

## Architecture & Workflow

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Streamlit UI Layer                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Import Page  │  │ Annotate Page│  │Analysis Page │      │
│  │              │  │              │  │              │      │
│  │ • CSV/JSON   │  │ • Accept/    │  │ • Error      │      │
│  │   Upload     │  │   Reject     │  │   Charts     │      │
│  │ • Validation │  │ • Navigation │  │ • Breakdowns │      │
│  │ • Preview    │  │ • Progress   │  │ • Export     │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
└─────────┼──────────────────┼──────────────────┼──────────────┘
          │                  │                  │
          │                  │                  │
┌─────────▼──────────────────▼──────────────────▼──────────────┐
│                    Application Logic Layer                    │
├───────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────────┐          ┌──────────────────┐          │
│  │ Import/Export    │          │ Pydantic Models  │          │
│  │ Utilities        │          │                  │          │
│  │                  │          │ • Sample         │          │
│  │ • CSV Import     │─────────▶│ • Annotation     │          │
│  │ • JSON Import    │          │                  │          │
│  │ • CSV Export     │          └──────────────────┘          │
│  │ • Validation     │                                        │
│  └────────┬─────────┘                                        │
│           │                                                   │
│           │                                                   │
│  ┌────────▼───────────────────────────────────────────┐      │
│  │           Database Layer (SQLite)                  │      │
│  │                                                     │      │
│  │  • Context Manager for Transactions                │      │
│  │  • CRUD Operations                                 │      │
│  │  • Query Methods                                   │      │
│  │  • Metadata Parsing (Safe JSON)                   │      │
│  │                                                     │      │
│  │  ┌────────────────┐      ┌──────────────────┐    │      │
│  │  │  samples       │      │  annotations     │    │      │
│  │  │  table         │◀────▶│  table           │    │      │
│  │  │                │      │                  │    │      │
│  │  │ • id (PK)      │      │ • id (PK)        │    │      │
│  │  │ • prompt       │      │ • sample_id (FK) │    │      │
│  │  │ • response     │      │ • is_acceptable  │    │      │
│  │  │ • metadata     │      │ • primary_issue  │    │      │
│  │  │ • imported_at  │      │ • notes          │    │      │
│  │  └────────────────┘      │ • annotated_at   │    │      │
│  │                          └──────────────────┘    │      │
│  └───────────────────────────────────────────────────┘      │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### User Workflow

```
1. Import Dataset
   ↓
   User uploads CSV/JSON with prompt-response pairs
   ↓
   [Validation] → [Preview] → [Import to Database]
   
2. Annotate Samples
   ↓
   Review each sample, make binary Accept/Reject decision
   ↓
   If rejected: select primary issue type + add notes
   ↓
   [Save to Database]
   
3. Error Analysis (THE MAIN VALUE)
   ↓
   Interactive dashboard showing error distribution
   ↓
   Click error type → see all examples with that issue
   ↓
   Read notes to understand patterns
   ↓
   [Export filtered results]
   
4. Export Results
   ↓
   Download rejected samples for fixing
   ↓
   Generate summary report documenting findings
```

### Component Overview

#### **Models Layer** (`models/`)
- **`sample.py`**: Pydantic model for prompt-response pairs
- **`annotation.py`**: Pydantic model for human feedback with validation

#### **Storage Layer** (`storage/`)
- **`database.py`**: SQLite database with context manager for safe transactions
- **`import_export.py`**: CSV/JSON import with validation, export utilities

#### **UI Layer** (`ui/`)
- **`import_page.py`**: File upload and validation interface
- **`annotate_page.py`**: Binary annotation interface with navigation
- **`analysis_page.py`**: Interactive error analysis dashboard with Plotly charts

## Usage

### 1. Import Data

Navigate to **Import Data** and upload a CSV or JSON file.

#### CSV Format

```csv
id,prompt,response,model,task_type
1,"What's your return policy?","30 days for full refund",gpt-4,support
2,"Do you ship to Canada?","Yes, free shipping!",gpt-3.5,support
```

**Required columns:** `id`, `prompt`, `response`  
**Optional columns:** Any additional columns are stored as metadata

#### JSON Format

```json
{
  "samples": [
    {
      "id": "1",
      "prompt": "What's your return policy?",
      "response": "30 days for full refund",
      "metadata": {
        "model": "gpt-4",
        "task_type": "support"
      }
    }
  ]
}
```

#### Try the Example Dataset

LabelBench includes an example dataset with 20 customer support samples:

```bash
# The file is located at: data/example_samples.csv
# Import it through the UI to get started immediately
```

### 2. Annotate Samples

Navigate to **Annotate** to review samples:

1. Read the prompt and response
2. Click **Accept** ✅ or **Reject** ❌
3. If rejecting, select a primary issue type and add notes
4. Use navigation buttons to move through samples

### 3. Analyze Errors

Navigate to **Error Analysis** to view:

- Overall acceptance rate and statistics
- Interactive error distribution chart (click bars to filter)
- Detailed sample views with prompts, responses, and notes
- Breakdown by metadata (model, task type, etc.)

### 4. Export Results

- Export rejected samples as CSV from the Error Analysis page
- Filter by error type before exporting
- All exports include prompt, response, issue type, and notes

## Project Structure

```
labelbench/
├── models/              # Pydantic data models
│   ├── __init__.py
│   ├── sample.py
│   └── annotation.py
├── storage/             # Database and import/export
│   ├── __init__.py
│   ├── database.py
│   └── import_export.py
├── ui/                  # Streamlit UI pages
│   ├── __init__.py
│   ├── import_page.py
│   ├── annotate_page.py
│   └── analysis_page.py
├── tests/               # Unit tests
│   ├── __init__.py
│   ├── test_models.py
│   └── test_database.py
├── data/                # Example datasets
│   └── example_samples.csv
├── app.py               # Main Streamlit entry point
├── pyproject.toml       # Project dependencies
├── .gitignore
└── README.md
```

## Development

### Run Tests

```bash
uv run pytest tests/ -v
```

### Install Dev Dependencies

```bash
uv sync --extra dev
```

## Features

- ✅ **Import** prompt-response pairs from CSV/JSON
- ✅ **Annotate** with binary Accept/Reject decisions and structured feedback
- ✅ **Analyze** errors with interactive dashboard
- ✅ **Breakdown** acceptance rates by metadata (model, task type, etc.)
- ✅ **Local storage** with SQLite
- ✅ **Export** rejected samples and summary reports

## Tech Stack

- **Python 3.10+**
- **Streamlit** - Web UI framework
- **SQLite** - Local database
- **Pydantic** - Data validation
- **Pandas** - Data manipulation
- **Plotly** - Interactive charts
- **uv** - Modern Python package manager

## License

MIT

## Contributing

Contributions welcome! Please feel free to submit a Pull Request.

