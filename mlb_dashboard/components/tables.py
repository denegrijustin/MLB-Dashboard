from __future__ import annotations

import pandas as pd
import streamlit as st


STOPLIGHT_STYLE = {
    "🟢": "background-color: rgba(34, 197, 94, 0.18); color: #166534; font-weight: 700; text-align: center;",
    "🟡": "background-color: rgba(245, 158, 11, 0.20); color: #92400e; font-weight: 700; text-align: center;",
    "🔴": "background-color: rgba(239, 68, 68, 0.18); color: #991b1b; font-weight: 700; text-align: center;",
}


def _style_stoplights(df: pd.DataFrame):
    stoplight_cols = [
        col
        for col in df.columns
        if "trend" in str(col).lower() or str(col).lower() in {"signal", "status"}
    ]
    if not stoplight_cols:
        return df

    styled = df.style
    for col in stoplight_cols:
        styled = styled.map(lambda v: STOPLIGHT_STYLE.get(v, ""), subset=[col])
    return styled


def show_table(df: pd.DataFrame, use_container_width: bool = True, height: int | None = None):
    if df is None or df.empty:
        st.info("No data available for this section.")
        return

    display_df = df.copy()
    styled = _style_stoplights(display_df)
    st.dataframe(styled, use_container_width=use_container_width, hide_index=True, height=height)
