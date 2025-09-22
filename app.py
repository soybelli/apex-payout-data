import os
import re
from datetime import datetime
from typing import Optional

import pandas as pd
import streamlit as st
import plotly.express as px

CSV_PATH = os.path.join(os.path.dirname(__file__), 'payouts.csv')


def parse_currency(value: str) -> Optional[float]:
    if pd.isna(value):
        return None
    s = str(value)
    s = s.replace(',', '')
    m = re.search(r"(-?\$?\s*\d+(?:\.\d+)?)", s)
    if not m:
        return None
    try:
        return float(m.group(1).replace('$', '').strip())
    except Exception:
        return None


def extract_country(location: str) -> str:
    if pd.isna(location):
        return 'Unknown'
    s = str(location)
    parts = [p.strip() for p in s.split(',') if p.strip()]
    if not parts:
        return 'Unknown'
    # Heuristic: last segment is country name or code
    last = parts[-1]
    # Normalize common patterns
    mapping = {
        'USA': 'USA', 'US': 'USA', 'U.S.A.': 'USA', 'United States': 'USA',
        'UK': 'UK', 'U.K.': 'UK', 'United Kingdom': 'UK'
    }
    if last in mapping:
        return mapping[last]
    return last


@st.cache_data(show_spinner=False)
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    # Normalize columns
    expected_cols = ['Date', 'Name', 'Location', 'Payout']
    rename_map = {}
    for col in df.columns:
        c = col.strip()
        if c.lower() == 'date':
            rename_map[col] = 'Date'
        elif c.lower() == 'name':
            rename_map[col] = 'Name'
        elif c.lower() in ('location', 'country'):
            rename_map[col] = 'Location'
        elif c.lower() in ('payout', 'amount'):
            rename_map[col] = 'Payout'
    df = df.rename(columns=rename_map)
    # Ensure columns exist
    for c in expected_cols:
        if c not in df.columns:
            df[c] = pd.NA

    # Parse date
    def parse_date(s):
        if pd.isna(s):
            return pd.NaT
        for fmt in ("%b %d, %Y", "%Y-%m-%d", "%m/%d/%Y"):
            try:
                return datetime.strptime(str(s), fmt)
            except Exception:
                continue
        return pd.NaT

    df['Date'] = df['Date'].apply(parse_date)
    df['YearMonth'] = df['Date'].dt.to_period('M').astype(str)

    # Clean payout
    df['PayoutValue'] = df['Payout'].apply(parse_currency)

    # Country
    df['Country'] = df['Location'].apply(extract_country)

    # Drop rows without amount or date
    df = df.dropna(subset=['PayoutValue', 'Date'])
    return df


def main():
    st.set_page_config(page_title="Apex Payouts Analytics", layout="wide")
    st.title("Apex Payouts Analytics")
    st.caption("Interactive analysis of payouts by country and month")

    if not os.path.exists(CSV_PATH):
        st.error(f"CSV not found at {CSV_PATH}")
        st.stop()

    df = load_data(CSV_PATH)

    # Sidebar filters
    st.sidebar.header("Filters")
    years = sorted({d.year for d in df['Date'].dropna()})
    year_filter = st.sidebar.multiselect("Year", years, default=years)
    if year_filter:
        df = df[df['Date'].dt.year.isin(year_filter)]

    # Key metrics
    total_payout = df['PayoutValue'].sum()
    total_records = len(df)
    st.metric("Total Payout", f"${total_payout:,.0f}")
    st.metric("Total Records", f"{total_records:,}")

    # Tabs
    tab1, tab2 = st.tabs(["Payout by Country", "Payout by Month"])

    with tab1:
        st.subheader("Payout by Country")
        country_agg = df.groupby('Country', as_index=False)['PayoutValue'].sum().sort_values('PayoutValue', ascending=False)
        st.dataframe(country_agg, use_container_width=True)
        fig = px.bar(country_agg.head(25), x='Country', y='PayoutValue', title='Top Countries by Total Payout', labels={'PayoutValue': 'Payout ($)'})
        fig.update_layout(xaxis={'categoryorder': 'total descending'})
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Payout by Month")
        month_agg = df.groupby('YearMonth', as_index=False)['PayoutValue'].sum().sort_values('YearMonth')
        st.dataframe(month_agg, use_container_width=True)
        fig2 = px.line(month_agg, x='YearMonth', y='PayoutValue', markers=True, title='Total Payout by Month', labels={'PayoutValue': 'Payout ($)'})
        st.plotly_chart(fig2, use_container_width=True)

    with st.expander("Raw Data"):
        st.dataframe(df[['Date', 'Name', 'Location', 'Payout', 'PayoutValue', 'Country']].sort_values('Date', ascending=False), use_container_width=True)


if __name__ == '__main__':
    main()


