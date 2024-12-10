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

# Function to load local CSV file
def load_local_csv(file_path):
    try:
        df = pd.read_csv(file_path, parse_dates=['Date'])
        return df
    except Exception as e:
        st.error(f"Error loading CSV: {e}")
        return None

# Reset email field and hide popup
def reset():
    st.session_state.email = ""
    st.session_state.show_popup = False

# Streamlit UI
st.title("AI Content Rating Analysis")

# Load and Handle CSV Data
csv_file_path = "dataset.csv"  # Use your actual CSV file here

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
    email = st.text_input("Enter your email to receive the report", value=st.session_state.email)

    if email:
        # Increase the size and color of the Analyze button
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
            # Trigger pop-up immediately after clicking analyze
            st.session_state.show_popup = True
            
            # df_filtered_low_rating = df_filtered[df_filtered['vSp Rating'] <= 4]
            # df_filtered_high_rating = df_filtered[df_filtered['vSp Rating'] == 5]
            # results = pd.DataFrame()

            # # Batch Processing
            # BATCH_SIZE = 10
            # for start in range(0, len(df_filtered_low_rating), BATCH_SIZE):
            #     batch = df_filtered_low_rating.iloc[start:start + BATCH_SIZE]
            #     # Placeholder process_batch function call
            #     # Replace this with your business logic
            #     results = pd.concat([results, batch], ignore_index=True)

            # df_combined = pd.concat([results, df_filtered_high_rating], ignore_index=True)

            # justified_low_ratings = results[results['justification'] == 'justified']
            # correct_reviews = len(justified_low_ratings) + len(df_filtered_high_rating)

            # unjustified_reviews = results[results['justification'] == 'unjustified']
            # unjustified_reviews_count = len(unjustified_reviews) if not unjustified_reviews.empty else 0

            # # Overall summary
            # summary_data = {
            #     "Total Reviews": [len(df_filtered)],
            #     "Correct Reviews": [correct_reviews],
            #     "Unjustified Reviews": [unjustified_reviews_count],
            #     "Overrated Reviews": [len(df_combined[(df_combined['justification'].str.contains('should have been', na=False)) & (df_combined['output_rating'] < df_combined['vSp Rating'])])],
            #     "Underrated Reviews": [len(df_combined[(df_combined['justification'].str.contains('should have been', na=False)) & (df_combined['output_rating'] > df_combined['vSp Rating'])])]
            # }
            # st.write("Overall Summary")
            # st.table(pd.DataFrame(summary_data))

            # # Download results
            # st.write("Download the Analysis csv with justification and explanation")
            # output = StringIO()
            # df_combined.to_csv(output, index=False)
            # st.download_button(
            #     label="Download Results as CSV",
            #     data=output.getvalue(),
            #     file_name='analysis_results.csv',
            #     mime='text/csv',
            #     on_click=reset  # Reset upon download
            # )
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
            <button onclick="window.location.reload();" style="background-color: #4CAF50; 
            color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer;">
            OK</button>
        </div>
        """, unsafe_allow_html=True
    )
    if st.button("OK"):
        on_click=reset
