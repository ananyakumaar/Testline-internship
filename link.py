import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Constants
QUIZ_METADATA_FILE = "quiz.json"
QUIZ_SUBMISSION_ENDPOINT = "https://api.jsonserve.com/rJvd7g"
HISTORICAL_DATA_ENDPOINT = "https://api.jsonserve.com/XgAgFJ"
PASSING_SCORE = 50  # Define a passing score threshold

# Load quiz metadata
def load_quiz_metadata(file_path):
    with open(file_path, 'r') as file:
        return pd.read_json(file)

# Fetch data from API endpoint
def fetch_data(endpoint):
    response = requests.get(endpoint)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Failed to fetch data: {response.status_code}")
        return None

# Analyze performance
def analyze_performance(historical_quiz_data):
    df = pd.DataFrame(historical_quiz_data)
    
    # Extract topic from nested quiz data
    df['topic'] = df['quiz'].apply(lambda x: x['topic'])
    
    # Group by topic to summarize scores
    performance_summary = df.groupby('topic').agg({
        'score': ['mean', 'std', 'count'],
        'accuracy': lambda x: x.str.replace('%', '').astype(float).mean()  # Convert accuracy to float
    }).reset_index()
    
    performance_summary.columns = ['topic', 'mean_score', 'std_score', 'attempts', 'mean_accuracy']
    
    return performance_summary

# Generate insights
def generate_insights(performance_summary):
    weak_areas = performance_summary[performance_summary['mean_score'] < PASSING_SCORE]
    return weak_areas

# Create recommendations
def create_recommendations(weak_areas):
    recommendations = weak_areas['topic'].tolist()
    return recommendations

# Define student persona
def define_student_persona(user_id, historical_quiz_data):
    user_data = pd.DataFrame(historical_quiz_data)
    user_data = user_data[user_data['user_id'] == user_id]
    
    strengths = user_data[user_data['score'] > PASSING_SCORE]['quiz'].apply(lambda x: x['topic']).unique()
    weaknesses = user_data[user_data['score'] < PASSING_SCORE]['quiz'].apply(lambda x: x['topic']).unique()
    
    return {
        'strengths': strengths,
        'weaknesses': weaknesses,
        'recommendations': create_recommendations(generate_insights(analyze_performance(historical_quiz_data)))
    }

# Visualize trends
def visualize_trends(historical_quiz_data):
    df = pd.DataFrame(historical_quiz_data)
    
    # Convert submitted_at to datetime for plotting
    df['submitted_at'] = pd.to_datetime(df['submitted_at'])
    
    trends = df.groupby(df['submitted_at'].dt.date).agg({'score': 'mean'}).reset_index()
    
    plt.figure(figsize=(10, 5))
    sns.lineplot(data=trends, x='submitted_at', y='score')
    plt.title('Average Quiz Score Over Time')
    plt.xlabel('Quiz Date')
    plt.ylabel('Average Score')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    st.pyplot(plt)

# Main Streamlit app function
def main():
    st.title("Quiz Performance Analysis")
    
    # User ID input
    user_id = st.text_input("Enter your User ID:")
    
    if st.button("Submit"):
        if user_id:
            # Fetch historical quiz data from API
            historical_quiz_data = fetch_data(HISTORICAL_DATA_ENDPOINT)
            
            if historical_quiz_data:
                # Analyze performance
                performance_summary = analyze_performance(historical_quiz_data)

                # Generate insights and recommendations
                weak_areas = generate_insights(performance_summary)
                recommendations = create_recommendations(weak_areas)

                # Display results
                st.subheader("Weak Areas:")
                st.write(weak_areas)

                st.subheader("Recommendations for Improvement:")
                st.write(recommendations)

                # Define student persona
                student_persona = define_student_persona(user_id, historical_quiz_data)
                
                st.subheader("Student Persona:")
                st.write(student_persona)

                # Visualize trends
                visualize_trends(historical_quiz_data)
        else:
            st.warning("Please enter a valid User ID.")

if __name__ == "__main__":
    main()
