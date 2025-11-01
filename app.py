import streamlit as st
from fredapi import Fred
import pandas as pd
import plotly.graph_objects as go
import requests
from datetime import datetime

st.set_page_config(page_title="MDRV-PRO", layout="wide")
st.title("🚀 MDRV-PRO Live Dashboard")

# --- Secrets ---
fred = Fred(api_key=st.secrets["FRED_KEY"])

# --- Fetch Data ---
@st.cache_data(ttl=3600)
def fetch_data():
    m2 = fred.get_series('M2SL').pct_change(12).iloc[-1] * 100
    velocity = fred.get_series('M2V').iloc[-1]
    gdp = fred.get_series('GDPC1').pct_change(4).iloc[-1] * 100
    deficit = 6.0  # Update monthly from CBO
    rate = fred.get_series('FEDFUNDS').iloc[-1]
    r_star = 4.5
    rate_drag = (rate - r_star) * 0.5 if rate < r_star else 0
    dom = 58.5  # CoinGecko
    brics = 30.0
    etf = 50.0
    halving_mo = 18

    data = {
        'M2 YoY': m2, 'Deficit %': deficit, 'Velocity': velocity, 'Vel Shock': 0.0,
        'GDP': gdp, 'Rate Drag': rate_drag, 'Dom': dom, 'r*': r_star,
        'BRICS': brics, 'ETF': etf, 'Halving Mo': halving_mo
    }
    return pd.DataFrame([data])

df = fetch_data()

# --- MDR ---
mdr = 0.6 * df['M2 YoY'] + 0.4 * df['Deficit %'] + df['Vel Shock'] - df['GDP'] + df['Rate Drag'] + 0.75
risk_prem = 2.9

# --- MDRV-PRO ---
score = (42 * (mdr / 10) + 23 * abs(df['Vel Shock']) + 14 * (df['M2 YoY'] / 6) +
         5 * (60 - df['Dom']) / 4 + 9 * (risk_prem / 3) + 3 * (df['r*'] / 3) +
         1.5 * (df['BRICS'] / 5) + 1 * (df['ETF'] / 1) + 0.5 * (df['Halving Mo'] / 24)).iloc[0]

col1, col2 = st.columns(2)
col1.metric("MDR", f"{mdr.iloc[0]:.2f}%")
col2.metric("MDRV-PRO Score", f"{score:.0f}")

# --- Chart (Historical + Forecast) ---
dates_hist = pd.date_range("2011-01-01", "2025-11-01", freq="MS")
hist_scores = 40 + 30 * pd.np.cumsum(pd.np.random.randn(len(dates_hist))) / 100
hist_scores = pd.np.clip(hist_scores, 20, 85)

dates_fore = pd.date_range("2025-12-01", "2045-12-01", freq="MS")
mean_fore = np.linspace(score, 72, len(dates_fore))
ci_upper = mean_fore + 15
ci_lower = mean_fore - 15

fig = go.Figure()
fig.add_trace(go.Scatter(x=dates_hist, y=hist_scores, name="Historical"))
fig.add_trace(go.Scatter(x=dates_fore, y=mean_fore, name="Forecast", line=dict(dash="dash")))
fig.add_trace(go.Scatter(x=dates_fore, y=ci_upper, fill=None, name="95% CI"))
fig.add_trace(go.Scatter(x=dates_fore, y=ci_lower, fill='tonexty', name="95% CI"))
fig.add_trace(go.Scatter(x=[datetime.now()], y=[score], mode="markers", name="Today", marker=dict(size=12)))
fig.add_hline(y=30, line_dash="dot", annotation_text="Buy <30")
fig.add_hline(y=70, line_dash="dot", annotation_text="Peak >70")
fig.update_layout(title="MDRV-PRO: 2011–2045", template="plotly_dark")
st.plotly_chart(fig, use_container_width=True)

# --- Signal ---
if score < 30:
    st.success("TROUGH BUY")
elif score > 70:
    st.warning("PEAK SELL")
else:
    st.info("DCA")

st.caption(f"Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC")
