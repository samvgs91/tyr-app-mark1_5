import pandas as pd
import streamlit as st


def append_total_row(df: pd.DataFrame, total_row: dict) -> pd.DataFrame:
    """Return a dataframe with an extra total row appended at the end."""
    total_df = pd.DataFrame([total_row])
    return pd.concat([df, total_df], ignore_index=True)


def build_column_config(df: pd.DataFrame) -> dict:
    """Build Streamlit number formatting config for numeric dataframe columns."""
    column_config = {}
    for column in df.columns:
        if pd.api.types.is_numeric_dtype(df[column]):
            column_config[column] = st.column_config.NumberColumn(
                column,
                format="%.2f",
            )
    return column_config


def render_table(df: pd.DataFrame, height: int = 450) -> None:
    """Render a dataframe using the app's standard wide numeric table styling."""
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        height=height,
        column_config=build_column_config(df),
    )
