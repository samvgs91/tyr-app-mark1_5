import pandas as pd
import streamlit as st


def ensure_drill_state(state_key: str) -> None:
    """Initialize the drill-down session state container if it is missing."""
    if state_key not in st.session_state:
        st.session_state[state_key] = {}


def clear_selector_state(drill_columns: list[tuple[str, str]], widget_prefix: str) -> None:
    """Clear selector widget state for each drill level."""
    for column, _ in drill_columns:
        st.session_state.pop(f"{widget_prefix}_{column}_selector", None)


def reset_from_level(
    level_index: int,
    state_key: str,
    drill_columns: list[tuple[str, str]],
    widget_prefix: str,
) -> None:
    """Remove the current drill level and any deeper selections."""
    level_keys = [column for column, _ in drill_columns]
    for key in level_keys[level_index:]:
        st.session_state[state_key].pop(key, None)
    clear_selector_state(drill_columns, widget_prefix)


def sanitize_drill_filters(
    df: pd.DataFrame,
    available_drill_columns: list[tuple[str, str]],
    state_key: str,
    widget_prefix: str,
) -> None:
    """Reset the drill path if any selected value no longer exists in the dataframe."""
    changed = False
    for index, (column, _) in enumerate(available_drill_columns):
        selected = st.session_state[state_key].get(column)
        if selected is None:
            continue
        valid_values = df[column].dropna().unique().tolist()
        if selected not in valid_values:
            reset_from_level(index, state_key, available_drill_columns, widget_prefix)
            changed = True
            break
    if changed:
        st.rerun()


def filter_by_drill_path(
    df: pd.DataFrame,
    available_drill_columns: list[tuple[str, str]],
    state_key: str,
) -> pd.DataFrame:
    """Filter a dataframe using the current drill selections stored in session state."""
    view = df.copy()
    for column, _ in available_drill_columns:
        selected = st.session_state[state_key].get(column)
        if selected is not None:
            view = view[view[column] == selected]
    return view


def get_active_level(
    available_drill_columns: list[tuple[str, str]],
    state_key: str,
) -> tuple[int, str, str]:
    """Return the first unselected drill level, or the deepest level if fully selected."""
    active_level_index = 0
    for index, (column, _) in enumerate(available_drill_columns):
        if st.session_state[state_key].get(column) is None:
            active_level_index = index
            break
        active_level_index = min(index + 1, len(available_drill_columns) - 1)

    current_level_column, current_level_label = available_drill_columns[active_level_index]
    return active_level_index, current_level_column, current_level_label


def aggregate_level(df: pd.DataFrame, level_column: str, value_column: str) -> pd.DataFrame:
    """Aggregate the visible dataframe for the current drill level pie chart."""
    pie_df = df[df[level_column].notna()].copy()
    if pie_df.empty:
        return pd.DataFrame(columns=[level_column, value_column])

    pie_df = (
        pie_df.groupby(level_column, as_index=False)[value_column]
        .sum()
        .sort_values(value_column, ascending=False)
    )
    total_value = pie_df[value_column].sum()
    pie_df["share"] = pie_df[value_column] / total_value if total_value else 0
    return pie_df
