# 🧹 Data Cleaner

Upload a messy CSV or Excel file and get back a clean, analysis-ready table, along with a report of every change made.

Built with **Python, pandas and Streamlit**.

## What it cleans

| Problem in raw data | What the app does |
|---|---|
| Column names like `Transaction Date ` | Converts to `transaction_date` |
| Extra spaces and mixed capitals | Trims spaces, optionally standardises case |
| Dates stored as text (`05-10-2026`) | Converts to real dates (day-first, Indian format) |
| Amounts like `₹1,211.50` or `(500)` | Converts to numbers (`1211.5`, `-500`) |
| Duplicate rows | Removes them (optional) |
| Completely empty rows | Removes them |
| Missing values | Counted per column so you can see what's left |

## Features

- Upload **CSV or Excel** files, with automatic encoding detection
- **Before & after** comparison of the original and cleaned data
- **Column details** showing type and missing-value count for every column
- **"What changed"** report listing each fix
- One-click **download of the cleaned CSV** (opens correctly in Excel, including ₹)
- A built-in **sample file** to try the app immediately

## Run it on your computer

1. Install Python 3.10 or newer, and install Anaconda if you don't have it.
2. Open **Anaconda Prompt**, go to the project folder, and install the requirements:

   ```
   cd path\to\data-cleaner
   pip install -r requirements.txt
   ```

3. Start the app:

   ```
   streamlit run app.py
   ```

4. Your browser opens at `http://localhost:8501`. Upload a file or click **Try sample data**.

## Project structure

```
data-cleaner/
├── app.py                  # Streamlit web interface
├── cleaner.py              # Cleaning engine (pure pandas, no UI code)
├── sample_messy_data.csv   # Sample file to try the app
├── requirements.txt        # Libraries to install
└── README.md
```

The cleaning logic lives in `cleaner.py` and does not depend on Streamlit, so you can also use it from a script or notebook:

```python
import pandas as pd
from cleaner import clean_dataset

raw = pd.read_csv("sample_messy_data.csv")
clean, report = clean_dataset(raw, text_case="title")
print(report["changes"])
```

## How it decides what a column is

- A column is treated as a **date** if its name contains `date` or `time`.
- A text column is treated as a **number** only if at least 80% of its values look numeric. This prevents a column like `description` from being broken by a few numbers.
- Values that can't be converted become **missing** rather than causing an error.

These are rules of thumb. They work well for typical bank, sales and marks data, but an unusual file may need a different rule.

## Privacy

Files are processed in memory on the machine running the app and are not saved or uploaded anywhere. For financial data, run the app locally rather than on a public server.

## Limitations and next steps

- Date detection relies on column names. A date column called `when` would not be converted.
- Categories, such as grouping "Swiggy" and "Zomato" as food, are not created. That could be a next feature.
- Ideas for extension: custom rules per column, saving cleaning settings, and support for more file formats.
