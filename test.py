import streamlit as st
import pandas as pd

# Initialize session state to keep track of the DataFrame
if "df" not in st.session_state:
    st.session_state.df = None  # Start with no DataFrame loaded

st.title("Spreadsheet Upload and Grid Display with Clear Option")

# File uploader to load the spreadsheet
uploaded_file = st.file_uploader("Upload an Excel or CSV file", type=["xlsx", "xls", "csv"])

# Placeholder for the grid display
grid_placeholder = st.empty()

# Load the DataFrame if a file is uploaded
if uploaded_file is not None:
    try:
        # Read the uploaded file into a DataFrame
        st.session_state.df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith(".xlsx") else pd.read_csv(uploaded_file)
        
        # Display DataFrame in the grid placeholder
        grid_placeholder.dataframe(st.session_state.df)
        
    except Exception as e:
        st.error(f"Error reading the spreadsheet: {e}")

# Button to clear the grid content
if st.button("Clear Grid"):
    st.session_state.df = None  # Clear the DataFrame from session state
    grid_placeholder.empty()     # Clear the placeholder content

# Display the grid only if there is data in the DataFrame
if st.session_state.df is not None:
    grid_placeholder.dataframe(st.session_state.df)
else:
    st.write("No data to display.")
