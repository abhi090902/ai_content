import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from io import StringIO
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime, timedelta

# Function to load local CSV file
def load_local_csv(file_path):
    return pd.read_csv(file_path)

# Function to send email with CSV attachment and text summary
def send_email_with_attachment(to_email, subject, body, attachment=None):
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = 'your_email@example.com'
    msg['To'] = to_email

    # Attach the message body
    msg.attach(MIMEText(body, 'plain'))

    # Attach the file
    if attachment:
        mime_app = MIMEApplication(attachment.getvalue(), 'csv')
        mime_app.add_header('Content-Disposition', 'attachment', filename="analysis_results.csv")
        msg.attach(mime_app)

    # Set up the server
    server = smtplib.SMTP('smtp.example.com', 587)
    server.starttls()
    server.login('your_email@example.com', 'your_password')
    
    # Send the email
    server.sendmail(msg['From'], to_email, msg.as_string())
    server.quit()

# Streamlit UI
st.title("AI Content Rating Analysis")

# Load CSV file
csv_file_path = "dataset.csv"  # Use your actual CSV file here
df = pd.read_csv(csv_file_path)
df['Date'] = pd.to_datetime(df['Date'], format='%b %d %Y')

# Date Selection
start_date = st.date_input("Start Date", value=df['Date'].min())
end_date = st.date_input("End Date", value=df['Date'].min() + timedelta(days=1))  # default to one day range

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

# Email input and Analyze button
email = st.text_input("Enter your email to receive the report")

if email:
    analyze_button = st.button("Analyze")
else:
    analyze_button = st.button("Analyze", disabled=True)

# Style Analyze button - Green and Larger
st.markdown("""
    <style>
    div.stButton > button {
        background-color: #4CAF50;  /* Green */
        color: white;
        height: 40px;
        width: 100px;
        font-size: 15px;
    }
    </style>""", unsafe_allow_html=True)

if analyze_button and email:
    # Display popup information (cannot be closed directly in Streamlit, so leveraged info message)
    st.info("""
    ## Report Generation in Progress.

    We will send the report CSV to your email address once generation is completed. Meanwhile, you can generate a new report or close this page.
    """)
    
    # Simulate the processing and email sending logic
    df_filtered_low_rating = df_filtered[df_filtered['vSp Rating'] <= 4]
    df_filtered_high_rating = df_filtered[df_filtered['vSp Rating'] == 5]
    results = pd.DataFrame()

    BATCH_SIZE = 10
    for start in range(0, len(df_filtered_low_rating), BATCH_SIZE):
        batch = df_filtered_low_rating.iloc[start:start + BATCH_SIZE]
        # Here you would call your existing process_batch function
        results = pd.concat([results, batch], ignore_index=True)

    # Combine only the date-filtered high ratings
    df_combined = pd.concat([results, df_filtered_high_rating], ignore_index=True)

    # Prepare the summary data
    summary_data = {
        "Total Reviews": [len(df_filtered)],
        "Correct Reviews": [0],  # Placeholder for logic
        "Unjustified Reviews": [0],  # Placeholder for logic
        "Overrated Reviews": [0],  # Placeholder for logic
        "Underrated Reviews": [0],  # Placeholder for logic
    }
    summary_text = pd.DataFrame(summary_data).to_string(index=False)

    # Prepare email with CSV attachment
    output = StringIO()
    df_combined.to_csv(output, index=False)
    send_email_with_attachment(email, "Your Report of AI Content Rating Analysis", summary_text, attachment=output)
