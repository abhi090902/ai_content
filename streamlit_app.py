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

# Streamlit UI
st.title("AI Content Rating Analysis")

# OpenAI API Key
api_key = st.text_input("Enter your OpenAI API key", type="password")

if api_key:
    openai.api_key = api_key
    os.environ['OPENAI_API_KEY'] = openai.api_key
    os.environ["OPENAI_MODEL_NAME"] = 'gpt-4o'

    # Define Agents
    content_analyzer = Agent(
    role="Human Content Analyzer Expert",
    goal="Analyze AI-generated and user-accepted content, and determine the rating justification.",
    backstory="You are a content expert tasked with validating the ratings of the AI-generated content which are rated by the user. The user checked the AI-generated content and made changes to arrive at the user-accepted content. The rating is based on how much time (amount of changes done or a nornal human to edit) the user took to arrive at the user-generated content from the AI content.",
    allow_delegation=False,
    verbose=True
    )
    # Define Tasks
    def create_analyze_content_task(review_text_present):
        if review_text_present:
            description = (
                "Correctly Analyze the AI-generated content and the user-accepted content and properly utlize the data provided to determine if the rating provided is justified. Follow these guidelines:"
                "Check if the rating is justified or weather a new rating is needed to be provided based on the percaentage change between AI generated content and user accepted content. Do not hallucinate.\n"
                "DATA:"
                "AI-generated content: {ai_content}\n"
                "User-accepted content: {vsp_content}\n"
                "Rating: {rating}\n"
                "Review Text: {review_text}\n"
                "First Priority: Instructions"
                "Strictly ensure that if the review text contains 2 or fewer complete sentences, where a complete sentence is defined as a portion of text ending with a single full stop (.), and **not a comma (,)**, and the provided rating is 2 or 3, the output should be 'Justified'."
                "Only For Eadge cases where if the review text has very short and is of only one or two words and the Rating is given as 1 then and only then provide justification as Justified"
                "Second Priority:Time Based Instructions"
                "Carry the analysis based on how much time (amount percentage of changes done or time taken for normal human to edit) the user took to arrive at the user-generated content from the AI content."
                "Second Priority:Time Based Instructions (Follow this only when first priority is not met)"
                "Carry the analysis based on how much time (amount percentage of changes done or time taken for normal human to edit) the user took to arrive at the user-generated content from the AI content.\n"
                "1. **Rating 5 can be justifed**: Only IF Only No changes needed. and are exactly identical \n "
                "2. **Rating 4 can be justifed**: Only IF  it takes less than 20 to 30 seconds to do the changes \n"
                "3. **Rating 3 can be justifed**: Only IF it takes about  30 to 60 seconds to do the changes.or if more than 50% of ai content is edited \n"
                "4. **Rating 2 can be justifed**: Only IF it takes  1 minute - or more and is almost rewritten\n"
                "5. **Rating 1 can be justifed**: Only IF it is  almost or Complete rewritten.\n"
                "//Defination of a Sentence : Strictly ensure that if the review text contains 2 or fewer complete sentences, where a complete sentence is defined as a portion of text ending with a full stop (.), and **not a comma (,)**, and the provided rating is 2 or 3, the output should be 'Justified'."
              "##Feedback on Previous attempt of task :\n"
              "Here is the feedback from your previous try, Learn from your mistake and correct it And reanalyse the output json, and follow the correct format for the ouput: {{{Agentic_learning}}}\n"
                )
        else:
            description = (
                "Correctly Analyze the AI-generated content and the user-accepted content and properly utlize the data provided to determine if the rating provided is justified. Follow these guidelines:"
                "Check if the rating is justified or  weather a new rating is needed to be provided based on the percaentage change between AI generated content and user accepted content. Do not hallucinate.\n"
                "DATA:"
                "AI-generated content: {ai_content}\n"
                "User-accepted content: {vsp_content}\n"
                "Rating: {rating}\n"
                "Review Text is  Not present"
                "First Priority: Instructions"
                "Strictly make sure, When review text is not present and if the rating is 1, 2 or 3 then  the provided rating should be considered justified and in the final output at  justification  it should be added justified"
                "Second Priority:Time Based Instructions (Follow this only when first priority is not met)"
                "Carry the analysis based on how much time (amount percentage of changes done or time taken for normal human to edit) the user took to arrive at the user-generated content from the AI content.\n"
                "1. **Rating 5 can be justifed**: Only IF Only No changes needed. and are exactly identical \n "
                "2. **Rating 4 can be justifed**: Only IF  it takes less than 20 to 30 seconds to do the changes \n"
                "3. **Rating 3 can be justifed**: Only IF it takes about  30 to 60 seconds to do the changes.or if more than 50% of ai content is edited \n"
                "4. **Rating 2 can be justifed**: Only IF it takes  1 minute - or more and is almost rewritten\n"
                "5. **Rating 1 can be justifed**: Only IF it is  almost or Complete rewritten.\n"
                          "##Feedback on Previous attempt of task :\n"
                "Here is the feedback from your previous try, Learn from your mistake and correct it And reanalyse the output json here since the rating is chnaged from intial you have added justification as Justified, with the new rating the justification is should have been (new rating)   follow the correct format for the ouput: {{{Agentic_learning}}}\n"
                "If "
                )
        return Task(
            description=description,
            expected_output='A comprehensive analysis of the content and a rating validation Strictly in a JSON format. {{"Rating": "new Rating that should be allocated only a  int number)",\n "justification": "Give only either  Justified or should have been (expected number)",\n "explanation": "explanation"\n}}',
            agent=content_analyzer,
            config = {"Rating": "new Rating that should be allocated only an int number", "justification": "Give only either Justified  or should have been (new rating) ", "explanation": "explanation"},
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

    if os.path.exists(csv_file_path):
        df = load_local_csv(csv_file_path)
    else:
        st.error("CSV file not found. Please ensure the file exists.")

    if df is not None:
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
            st.info("""
            ## Report Generation in Progress.

            We will send the report CSV to your email address once generation is completed. Meanwhile, you can generate a new report or close this page.
            """)
            
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
            send_email_with_attachment(email, "Your Report of AI Content Rating Analysis", summary_text, attachment=output)

            st.download_button(
                label="Download Results as CSV",
                data=output.getvalue(),
                file_name='analysis_results.csv',
                mime='text/csv'
            )
