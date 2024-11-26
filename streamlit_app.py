import os
import pandas as pd
import openai
from crewai import Agent, Task, Crew
from datetime import datetime
import json
import streamlit as st
import matplotlib.pyplot as plt
from io import StringIO
import re
# Streamlit UI
st.title("AI Content Rating Analysis")

# Add input for OpenAI API key
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
        tasks=[],  # Tasks will be added dynamically based on the review_text condition
        verbose=True,
        memory=True  # If context between tasks is important
    )
    def analyze_and_validate(row):
          ai_content = row['AI Content']
          vsp_content = row['vSp edited content']
          rating = row['vSp Rating']
          review_text = row['Review Text']
          prompt = row['Prompt']
          Agentic_learning = ""
          if not isinstance(vsp_content, str) or not vsp_content.strip():
              return "NA", "unjustified", "no vsp edited content for analysis"
          attempts = 0
          while attempts < 10:
              inputs = {
              "ai_content": ai_content,
              "vsp_content": vsp_content,
              "rating": rating,
              "review_text": review_text,
              "prompt": prompt,
              "Agentic_learning":Agentic_learning
              }
              review_text_present = isinstance(review_text, str) and bool(review_text.strip())
              crew.tasks = [
                  create_analyze_content_task(review_text_present)
              ]
              pattern = re.compile(r'should have been (\d+)')
              result = crew.kickoff(inputs=inputs)
              result_content = str(result)
              Agentic_learning += "\n"+ f""" In your attempt {int(attempts)+1} Discrepancy detected in your response : {result_content} """+"\n"
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
                          print(f"Cannot convert new_rating '{new_rating}' to an integer. Re-analyzing...")
                          attempts += 1
                          continue
                  if new_rating is None or justification == "" or explanation is None:
                      print(f"Missing fields detected for row with AI content: {ai_content}. Re-analyzing...")
                      attempts += 1
                      continue
                  # Ensure the justification is not "Justified" if the input rating and output rating differ
                  if new_rating != rating and justification == "justified":
                      print(f"Discrepancy detected in justification for row with AI content: {ai_content}. Re-analyzing...")
                      attempts += 1
                      continue
                  return new_rating, justification, explanation
              except (json.JSONDecodeError, KeyError, TypeError):
                  print(f"Parsing failed or missing keys in response for AI content: {ai_content}. Retrying...")
              print("Retrying analysis...")
              attempts += 1
          return rating , justification = "NA", explanation = "Not analysed"

    def process_batch(batch):
        output = batch.apply(analyze_and_validate, axis=1, result_type='expand')
        batch[['output_rating', 'justification', 'explanation']] = output
        return batch

    uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        df['vSp Rating'] = pd.to_numeric(df['vSp Rating'], errors='coerce')
        df_filtered = df.dropna(subset=['vSp Rating']).copy()
        df_filtered['Date'] = pd.to_datetime(df_filtered['Date'], format='%b %d %Y')

        start_date = st.date_input("Start Date", value=df_filtered['Date'].min())
        st.write("**Note:** Only choose either one or two days for analysis.")  # Add note below start date

        # Limit the selection of end_date to one day after the start date
        possible_end_dates = pd.date_range(start=start_date, periods=2).tolist()
        end_date = st.date_input("End Date", value=possible_end_dates[0], min_value=possible_end_dates[0], max_value=possible_end_dates[-1])

        start_date = datetime.combine(start_date, datetime.min.time())
        end_date = datetime.combine(end_date, datetime.min.time())

        # Filter the DataFrame
        df_filtered = df_filtered[(df_filtered['Date'] >= start_date) & (df_filtered['Date'] <= end_date)].copy()
        rating_counts = df_filtered['vSp Rating'].value_counts().sort_index()

        # Plotting with vertical x-axis labels and data labels
        fig, ax = plt.subplots()
        bars = ax.bar(rating_counts.index, rating_counts.values, color='skyblue')

        # Add data labels
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,  # X position
                height,  # Y position (height of the bar)
                f'{height}',  # Label text
                ha='center',  # Horizontal alignment
                va='bottom',  # Vertical alignment
                fontsize=10  # Font size
            )

        # Customize the plot
        ax.set_xlabel('vSp Rating')
        ax.set_ylabel('Count')
        ax.set_title('vSp Rating Counts')
        plt.xticks()  # Rotate x-axis labels for better readability
        st.pyplot(fig)


        if st.button("Analyze"):
            df_filtered_low_rating = df_filtered[df_filtered['vSp Rating'] <= 4]
            results = pd.DataFrame()
            BATCH_SIZE = 10
            for start in range(0, len(df_filtered_low_rating), BATCH_SIZE):
                batch = df_filtered_low_rating.iloc[start:start + BATCH_SIZE]
                results = pd.concat([results, process_batch(batch)], ignore_index=True)

            df_combined = pd.concat([results, df[df['vSp Rating'] > 4]], ignore_index=True)

            justified_low_ratings = results[results['justification'] == 'justified']
            correct_reviews = len(justified_low_ratings) + rating_counts.get(5.0, 0)

            # Display overall summary
            summary_data = {
                "Total Reviews": [len(df_filtered)],
                "Correct Reviews": [correct_reviews],
                "Overrated Reviews": [len(df_combined[(df_combined['justification'].str.contains('should have been', na=False)) & (df_combined['output_rating'] < df_combined['vSp Rating'])])],
                "Underrated Reviews": [len(df_combined[(df_combined['justification'].str.contains('should have been', na=False)) & (df_combined['output_rating'] > df_combined['vSp Rating'])])]
            }
            st.write("Overall Summary")
            st.table(pd.DataFrame(summary_data))

            # Allow downloading the results
            st.write("Download the Analysis csv with justification and explanation")
            output = StringIO()
            df_combined.to_csv(output, index=False)
            st.download_button(
                label="Download Results as CSV",
                data=output.getvalue(),
                file_name='analysis_results.csv',
                mime='text/csv'
            )
