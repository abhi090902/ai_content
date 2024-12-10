import os
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st
import matplotlib.pyplot as plt

# Initialize session state for the pop-up visibility
if 'show_popup' not in st.session_state:
    st.session_state.show_popup = False

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
csv_file_path = "dataset.csv"  # Replace with your actual CSV file
df = load_local_csv(csv_file_path)

if df is not None:
    df['Date'] = pd.to_datetime(df['Date'], format='%b %d %Y', errors='coerce')

    # Date Selection
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
        analyze_button = st.button("Analyze")
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

        if analyze_button:
            st.session_state.show_popup = True  # Show the pop-up

# Render pop-up
if st.session_state.show_popup:
    st.markdown(
        """
        <div id="popup" style="position: fixed; top: 20%; left: 50%; transform: translateX(-50%);
        background-color: rgba(0, 0, 0, 0.8); padding: 20px; color: white; border-radius: 10px;
        width: 80%; text-align: center; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3); z-index: 1;">
            <h3>Report Generation in Progress</h3>
            <p>We will send the report CSV to your email address once the generation is completed. 
            Meanwhile, you can generate a new report or close this page.</p>
            <button id="ok-button" style="background-color: #4CAF50; 
            color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer;">
            OK</button>
        </div>
        <script>
        document.getElementById("ok-button").onclick = function() {
            const popup = document.getElementById("popup");
            popup.style.display = "none";
            fetch('/streamlit/run-component', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 'show_popup': false })
            });
        };
        </script>
        """, unsafe_allow_html=True
    )
