import os
import streamlit as st
import pandas as pd
from case_retrieval import retrieve_similar_cases
from text_summarization import summarize_text
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import gcsfs

# Load environment variables
load_dotenv()
api_key = os.getenv('PINECONE_API_KEY')
gcs_bucket = os.getenv('GCS_BUCKET')

@st.cache_data
def load_dataset():
    gcs_file_path = f'gs://{gcs_bucket}/cleaned_data.csv'
    fs = gcsfs.GCSFileSystem()
    df = pd.read_csv(gcs_file_path, storage_options={'gcsfs': fs})
    df = df[['id', 'majority_opinion']]  
    return df

df_cleaned = load_dataset()

case_lookup = {int(row['id']): row['majority_opinion'] for _, row in df_cleaned.iterrows()}

@st.cache_resource
def load_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

model = load_model()

def get_case_summaries(input_text, top_k=5):
    similar_case_ids = retrieve_similar_cases(input_text, top_k=top_k)
    summaries = []
    
    for case_id in similar_case_ids:
        try:
            case_id_int = int(float(case_id))
            if case_id_int in case_lookup:
                case_text = case_lookup[case_id_int]
                summary = summarize_text(case_text)
                summaries.append({'case_id': case_id_int, 'summary': summary})
        except Exception as e:
            st.error(f"Error processing case_id {case_id}: {e}")
    
    return summaries


### APP LAYOUT
st.title('LegalLens - Precedence Lookup')
st.header('Find Similar Cases and Summarize Them')

input_text = st.text_area('Enter case details:', height=200)
top_k = st.slider('Number of similar cases to retrieve:', 1, 10, 5)

# Button to trigger case retrieval and summarization
if st.button('Find Similar Cases'):
    if input_text.strip() == "":
        st.error("Please enter the case details.")
    else:
        with st.spinner('Retrieving similar cases and generating summaries...'):
            case_summaries = get_case_summaries(input_text, top_k=top_k)
        st.success('Similar cases and summaries retrieved successfully!')
        
        for i, case in enumerate(case_summaries):
            with st.expander(f'Case {i+1} (ID: {case["case_id"]})'):
                st.write(case['summary'])


st.markdown(
    """
    <style>
    footer {visibility: hidden;}
    .footer {visibility: visible; position: relative; bottom: 10px; text-align: center;}
    </style>
    """,
    unsafe_allow_html=True
)
st.markdown('<div class="footer">Developed by Zeeshan Hameed</div>', unsafe_allow_html=True)