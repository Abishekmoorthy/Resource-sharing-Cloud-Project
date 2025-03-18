from flask import Flask, request, jsonify, render_template
from pytubefix import YouTube
import time
import json
import boto3
from botocore.exceptions import ClientError
import urllib
import uuid
from io import BytesIO
import PyPDF2
import pyodbc


app = Flask(__name__)

print(pyodbc.drivers())

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access the variables
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
aws_region = os.getenv('AWS_REGION')
bucket_name = os.getenv('BUCKET_NAME')

azure_sql_config = {
    'server': os.getenv('AZURE_SQL_SERVER'),
    'database': os.getenv('AZURE_SQL_DATABASE'),
    'username': os.getenv('AZURE_SQL_USERNAME'),
    'password': os.getenv('AZURE_SQL_PASSWORD'),
    'driver': os.getenv('AZURE_SQL_DRIVER'),
}
# (
#         f"DRIVER={azure_sql_config['driver']};"
#         f"SERVER={azure_sql_config['server']};"
#         f"DATABASE={azure_sql_config['database']};"
#         f"UID={azure_sql_config['username']};"
#         f"PWD={azure_sql_config['password']}"
#     )
# Azure SQL connection setup
def get_db_connection():
    conn_str = 'Driver={ODBC Driver 18 for SQL Server};Server=tcp:cloudprojserver.database.windows.net;Database=Cloud_proj;Uid=Guhan_cloud;Pwd=mable@123;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
    return pyodbc.connect(conn_str)

def save_to_db(video_title, summary, tags, user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Insert data into a table named video_summaries
    create_table_query = """
    IF NOT EXISTS (
    SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'video_summaries'
)
    CREATE TABLE video_summaries (
        id INT IDENTITY(1,1) PRIMARY KEY,
        video_title NVARCHAR(255),
        summary NVARCHAR(MAX),
        tags NVARCHAR(MAX),
        user_id NVARCHAR(50),
        created_at DATETIME DEFAULT GETDATE()
    );
    """
    cursor.execute(create_table_query)

    insert_query = """
    INSERT INTO video_summaries (video_title, summary, tags, user_id)
    VALUES (?, ?, ?, ?);
    """
    cursor.execute(insert_query, video_title, summary, ", ".join(tags), user_id)
    conn.commit()
    conn.close()

def save_to_db_pdf(pdf_title, summary, tags, user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Insert data into a table named video_summaries
    create_table_query = """
    IF NOT EXISTS (
    SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'pdf_summaries'
)
    CREATE TABLE pdf_summaries (
        id INT IDENTITY(1,1) PRIMARY KEY,
        pdf_title NVARCHAR(255),
        summary NVARCHAR(MAX),
        tags NVARCHAR(MAX),
        user_id NVARCHAR(50),
        created_at DATETIME DEFAULT GETDATE()
    );
    """
    cursor.execute(create_table_query)

    insert_query = """
    INSERT INTO pdf_summaries (pdf_title, summary, tags, user_id)
    VALUES (?, ?, ?, ?);
    """
    cursor.execute(insert_query, pdf_title, summary, ", ".join(tags), user_id)
    conn.commit()
    conn.close()
@app.route('/print_db_contents_pdf', methods=['GET'])
def print_db_contents_pdf():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Print video summaries
    # print("\n--- Video Summaries ---")
    # cursor.execute("SELECT * FROM video_summaries")
    # video_rows = cursor.fetchall()
    # for row in video_rows:
    #     print(row)

    # Print PDF summaries
    print("\n--- PDF Summaries ---")
    cursor.execute("SELECT * FROM pdf_summaries")
    pdf_rows = cursor.fetchall()
    result = []
    for row in pdf_rows:
        # Get column names from cursor description
        column_names = [desc[0] for desc in cursor.description]
        # Create a dictionary for each row
        row_dict = dict(zip(column_names, row))
        result.append(row_dict)
    
    conn.close()
    return result  # This will be JSON serializable
@app.route('/print_db_contents_vdo', methods=['GET'])
def print_db_contents_vdo():
    conn = get_db_connection()
    cursor = conn.cursor()

    #Print video summaries
    print("\n--- Video Summaries ---")
    cursor.execute("SELECT * FROM video_summaries")
    result=[]
    video_rows = cursor.fetchall()
    for row in video_rows:
        # Get column names from cursor description
        column_names = [desc[0] for desc in cursor.description]
        # Create a dictionary for each row
        row_dict = dict(zip(column_names, row))
        result.append(row_dict)
    
    conn.close()
    return result  # This will be JSON serializable

# Call the function to print database contents



def download_audio(url):
    """Downloads audio from a YouTube video as bytes."""

    vid = YouTube(url)
    audio_stream = vid.streams.get_audio_only()
    unique_id = str(uuid.uuid4())
    audio_file_name = f"{unique_id}.mp3"

    print(f"\nVideo found: {vid.title}\n")
    print("Downloading audio to memory...")

    audio_data = BytesIO()
    audio_stream.stream_to_buffer(audio_data)
    audio_data.seek(0)  

    print("Audio download complete.")

    return audio_data, audio_file_name

def upload_to_s3(file_data, bucket, object_name):
    """Uploads a file in bytes to an S3 bucket."""
    s3_client = boto3.client(
        's3',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key
    )
    try:
        print('Uploading file to S3...')
        # Use upload_fileobj for in-memory file-like objects
        s3_client.upload_fileobj(file_data, bucket, object_name)
        print("File uploaded to S3.")
    except ClientError as e:
        print(f"Failed to upload to S3: {e}")


def transcribe_audio(job_name, file_uri):
    """Transcribes an audio file using Amazon Transcribe."""
    transcribe_client = boto3.client(
        'transcribe',
        region_name=aws_region,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key
    )
    transcribe_client.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': file_uri},
        MediaFormat='mp3',
        LanguageCode='en-US'
    )
    
    print("Transcription started...")
    while True:
        job = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
        status = job['TranscriptionJob']['TranscriptionJobStatus']
        if status in ['COMPLETED', 'FAILED']:
            print(f"Job {job_name} is {status}.")
            if status == 'COMPLETED':
                response = urllib.request.urlopen(job['TranscriptionJob']['Transcript']['TranscriptFileUri'], timeout=30)
                data = json.loads(response.read())
                text = data['results']['transcripts'][0]['transcript']
                print("Transcription complete. Transcript saved.")
            break
        else:
            print("Transcription in progress. Waiting...")
        time.sleep(20)
    return text

def summarize_text(t):
    """Summarizes the transcribed text using Bedrock."""
    model_id = 'us.meta.llama3-2-1b-instruct-v1:0'
    bedrock = boto3.client(
        "bedrock-runtime",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=aws_region
    )
    t += " Summarize the above in 3 to 4 lines."
    
    prompt = (
        "You are a content summarization expert. Summarize the given content meaningfully without omitting important details."
        f"\n\nHuman:{t}\n\nAssistant:"
    )   

    
    request = json.dumps({"prompt": prompt, "temperature": 0.5})
    print("hellp")
    response = bedrock.invoke_model(modelId=model_id, body=request)
    print("hellpo 2")
    model_response = json.loads(response["body"].read())
    summary = model_response["generation"]
    
    print("Your Summary:", summary)
    return summary

def extract_text_from_pdf(pdf_file):
    print("started extracting text from pdf")
    reader = PyPDF2.PdfReader(pdf_file)
    text = "".join([page.extract_text() for page in reader.pages if page.extract_text()])
    print("extracted text from pdf..summarizing")
    text=summarize_text(text)
    return text

def generate_tags(text):
    model_id = 'us.meta.llama3-2-1b-instruct-v1:0'
    bedrock = boto3.client(
        "bedrock-runtime",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=aws_region
    )
    prompt = (
        f"Extract 10-15 single-word tags from the following text. maximum 100 words"
        f"Only return the tags, comma-separated (e.g., AI, machine-learning, NLP, cloud) no need to add notes and introduction:\n\n{text}"
    )
    request = json.dumps({"prompt": prompt, "temperature": 0.5})
    response = bedrock.invoke_model(modelId=model_id, body=request)
    model_response = json.loads(response["body"].read())
    print("tags generated : ", model_response["generation"])
    return model_response["generation"]

@app.route('/')
def index():
    return render_template('index.html')

# @app.route('/get_summary', methods=['POST'])
# def get_summary():
#     data = request.json
#     url = data.get('url')
#     if url:
#         audio_file, unique_id = download_audio(url)
#         s3_uri = f's3://{bucket_name}/{unique_id}.mp3'
#         upload_to_s3(audio_file, bucket_name, f"{unique_id}.mp3")
#         transcription_text = transcribe_audio(unique_id, s3_uri)
#         summary = summarize_text(transcription_text) if transcription_text else ""
#         return jsonify({"summary": summary})
#     return jsonify({"error": "Invalid URL"})

@app.route('/get_summary', methods=['POST'])
def get_summary():
    data = request.json
    url = data.get('url')
    user_id = 'user1'
    if url and user_id:
        unique_id="101"
        audio_file, video_title = download_audio(url)
        s3_uri = f's3://{bucket_name}/{unique_id}.mp3'
        upload_to_s3(audio_file, bucket_name, f"{unique_id}.mp3")
        transcription_text = transcribe_audio(unique_id, s3_uri)
        summary = summarize_text(transcription_text)
        tags = generate_tags(transcription_text)
        save_to_db(video_title, summary, tags, user_id)
        return jsonify({"summary": summary, "tags": tags})
@app.route('/pdf')
def pdf():
    return render_template('pdf.html')


@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"})

    pdf_file = request.files['file']
    user_id = 'user1'
    pdf_title = pdf_file.filename
    extracted_text = extract_text_from_pdf(pdf_file)
    tags = generate_tags(extracted_text)
    
    

    # Ensure tags is always a list
    if not isinstance(tags, list):
        tags = tags.split(", ") if isinstance(tags, str) else list(tags) if isinstance(tags, set) else []

    tags = [tag for tag in tags if len(tag) <= 20]
    save_to_db_pdf(pdf_title, extracted_text, tags, user_id)
    
    return jsonify({"tags": tags})

if __name__ == '__main__':
    app.run(debug=True)





    app.run(debug=True)