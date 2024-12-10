import os
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st
import matplotlib.pyplot as plt
from io import StringIO

# Initialize session state for the pop-up visibility
if 'show_popup' not in st.session_state:
    st.session_state.show_popup = False

if "email" not in st.session_state:
    st.session_state.email = ""

if "reset" not in st.session_state:
    st.session_state.reset = False

# Function to load local CSV file
def load_local_csv(file_path):
    try:
        df = pd.read_csv(file_path, parse_dates=['Date'])
        return df
    except Exception as e:
        st.error(f"Error loading CSV: {e}")
        return None

# Function to send email with CSV attachment and text summary (just a placeholder here)
def send_email_with_attachment(to_email, subject, body, attachment=None):
    # Placeholder for email sending logic
    pass

# Streamlit UI
st.title("AI Content Rating Analysis")

# Load and Handle CSV Data
csv_file_path = "dataset.csv"  # Use your actual CSV file here

df = load_local_csv(csv_file_path)
if df is not None and not st.session_state.reset:
    df['Date'] = pd.to_datetime(df['Date'], format='%b %d %Y', errors='coerce')

    # Date Selection
    start_date_input = st.date_input("Start Date", value=df['Date'].min().date())
    end_date_input = st.date_input("End Date", value=(df['Date'].min() + timedelta(days=1)).date())
    
    # Convert to datetime64[ns] type
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
            st.session_state.reset = False
    else:
        st.warning("Please enter an email address to proceed.")

# Simulate the pop-up
if st.session_state.show_popup:
    if st.button("OK to Reset") and st.session_state.show_popup:
        # Reset the session state
        for key in st.session_state.keys():
            st.session_state[key] = False
    else:
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
