from __future__ import annotations

from decimal import Decimal

import pandas as pd
import streamlit as st
from pandas.api.types import (
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
)
from st_aggrid import AgGrid


def sanitize_for_grid(df: pd.DataFrame) -> pd.DataFrame:
    safe_df = df.copy()

    for column in safe_df.columns:
        series = safe_df[column]

        if is_datetime64_any_dtype(series):
            safe_df[column] = series.dt.strftime("%Y-%m-%d %H:%M:%S").where(
                series.notna(), None
            )
            continue

        if is_numeric_dtype(series):
            continue

        if is_object_dtype(series):
            safe_df[column] = series.map(_normalize_object_value)

    return safe_df


def render_aggrid(df: pd.DataFrame, *, fallback_label: str = "table", **kwargs):
    safe_df = sanitize_for_grid(df)

    try:
        return AgGrid(safe_df, **kwargs)
    except Exception as exc:
        st.warning(
            f"Interactive grid unavailable for {fallback_label}. Showing a standard table instead."
        )
        st.caption(f"AgGrid error: {exc}")
        st.dataframe(safe_df, use_container_width=True)
        return None


def _normalize_object_value(value):
    if pd.isna(value):
        return None

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, (pd.Timestamp,)):
        return value.strftime("%Y-%m-%d %H:%M:%S")

    return value
