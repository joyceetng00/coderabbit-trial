# LabelBench Testing Checklist

## What You Need to Prepare Separately

### ✅ 1. Test Dataset (CSV or JSON)

You mentioned you already know about this, but here's the format needed:

**CSV Format:**
```csv
id,prompt,response,model,task_type
sample_1,"What's your return policy?","You can return items within 30 days...",gpt-4,customer_support
sample_2,"Do you ship to Canada?","Yes, we offer free shipping...",gpt-3.5,customer_support
```

**Required columns:** `id`, `prompt`, `response`  
**Optional columns:** Any additional columns become metadata

**JSON Format:**
```json
{
  "samples": [
    {
      "id": "sample_1",
      "prompt": "What's your return policy?",
      "response": "You can return items within 30 days...",
      "metadata": {
        "model": "gpt-4",
        "task_type": "customer_support"
      }
    }
  ]
}
```

**Recommendations:**
- Start with 20-50 samples for initial testing
- Include diverse error types (hallucinations, incomplete responses, wrong format, etc.)
- Mix of acceptable and problematic responses
- Varied metadata values (different models, task types) to test filtering

---

### ✅ 2. Environment Setup

**Python 3.10+ installed:**
```bash
python --version  # Should be 3.10 or higher
```

**uv package manager installed:**
```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh
# or
pip install uv
```

**Verify installation:**
```bash
uv --version
```

---

### ✅ 3. Install Dependencies

From the `labelbench` directory:
```bash
cd labelbench
uv sync --extra dev  # Installs all dependencies including dev tools
```

This will:
- Create virtual environment automatically
- Install Streamlit, Pandas, Plotly, Pydantic
- Install pytest for testing

---

### ✅ 4. Run Unit Tests First

Before running the app, verify core components work:
```bash
cd labelbench
uv run pytest tests/ -v
```

**Expected:** All tests should pass. If they fail, fix those issues before proceeding.

---

### ✅ 5. Test Import Functionality

Before using the UI, verify import works:
```python
# Quick test script (test_import.py)
from storage.import_export import import_csv

try:
    samples = import_csv("data/example_samples.csv")
    print(f"✅ Successfully imported {len(samples)} samples")
    print(f"First sample: {samples[0].id}")
except Exception as e:
    print(f"❌ Import failed: {e}")
```

Run with:
```bash
uv run python test_import.py
```

---

### ✅ 6. Verify Database Creation

When you first run the app, it should create `labelbench.db` automatically. Check:
```bash
ls -lh labelbench.db  # Should exist after first run
```

---

### ✅ 7. Streamlit Configuration (Optional)

Create `.streamlit/config.toml` if you want to customize:
```toml
[server]
port = 8501
maxUploadSize = 200  # MB, adjust if needed for large files
```

---

## What Gets Created Automatically

✅ Database file (`labelbench.db`) - Created on first run  
✅ SQLite tables and indexes - Created automatically  
✅ Session state - Managed by Streamlit  

---

## Quick Start Testing Workflow

1. **Prepare your dataset** → Save as `data/test_samples.csv`
2. **Install dependencies** → `uv sync --extra dev`
3. **Run tests** → `uv run pytest tests/ -v`
4. **Start app** → `uv run streamlit run app.py`
5. **Test import** → Upload your CSV in the Import page
6. **Test annotation** → Annotate a few samples
7. **Test analysis** → Check the Error Analysis dashboard
8. **Test export** → Export rejected samples

---

## Common Issues & Solutions

**Issue: "Module not found"**
- Solution: Run `uv sync` to install dependencies
- Make sure you're in the `labelbench` directory

**Issue: "Database locked"**
- Solution: Close any other instances of the app
- Delete `labelbench.db` and restart (will recreate it)

**Issue: "Import validation errors"**
- Check CSV has required columns: `id`, `prompt`, `response`
- Ensure IDs contain only letters, numbers, underscores, hyphens
- Check for empty rows or missing data

**Issue: "Port already in use"**
- Solution: Kill existing Streamlit process or change port in config

---

## Next Steps After Initial Testing

1. ✅ Import works correctly
2. ✅ Annotation saves to database
3. ✅ Error Analysis dashboard displays
4. ✅ Export functionality works
5. ✅ Navigation (Previous/Next/Jump) works
6. ✅ Bounds checking prevents crashes

---

## Files You Should Have

```
labelbench/
├── models/
│   ├── __init__.py
│   ├── sample.py
│   └── annotation.py
├── storage/
│   ├── __init__.py
│   ├── database.py
│   └── import_export.py
├── ui/
│   ├── __init__.py
│   ├── import_page.py
│   ├── annotate_page.py
│   └── analysis_page.py
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   └── test_database.py
├── data/
│   └── example_samples.csv  ← YOUR DATASET GOES HERE
├── app.py
├── pyproject.toml
└── .gitignore
```

---

**You're ready to test once you have:**
- ✅ Test dataset (CSV or JSON)
- ✅ Python 3.10+ installed
- ✅ uv installed
- ✅ Dependencies installed (`uv sync`)

Everything else will be created automatically! 🚀

