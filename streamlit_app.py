import os
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st
import matplotlib.pyplot as plt

# Initialize session state for pop-up visibility
if 'show_popup' not in st.session_state:
    st.session_state.show_popup = False

# Reset parameters
def reset():
    for key in st.session_state.keys():
        st.session_state[key] = False

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

# Load and handle CSV data
csv_file_path = "dataset.csv"  # Update this to the correct file path

df = load_local_csv(csv_file_path)
if df is not None and not st.session_state.show_popup:
    df['Date'] = pd.to_datetime(df['Date'], format='%b %d %Y', errors='coerce')

    # Date selection
    start_date_input = st.date_input("Start Date", value=df['Date'].min().date())
    end_date_input = st.date_input("End Date", value=(df['Date'].min() + timedelta(days=1)).date())

    start_date = pd.to_datetime(start_date_input)
    end_date = pd.to_datetime(end_date_input)

    # Display selected date range
    st.markdown(f"**Selected Date Range:** {start_date} to {end_date}")

    # Filter DataFrame by the date range
    df_filtered = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)].copy()
    rating_counts = df_filtered['vSp Rating'].value_counts().sort_index()

    # Plot the ratings graph
    fig, ax = plt.subplots()
    bars = ax.bar(rating_counts.index, rating_counts.values, color='skyblue')
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, height, f'{height}', ha='center', va='bottom', fontsize=10)

    ax.set_xlabel('vSp Rating')
    ax.set_ylabel('Count')
    ax.set_title('vSp Rating Counts')
    st.pyplot(fig)

    # Email input
    email = st.text_input("Enter your email to receive the report")

    if email:
        if st.button("Analyze"):
            # Trigger pop-up immediately after clicking analyze
            st.session_state.show_popup = True
    else:
        st.warning("Please enter an email address to proceed.")

# Simulate the pop-up
if st.session_state.show_popup:
    st.markdown(
        """
        <div style="position: fixed; top: 20%; left: 50%; transform: translateX(-50%);
        background-color: rgba(0, 0, 0, 0.8); padding: 20px; color: white; border-radius: 10px;
        width: 80%; text-align: center; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3); z-index: 1;">
            <h3>Report Generation in Progress</h3>
            <p>We will send the report CSV to your email address once the generation is completed. 
            Meanwhile, you can generate a new report or close this page.</p>
        </div>
        """, unsafe_allow_html=True
    )
    
    # Add an 'OK' button within the Streamlit interface to reset
    if st.button("OK"):
        reset()
