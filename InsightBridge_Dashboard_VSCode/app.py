from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sklearn.linear_model import LinearRegression


APP_DIR = Path(__file__).parent
DEFAULT_DATA = APP_DIR / "data" / "business_data.csv"
BRAND_BLUE = "#2563EB"
BRAND_TEAL = "#14B8A6"
BRAND_PURPLE = "#7C3AED"

st.set_page_config(
    page_title="InsightBridge AI Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp { background: #F7F9FC; }
    [data-testid="stSidebar"] { background: #0F172A; }
    [data-testid="stSidebar"] * { color: #F8FAFC; }
    div[data-testid="stMetric"] {
        background: white; border: 1px solid #E2E8F0; border-radius: 14px;
        padding: 16px 18px; box-shadow: 0 3px 14px rgba(15,23,42,.05);
    }
    div[data-testid="stMetricValue"] { color: #0F172A; }
    .hero {
        padding: 24px 28px; border-radius: 18px; color: white;
        background: linear-gradient(115deg, #0F172A 0%, #1D4ED8 62%, #14B8A6 100%);
        margin-bottom: 18px;
    }
    .hero h1 { margin: 0; font-size: 2rem; }
    .hero p { margin: 8px 0 0 0; color: #DBEAFE; }
    .insight {
        background: #ECFDF5; border-left: 5px solid #14B8A6; color: #134E4A;
        padding: 14px 16px; border-radius: 8px; margin: 8px 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_data(uploaded_file=None) -> pd.DataFrame:
    source = uploaded_file if uploaded_file is not None else DEFAULT_DATA
    df = pd.read_csv(source)
    required = {
        "date", "region", "industry", "customers", "leads", "conversions",
        "revenue", "expenses", "satisfaction", "churn_rate",
    }
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {', '.join(sorted(missing))}")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    numeric = list(required - {"date", "region", "industry"})
    df[numeric] = df[numeric].apply(pd.to_numeric, errors="coerce")
    df = df.dropna(subset=["date", "region", "industry", *numeric])
    df["profit"] = df["revenue"] - df["expenses"]
    df["margin"] = np.where(df["revenue"] > 0, df["profit"] / df["revenue"], 0)
    df["conversion_rate"] = np.where(df["leads"] > 0, df["conversions"] / df["leads"], 0)
    return df.sort_values("date")


def money(value: float) -> str:
    return f"${value:,.0f}"


def delta_pct(current: float, previous: float) -> str:
    if previous == 0 or pd.isna(previous):
        return "N/A"
    return f"{(current / previous - 1) * 100:+.1f}%"


def metric_delta(df: pd.DataFrame, column: str) -> str:
    monthly = df.groupby("date", as_index=False)[column].sum().sort_values("date")
    if len(monthly) < 2:
        return "N/A"
    return delta_pct(monthly.iloc[-1][column], monthly.iloc[-2][column])


def forecast_monthly(df: pd.DataFrame, periods: int = 6) -> pd.DataFrame:
    monthly = df.groupby("date", as_index=False)["revenue"].sum().sort_values("date")
    x = np.arange(len(monthly)).reshape(-1, 1)
    model = LinearRegression().fit(x, monthly["revenue"])
    future_x = np.arange(len(monthly), len(monthly) + periods).reshape(-1, 1)
    future_dates = pd.date_range(monthly["date"].max() + pd.offsets.MonthBegin(1), periods=periods, freq="MS")
    prediction = np.maximum(model.predict(future_x), 0)
    return pd.DataFrame({"date": future_dates, "revenue": prediction, "type": "Forecast"})


def render_overview(df: pd.DataFrame) -> None:
    revenue = df["revenue"].sum()
    profit = df["profit"].sum()
    customers = int(df["customers"].sum())
    avg_satisfaction = df["satisfaction"].mean()
    cols = st.columns(4)
    cols[0].metric("Total Revenue", money(revenue), metric_delta(df, "revenue"))
    cols[1].metric("Total Profit", money(profit), metric_delta(df, "profit"))
    cols[2].metric("Customer Activity", f"{customers:,}", metric_delta(df, "customers"))
    cols[3].metric("Satisfaction", f"{avg_satisfaction:.2f}/5", f"{df['churn_rate'].mean():.1%} churn")

    monthly = df.groupby("date", as_index=False).agg(revenue=("revenue", "sum"), expenses=("expenses", "sum"))
    monthly_long = monthly.melt("date", var_name="Measure", value_name="Amount")
    left, right = st.columns([1.65, 1])
    with left:
        st.subheader("Revenue and expense trend")
        fig = px.line(monthly_long, x="date", y="Amount", color="Measure", markers=True,
                      color_discrete_map={"revenue": BRAND_BLUE, "expenses": "#F97316"})
        fig.update_layout(legend_title="", hovermode="x unified", yaxis_tickprefix="$", yaxis_tickformat=",")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        st.subheader("Revenue by industry")
        industry = df.groupby("industry", as_index=False)["revenue"].sum().sort_values("revenue")
        fig = px.bar(industry, x="revenue", y="industry", orientation="h", color="revenue",
                     color_continuous_scale=["#BFDBFE", BRAND_BLUE])
        fig.update_layout(coloraxis_showscale=False, xaxis_tickprefix="$", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

    best = df.groupby("industry")["profit"].sum().idxmax()
    margin = profit / revenue if revenue else 0
    st.markdown(
        f'<div class="insight"><b>AI insight:</b> {best} is the strongest profit contributor. '
        f'The selected business segment is operating at a {margin:.1%} profit margin.</div>',
        unsafe_allow_html=True,
    )


def render_sales(df: pd.DataFrame) -> None:
    st.subheader("Sales performance")
    industry = df.groupby("industry", as_index=False).agg(
        Revenue=("revenue", "sum"), Profit=("profit", "sum"),
        Leads=("leads", "sum"), Conversions=("conversions", "sum"),
    )
    industry["Conversion Rate"] = industry["Conversions"] / industry["Leads"]
    left, right = st.columns(2)
    with left:
        fig = px.scatter(industry, x="Revenue", y="Profit", size="Conversions", color="industry",
                         hover_name="industry", size_max=55)
        fig.update_layout(xaxis_tickprefix="$", yaxis_tickprefix="$", legend_title="Industry")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        fig = px.bar(industry.sort_values("Conversion Rate"), x="Conversion Rate", y="industry",
                     orientation="h", color="Conversion Rate", color_continuous_scale="Teal")
        fig.update_layout(coloraxis_showscale=False, xaxis_tickformat=".0%", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)
    display = industry.copy()
    display["Revenue"] = display["Revenue"].map(money)
    display["Profit"] = display["Profit"].map(money)
    display["Conversion Rate"] = display["Conversion Rate"].map(lambda x: f"{x:.1%}")
    st.dataframe(display, use_container_width=True, hide_index=True)


def render_customers(df: pd.DataFrame) -> None:
    st.subheader("Customer intelligence")
    summary = df.groupby(["region", "industry"], as_index=False).agg(
        Customers=("customers", "sum"), Satisfaction=("satisfaction", "mean"),
        Churn=("churn_rate", "mean"), Revenue=("revenue", "sum"),
    )
    left, right = st.columns(2)
    with left:
        fig = px.sunburst(summary, path=["region", "industry"], values="Customers", color="Satisfaction",
                          color_continuous_scale="Blues", range_color=(3.5, 5))
        st.plotly_chart(fig, use_container_width=True)
    with right:
        fig = px.scatter(summary, x="Satisfaction", y="Churn", size="Customers", color="industry",
                         hover_data=["region", "Revenue"], size_max=48)
        fig.update_layout(yaxis_tickformat=".1%", legend_title="Industry")
        st.plotly_chart(fig, use_container_width=True)
    risk = summary.sort_values(["Churn", "Satisfaction"], ascending=[False, True]).iloc[0]
    st.markdown(
        f'<div class="insight"><b>Retention alert:</b> Prioritize {risk["industry"]} customers in '
        f'{risk["region"]}; this segment has the highest selected churn rate at {risk["Churn"]:.1%}.</div>',
        unsafe_allow_html=True,
    )


def render_forecast(df: pd.DataFrame) -> None:
    st.subheader("Predictive revenue forecast")
    months = st.slider("Forecast horizon in months", 3, 12, 6)
    actual = df.groupby("date", as_index=False)["revenue"].sum()
    actual["type"] = "Actual"
    future = forecast_monthly(df, months)
    combined = pd.concat([actual.tail(18), future], ignore_index=True)
    fig = px.line(combined, x="date", y="revenue", color="type", markers=True,
                  color_discrete_map={"Actual": BRAND_BLUE, "Forecast": BRAND_TEAL})
    fig.add_vline(x=actual["date"].max().timestamp() * 1000, line_dash="dash", line_color="#64748B")
    fig.update_layout(hovermode="x unified", yaxis_tickprefix="$", legend_title="")
    st.plotly_chart(fig, use_container_width=True)
    projected = future["revenue"].sum()
    baseline = actual.tail(months)["revenue"].sum()
    st.metric(f"Projected revenue over next {months} months", money(projected), delta_pct(projected, baseline))
    st.caption("Forecast uses a simple linear trend model and is intended for planning, not a guarantee.")


def render_investor() -> None:
    st.subheader("Five-year business projection")
    plan = pd.DataFrame({
        "Year": ["Year 1", "Year 2", "Year 3", "Year 4", "Year 5"],
        "Customers": [50, 120, 300, 800, 1000],
        "Revenue": [110000, 264000, 660000, 1760000, 2200000],
        "Expenses": [135000, 200000, 350000, 600000, 900000],
    })
    plan["Profit"] = plan["Revenue"] - plan["Expenses"]
    long = plan.melt("Year", value_vars=["Revenue", "Expenses", "Profit"], var_name="Measure", value_name="Amount")
    fig = px.bar(long, x="Year", y="Amount", color="Measure", barmode="group",
                 color_discrete_map={"Revenue": BRAND_BLUE, "Expenses": "#F97316", "Profit": BRAND_TEAL})
    fig.update_layout(yaxis_tickprefix="$", yaxis_tickformat=",", legend_title="")
    st.plotly_chart(fig, use_container_width=True)
    a, b, c = st.columns(3)
    a.metric("Investment Ask", "$250,000", "15% equity")
    b.metric("Year 5 Revenue", "$2.2M", "+1,900% vs Year 1")
    c.metric("Year 5 Profit", "$1.3M", "59.1% margin")
    st.markdown("#### Planned use of funds")
    allocation = pd.DataFrame({"Category": ["Product development", "Marketing", "Staff salaries", "Operations"], "Share": [40, 30, 20, 10]})
    fig = px.pie(allocation, names="Category", values="Share", hole=.58,
                 color_discrete_sequence=[BRAND_BLUE, BRAND_TEAL, BRAND_PURPLE, "#F97316"])
    fig.update_traces(textinfo="percent+label")
    st.plotly_chart(fig, use_container_width=True)


with st.sidebar:
    st.markdown("## ◈ InsightBridge")
    st.caption("AI-powered business intelligence")
    uploaded = st.file_uploader("Upload a business CSV", type="csv")

try:
    data = load_data(uploaded)
except Exception as error:
    st.error(f"The data could not be loaded. {error}")
    st.stop()

with st.sidebar:
    min_date, max_date = data["date"].min().date(), data["date"].max().date()
    date_range = st.date_input("Date range", (min_date, max_date), min_value=min_date, max_value=max_date)
    regions = st.multiselect("Region", sorted(data["region"].unique()), default=sorted(data["region"].unique()))
    industries = st.multiselect("Industry", sorted(data["industry"].unique()), default=sorted(data["industry"].unique()))
    st.divider()
    st.caption("Built for Canadian small and medium businesses")

start, end = (date_range if len(date_range) == 2 else (min_date, max_date))
filtered = data[
    data["date"].dt.date.between(start, end)
    & data["region"].isin(regions)
    & data["industry"].isin(industries)
]

st.markdown(
    """<div class="hero"><h1>Business Intelligence Dashboard</h1>
    <p>Clear performance insights, customer intelligence, and predictive analytics for better decisions.</p></div>""",
    unsafe_allow_html=True,
)

if filtered.empty:
    st.warning("No records match the selected filters. Adjust the sidebar selections.")
    st.stop()

tabs = st.tabs(["Executive Overview", "Sales", "Customers", "AI Forecast", "Investor View"])
with tabs[0]:
    render_overview(filtered)
with tabs[1]:
    render_sales(filtered)
with tabs[2]:
    render_customers(filtered)
with tabs[3]:
    render_forecast(filtered)
with tabs[4]:
    render_investor()

st.divider()
st.caption("InsightBridge AI Solutions • Demo dashboard • Data refreshes when a new CSV is uploaded")

