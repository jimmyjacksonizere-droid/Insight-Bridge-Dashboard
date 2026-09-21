# InsightBridge AI Solutions Dashboard

A complete Streamlit dashboard for VS Code. It demonstrates the InsightBridge business concept with executive KPIs, sales analysis, customer intelligence, predictive revenue forecasting, and an investor view.

## What is included

- Executive KPIs: revenue, expenses, profit, customers, satisfaction, and churn
- Filters for date, city, and industry
- Sales and conversion analysis
- Customer satisfaction and retention-risk views
- Six-month predictive revenue forecast with an adjustable horizon
- Five-year financial projections and investor fund allocation
- CSV upload so a client can replace the included demonstration data

## Run in VS Code

1. Extract this folder and open `InsightBridge_Dashboard` in VS Code.
2. Open **Terminal > New Terminal**.
3. Create a virtual environment:

   **Windows PowerShell**

   ```powershell
   py -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

   **Windows Command Prompt**

   ```bat
   py -m venv .venv
   .venv\Scripts\activate.bat
   ```

4. Install the packages:

   ```bash
   pip install -r requirements.txt
   ```

5. Start the dashboard:

   ```bash
   streamlit run app.py
   ```

6. Open the local address shown in the terminal, usually `http://localhost:8501`.

## Use your own data

Choose **Upload a business CSV** in the sidebar. The CSV must contain these columns:

| Column | Example |
|---|---|
| `date` | `2026-09-01` |
| `region` | `Edmonton` |
| `industry` | `Retail` |
| `customers` | `42` |
| `leads` | `85` |
| `conversions` | `33` |
| `revenue` | `12500.50` |
| `expenses` | `7800.00` |
| `satisfaction` | `4.3` |
| `churn_rate` | `0.05` |

Dates that cannot be read and nonnumeric values are removed. Profit, margin, and conversion rate are calculated automatically.

## Regenerate the demo data

```bash
python generate_data.py
```

This replaces `data/business_data.csv` with a reproducible synthetic dataset. The data is for demonstration and does not represent actual InsightBridge clients.

