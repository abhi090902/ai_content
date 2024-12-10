import os
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st
import matplotlib.pyplot as plt

# Initialize session state for the pop-up visibility and email input
if 'show_popup' not in st.session_state:
    st.session_state.show_popup = False

if 'email' not in st.session_state:
    st.session_state.email = ''

# Function to load local CSV file
def load_local_csv(file_path):
    try:
        df = pd.read_csv(file_path, parse_dates=['Date'])
        return df
    except Exception as e:
        st.error(f"Error loading CSV: {e}")
        return None

# Streamlit UI
st.title("AI Content Rating Analysis")

# Load and Handle CSV Data
csv_file_path = "dataset.csv"  # Replace with your actual CSV file or path
df = load_local_csv(csv_file_path)

if df is not None:
    df['Date'] = pd.to_datetime(df['Date'], format='%b %d %Y', errors='coerce')
    
    # Date Selection
    start_date_input = st.date_input("Start Date", value=df['Date'].min().date())
    end_date_input = st.date_input("End Date", value=(df['Date'].max()).date())

    start_date = pd.to_datetime(start_date_input)
    end_date = pd.to_datetime(end_date_input)

    # Display selected date range
    st.markdown(f"**Selected Date Range:** {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

    # Filter DataFrame by the date range
    df_filtered = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)].copy()
    rating_counts = df_filtered['vSp Rating'].value_counts().sort_index()

    # Plot the ratings graph
    fig, ax = plt.subplots()
    bars = ax.bar(rating_counts.index, rating_counts.values, color='skyblue')
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, height, f'{int(height)}', ha='center', va='bottom', fontsize=10)

    ax.set_xlabel('vSp Rating')
    ax.set_ylabel('Count')
    ax.set_title('vSp Rating Counts')
    st.pyplot(fig)

    # Email input
    st.session_state.email = st.text_input("Enter your email to receive the report", value=st.session_state.email)
    if st.session_state.email:
        # Style for bigger Analyze button
        st.markdown(
            """
            <style>
            div.stButton > button {
                background-color: #4CAF50;  /* Green */
                color: white;
                height: 50px;
                width: 150px;  /* Bigger width */
                font-size: 18px;  /* Larger font size */
            }
            </style>
            """, unsafe_allow_html=True
        )
        analyze_button = st.button("Analyze")
        if analyze_button:
            st.session_state.show_popup = True  # Show the pop-up

# Render pop-up
if st.session_state.get('show_popup', False):
    # Using st.modal (available in Streamlit versions >= 1.22)
    with st.modal("Report Generation in Progress"):
        st.write("""
            We will send the report CSV to your email address once the generation is completed.
            Meanwhile, you can generate a new report or close this page.
        """)
        ok_button = st.button("OK")
        if ok_button:
            st.session_state.show_popup = False  # Hide the pop-up
            st.session_state.email = ''  # Reset the email input
            st.experimental_rerun()  # Rerun the app to update the UI
