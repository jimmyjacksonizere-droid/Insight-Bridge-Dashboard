from pathlib import Path

import numpy as np
import pandas as pd


OUTPUT = Path(__file__).parent / "data" / "business_data.csv"


def generate_business_data(seed: int = 42) -> pd.DataFrame:
    """Create a reproducible demo dataset for the InsightBridge dashboard."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2024-01-01", "2026-12-01", freq="MS")
    industries = ["Retail", "Restaurant", "Healthcare", "Finance", "E-commerce"]
    regions = ["Edmonton", "Calgary"]
    rows = []

    for month_number, date in enumerate(dates):
        seasonality = 1 + 0.10 * np.sin(2 * np.pi * date.month / 12)
        growth = 1 + 0.025 * month_number
        for industry in industries:
            for region in regions:
                industry_factor = {
                    "Retail": 1.18,
                    "Restaurant": 0.92,
                    "Healthcare": 1.08,
                    "Finance": 1.24,
                    "E-commerce": 1.32,
                }[industry]
                region_factor = 1.08 if region == "Calgary" else 1.0
                customers = max(8, round(24 * growth * industry_factor * region_factor + rng.normal(0, 3)))
                avg_order = max(45, 92 * industry_factor * seasonality + rng.normal(0, 8))
                revenue = customers * avg_order * rng.uniform(2.0, 2.7)
                expenses = revenue * rng.uniform(0.54, 0.75)
                leads = max(customers, round(customers * rng.uniform(1.7, 2.6)))
                conversions = min(leads, round(leads * rng.uniform(0.28, 0.48)))
                satisfaction = float(np.clip(rng.normal(4.18, 0.24), 3.2, 5.0))
                churn_rate = float(np.clip(rng.normal(0.055, 0.018), 0.01, 0.14))
                rows.append(
                    {
                        "date": date.date().isoformat(),
                        "region": region,
                        "industry": industry,
                        "customers": customers,
                        "leads": leads,
                        "conversions": conversions,
                        "revenue": round(revenue, 2),
                        "expenses": round(expenses, 2),
                        "satisfaction": round(satisfaction, 2),
                        "churn_rate": round(churn_rate, 4),
                    }
                )
    return pd.DataFrame(rows)


if __name__ == "__main__":
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    generate_business_data().to_csv(OUTPUT, index=False)
    print(f"Created {OUTPUT}")

