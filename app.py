import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="AI-Intel Dashboard", layout="wide")

@st.cache_data
def load_data(path: str) -> pd.DataFrame:
  df = pd.read_csv(path)
  # Pokus o rozumné parsovanie dátumu, ak existuje stĺpec s názvom podobným 'date'
  date_cols = [c for c in df.columns if c.lower() in ["date", "dt", "timestamp"]]
  if date_cols:
    for c in date_cols:
      with pd.option_context("mode.chained_assignment", None):
        df[c] = pd.to_datetime(df[c], errors="coerce")
  return df

CSV_PATH = "ai_search_tools_latest_clean.csv"
df = load_data(CSV_PATH)

st.title("AI Search Intelligence Dashboard")
st.caption("Dataset: ai_search_tools_latest_clean.csv")

# Základné rozhranie – adaptívne podľa dostupných stĺpcov
cols = {c.lower(): c for c in df.columns}

# Filtre
# Tool filter
tool_col = None
for cand in ["tool", "model", "engine", "provider", "source"]:
  if cand in cols:
    tool_col = cols[cand]
    break
tools = sorted(df[tool_col].dropna().unique()) if tool_col else []
selected_tools = st.sidebar.multiselect("Filter by Tool", tools, default=tools[:5] if tools else None)

# Date filter
date_col = None
for cand in ["date", "dt", "timestamp"]:
  if cand in cols and pd.api.types.is_datetime64_any_dtype(df[cols[cand]]):
    date_col = cols[cand]
    break

fdf = df.copy()
if tool_col and selected_tools:
  fdf = fdf[fdf[tool_col].isin(selected_tools)]

if date_col:
  min_d, max_d = fdf[date_col].min(), fdf[date_col].max()
  if pd.notna(min_d) and pd.notna(max_d):
    start, end = st.sidebar.slider(
      "Date range", min_value=min_d.to_pydatetime(), max_value=max_d.to_pydatetime(),
      value=(min_d.to_pydatetime(), max_d.to_pydatetime())
    )
    fdf = fdf[(fdf[date_col] >= pd.Timestamp(start)) & (fdf[date_col] <= pd.Timestamp(end))]

# Metry
c1, c2, c3 = st.columns(3)
c1.metric("Rows", f"{len(fdf):,}")
if tool_col:
  c2.metric("Tools", f"{fdf[tool_col].nunique():,}")

# Candidate numeric cols for metrics/plots
num_cols = [c for c in fdf.columns if pd.api.types.is_numeric_dtype(fdf[c])]

# Časový graf
if date_col and num_cols:
  y_col = st.sidebar.selectbox("Y for time series", options=num_cols)
  color_col = tool_col if tool_col else None
  ts = fdf.dropna(subset=[date_col, y_col])
  if not ts.empty:
    fig = px.line(ts.sort_values(date_col), x=date_col, y=y_col, color=color_col, title=f"{y_col} over time")
    st.plotly_chart(fig, use_container_width=True)

# Bar graf podľa kategórie (region/segment)
cat_col = None
for cand in ["region", "country", "segment", "category"]:
  if cand in cols:
    cat_col = cols[cand]
    break
if cat_col and num_cols:
  y_bar = st.sidebar.selectbox("Y for category bar", options=num_cols, index=min(1, len(num_cols)-1))
  agg = fdf.groupby(cat_col, dropna=False)[y_bar].sum().reset_index().sort_values(y_bar, ascending=False)
  if not agg.empty:
    fig_bar = px.bar(agg, x=cat_col, y=y_bar, title=f"{y_bar} by {cat_col}")
    st.plotly_chart(fig_bar, use_container_width=True)

# Tabuľka
st.subheader("Preview")
st.dataframe(fdf.head(100))

