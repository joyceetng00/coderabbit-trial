# LabelBench Repository

This repository contains the LabelBench application - a lightweight Python-based web application for annotating LLM responses to build golden evaluation datasets.

## 📁 Repository Structure

```
coderabbit-trial/
├── labelbench/              # Main application directory
│   ├── app.py              # Streamlit entry point
│   ├── models/             # Pydantic data models
│   ├── storage/            # Database & import/export utilities
│   ├── ui/                 # Streamlit UI pages
│   ├── tests/              # Unit tests
│   ├── data/               # Example datasets
│   ├── pyproject.toml      # Project dependencies
│   └── README.md           # Application documentation
│
├── context_files/          # Development & specification documents
│   ├── SPEC_REVIEW.md      # Technical review of the specification
│   ├── SPEC_UPDATES.md     # Changes made to the original spec
│   ├── TESTING_CHECKLIST.md # Testing requirements & setup guide
│   └── UI_CHANGES.md       # UI bug fixes & improvements
│
├── labelbench_spec.md      # Complete technical specification
└── README.md               # This file
```

## 🚀 Quick Start

### For Users
Navigate to the `labelbench/` directory and follow the instructions in `labelbench/README.md`:

```bash
cd labelbench
uv sync --extra dev
uv run streamlit run app.py
```

### For Developers
See the documentation files in `context_files/` for development context.

## 📚 Documentation Navigation

### Application Documentation
- **`labelbench/README.md`** - Complete application guide with:
  - Quick start instructions
  - Architecture diagrams
  - Usage examples
  - Feature overview

### Development Context
All development-related documents are in `context_files/`:

- **`SPEC_REVIEW.md`** - Technical review of the specification:
  - Architecture assessment
  - Critical issues identified
  - Technology stack review
  - Recommendations for improvements

- **`SPEC_UPDATES.md`** - Changes made to the original specification:
  - Package manager switch (uv)
  - Time reference removals
  - Critical bug fixes
  - Implementation completion notes

- **`TESTING_CHECKLIST.md`** - Testing requirements:
  - What you need to prepare separately
  - Environment setup
  - Testing workflow
  - Common issues & solutions

- **`UI_CHANGES.md`** - UI improvements and bug fixes:
  - Issues identified
  - Proposed fixes
  - Implementation details
  - Testing checklist

### Technical Specification
- **`labelbench_spec.md`** - Complete technical specification:
  - Full implementation guide
  - Phase-by-phase instructions
  - Code examples
  - PR structure

## 🗂️ Directory Details

### `labelbench/` - Main Application
The complete LabelBench application with all components:

- **`app.py`** - Main Streamlit entry point with navigation
- **`models/`** - Pydantic data models (Sample, Annotation)
- **`storage/`** - Database layer and import/export utilities
- **`ui/`** - Streamlit UI pages (Import, Annotate, Analysis)
- **`tests/`** - Unit tests for models and database
- **`data/`** - Example datasets for testing
- **`pyproject.toml`** - Project dependencies and configuration

### `context_files/` - Development Documentation
Supporting documents for understanding the development process:

- Technical reviews and assessments
- Specification updates and changes
- Testing guides and checklists
- UI improvement documentation

## 🔍 Finding What You Need

### I want to...
- **Run the application** → See `labelbench/README.md`
- **Understand the architecture** → See `labelbench/README.md` (architecture diagram)
- **Review technical decisions** → See `context_files/SPEC_REVIEW.md`
- **See what changed from spec** → See `context_files/SPEC_UPDATES.md`
- **Set up for testing** → See `context_files/TESTING_CHECKLIST.md`
- **Understand UI fixes** → See `context_files/UI_CHANGES.md`
- **Read the full spec** → See `labelbench_spec.md`
- **Find code examples** → See `labelbench_spec.md` or browse `labelbench/`

## 🛠️ Development Workflow

1. **Read the spec** → `labelbench_spec.md`
2. **Review technical assessment** → `context_files/SPEC_REVIEW.md`
3. **Check updates** → `context_files/SPEC_UPDATES.md`
4. **Set up environment** → `context_files/TESTING_CHECKLIST.md`
5. **Review UI changes** → `context_files/UI_CHANGES.md`
6. **Run the app** → `labelbench/README.md`

## 📝 Key Features

- ✅ Import prompt-response pairs from CSV/JSON
- ✅ Binary Accept/Reject annotation with structured feedback
- ✅ Interactive error analysis dashboard
- ✅ Metadata breakdowns and filtering
- ✅ Local SQLite storage
- ✅ Export rejected samples for downstream evaluation

## 🔗 Quick Links

- [Application README](labelbench/README.md)
- [Technical Specification](labelbench_spec.md)
- [Technical Review](context_files/SPEC_REVIEW.md)
- [Spec Updates](context_files/SPEC_UPDATES.md)
- [Testing Guide](context_files/TESTING_CHECKLIST.md)
- [UI Changes](context_files/UI_CHANGES.md)

## 📄 License

MIT
