import os
import pandas as pd
import openai
from crewai import Agent, Task, Crew
from datetime import datetime, timedelta
import json
import streamlit as st
import matplotlib.pyplot as plt
from io import StringIO
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

# Ensure OpenAI API key is set
#openai.api_key = os.getenv('OPENAI_API_KEY', 'your_default_api_key')
#os.environ["OPENAI_MODEL_NAME"] = 'gpt-4o'
api_key = st.text_input("Enter your OpenAI API key", type="password")
openai.api_key = api_key
os.environ['OPENAI_API_KEY'] = openai.api_key
os.environ["OPENAI_MODEL_NAME"] = 'gpt-4o'

# Function to load local CSV file
def load_local_csv(file_path):
    try:
        df = pd.read_csv(file_path, parse_dates=['Date'])
        return df
    except Exception as e:
        st.error(f"Error loading CSV: {e}")
        return None

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

# Initialize session state for the pop-up visibility
if 'show_popup' not in st.session_state:
    st.session_state.show_popup = False

if "email" not in st.session_state:
    st.session_state.email = ""

# Streamlit UI
st.title("AI Content Rating Analysis")

# Define Agents
content_analyzer = Agent(
    role="Human Content Analyzer Expert",
    goal="Analyze AI-generated and user-accepted content, and determine the rating justification.",
    backstory="You are a content expert tasked with validating the ratings of AI-generated content.",
    allow_delegation=False,
    verbose=True
)

# Define Tasks
def create_analyze_content_task(review_text_present):
    description = (
        "Correctly Analyze the AI-generated content and the user-accepted content and properly utilize the data provided to determine if the rating provided is justified."
    )
    return Task(
        description=description,
        expected_output='A comprehensive analysis of the content and a rating validation.',
        agent=content_analyzer,
        config={"Rating": "int", "justification": "str", "explanation": "str"}
    )

# Define Crew
crew = Crew(
    agents=[content_analyzer],
    tasks=[],
    verbose=True,
    memory=True
)

def analyze_and_validate(row):
    ai_content = row['AI Content']
    vsp_content = row['vSp edited content']
    rating = row['vSp Rating']
    review_text = row['Review Text']
    prompt = row['Prompt']
    Agentic_learning = ""
    if not isinstance(vsp_content, str) or not vsp_content.strip():
        return rating, "unjustified", "no vsp edited content for analysis"
    
    attempts = 0
    while attempts < 10:
        inputs = {
            "ai_content": ai_content,
            "vsp_content": vsp_content,
            "rating": rating,
            "review_text": review_text,
            "prompt": prompt,
            "Agentic_learning": Agentic_learning
        }
        review_text_present = isinstance(review_text, str) and bool(review_text.strip())
        crew.tasks = [
            create_analyze_content_task(review_text_present)
        ]
        pattern = re.compile(r'should have been (\d+)')
        result = crew.kickoff(inputs=inputs)
        result_content = str(result)
        Agentic_learning += f"\n In your attempt {attempts + 1} Discrepancy detected in your response: {result_content}\n"
        try:
            start_idx = result_content.find('{')
            end_idx = result_content.find('}') + 1
            json_str = result_content[start_idx:end_idx].strip()
            output = json.loads(json_str)
            new_rating = output.get('Rating')
            justification = output.get('justification', '').lower()
            explanation = output.get('explanation')
            suggested_rating_match = pattern.search(justification)
            suggested_rating = int(suggested_rating_match.group(1)) if suggested_rating_match else None
            
            if suggested_rating is not None:
                return suggested_rating, justification, explanation
            
            if isinstance(new_rating, str):
                try:
                    new_rating = int(new_rating)
                except ValueError:
                    st.warning(f"Cannot convert new_rating '{new_rating}' to an integer. Re-analyzing...")
                    attempts += 1
                    continue
            
            if new_rating is None or justification == "" or explanation is None:
                st.warning(f"Missing fields detected for row with AI content: {ai_content}. Re-analyzing...")
                attempts += 1
                continue
            
            if new_rating != rating and justification == "justified":
                st.warning(f"Discrepancy detected in justification for row with AI content: {ai_content}. Re-analyzing...")
                attempts += 1
                continue
            
            return new_rating, justification, explanation
        
        except (json.JSONDecodeError, KeyError, TypeError):
            st.warning(f"Parsing failed or missing keys in response for AI content: {ai_content}. Retrying...")
        
        attempts += 1
    
    return rating, "NA", "Not analysed"

def process_batch(batch):
    output = batch.apply(analyze_and_validate, axis=1, result_type='expand')
    batch[['output_rating', 'justification', 'explanation']] = output
    return batch

# Load and Handle CSV Data
csv_file_path = "dataset.csv"  # Use your actual CSV file here

df = load_local_csv(csv_file_path)
if df is not None:
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

            # Simulation of analysis process
            df_filtered_low_rating = df_filtered[df_filtered['vSp Rating'] <= 4]
            df_filtered_high_rating = df_filtered[df_filtered['vSp Rating'] == 5]
            results = pd.DataFrame()

            # Batch Processing
            BATCH_SIZE = 10
            for start in range(0, len(df_filtered_low_rating), BATCH_SIZE):
                batch = df_filtered_low_rating.iloc[start:start + BATCH_SIZE]
                results = pd.concat([results, process_batch(batch)], ignore_index=True)

            df_combined = pd.concat([results, df_filtered_high_rating], ignore_index=True)

            justified_low_ratings = results[results['justification'] == 'justified']
            correct_reviews = len(justified_low_ratings) + len(df_filtered_high_rating)

            unjustified_reviews = results[results['justification'] == 'unjustified']
            unjustified_reviews_count = len(unjustified_reviews) if not unjustified_reviews.empty else 0

            # Overall Summary
            summary_data = {
                "Total Reviews": [len(df_filtered)],
                "Correct Reviews": [correct_reviews],
                "Unjustified Reviews": [unjustified_reviews_count],
                "Overrated Reviews": [len(df_combined[(df_combined['justification'].str.contains('should have been', na=False)) & (df_combined['output_rating'] < df_combined['vSp Rating'])])],
                "Underrated Reviews": [len(df_combined[(df_combined['justification'].str.contains('should have been', na=False)) & (df_combined['output_rating'] > df_combined['vSp Rating'])])]
            }
            st.write("Overall Summary")
            st.table(pd.DataFrame(summary_data))

            # Download results
            st.write("Download the Analysis csv with justification and explanation")
            output = StringIO()
            df_combined.to_csv(output, index=False)

            # Send the email with the CSV attachment
            send_email_with_attachment(email, "Your Report of AI Content Rating Analysis", 'Here is your analysis report.', attachment=output)
            
            st.download_button(
                label="Download Results as CSV",
                data=output.getvalue(),
                file_name='analysis_results.csv',
                mime='text/csv'
            )
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
            <button onclick="window.location.reload();" style="background-color: #4CAF50; color: white; padding: 10px 20px; 
            border: none; border-radius: 5px; cursor: pointer;">OK</button>
        </div>
        """, unsafe_allow_html=True
    )
