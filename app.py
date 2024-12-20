import os
import json 
import pdfplumber
import logging
import re
from collections import Counter
from flask import Flask, request, jsonify, send_file, render_template
from nltk.corpus import stopwords
import pymongo
import spacy
import time
import psutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from werkzeug.utils import secure_filename

# Initialize Flask app
app = Flask(__name__)

if not os.path.exists("uploads"):
    os.makedirs("uploads")

# Configure logging
logging.basicConfig(level=logging.INFO, filename="pdf_processing.log", filemode="a")

# MongoDB setup
mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
db = mongo_client['pdf_database']
collection = db['pdf_metadata']

# Download stopwords if not already downloaded
import nltk
nltk.download('stopwords')

# Load English stop words
stop_words = set(stopwords.words('english'))

# Load the spaCy model
nlp = spacy.load("en_core_web_sm")

# HTML Route
@app.route('/')
def index():
    app.logger.info("Rendering upload.html")
    return render_template('upload.html')  # Ensure this file exists in a 'templates' folder

# Upload Route
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file part'}), 400

@app.route('/parse', methods= ['POST'])
def parse_pdf():
    files = request.files.getlist('file')
    results = []
    errors = []

    if not files:
        return jsonify({"success": False, "message": "No files uploaded."}), 400

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(process_pdf, file): file.filename for file in files}
        for future in as_completed(futures):
            result = future.result()
            if isinstance(result, dict) and 'error' in result:
                errors.append(result)
            else:
                results.append(result)

    if errors:
        return jsonify({"success": False, "results": results, "errors": errors}), 400
    
    return jsonify({"success": True, "results": results, "errors": errors})

# Function to process each PDF file
def process_pdf(file):
    file_path = os.path.join("uploads", secure_filename(file.filename))  # Ensure the uploads directory exists
    file.save(file_path)  # Save the uploaded file

    start_time = time.time()
    process = psutil.Process(os.getpid())
    
    title, authors, keywords, summary = parse_pdf_metadata_and_summarize(file_path)
    time_taken = time.time() - start_time
    memory_usage = process.memory_info().rss / (1024 * 1024)
    
    save_to_mongodb(file_path, title, authors, keywords, summary, time_taken, memory_usage)
    
    return {
        "file_name": os.path.basename(file_path),
        "title": title,
        "author": authors,
        "keywords": keywords,
        "summary": summary,
        "file_path": file_path,
        "file_size": os.path.getsize(file_path),
        "time_taken_sec": time_taken,
        "memory_usage_mb": memory_usage
    }

# Function to extract title, author, keywords, and summary
def parse_pdf_metadata_and_summarize(file_path):
    try:
        title = "Unknown Title"
        authors = "Unknown Author"
        extracted_keywords = []
        summary_text = ""

        with pdfplumber.open(file_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"

            if text:
                first_page_text = pdf.pages[0].extract_text()
                if first_page_text:
                    title_words = [word for word in first_page_text.split() if "(" not in word][:10]
                    title = ' '.join(title_words)

                authors_matches = re.findall(r'\((.*?)\)', first_page_text)
                if authors_matches:
                    authors = ', '.join(authors_matches)

                word_list = re.findall(r'\b\w+\b', text.lower())
                filtered_words = [word for word in word_list if word not in stop_words]
                most_common_words = Counter(filtered_words).most_common(10)
                extracted_keywords = [word for word, count in most_common_words]

                doc = nlp(text)
                summary_text = summarize_text(doc, num_sentences=2)

        return title, authors, extracted_keywords, summary_text
    except Exception as e:
        logging.error(f"Error parsing PDF {file_path}: {e}")
        return "Unknown Title", "Unknown Author", [], "Error during summarization"

# Function to summarize text
def summarize_text(doc, num_sentences=2):
    word_frequencies = {}
    for token in doc:
        if not token.is_stop and not token.is_punct:
            word_frequencies[token.text.lower()] = word_frequencies.get(token.text.lower(), 0) + 1

    sentence_scores = {}
    for sent in doc.sents:
        for word in sent:
            if word.text.lower() in word_frequencies:
                if sent in sentence_scores:
                    sentence_scores[sent] += word_frequencies[word.text.lower()]
                else:
                    sentence_scores[sent] = word_frequencies[word.text.lower()]

    summarized_sentences = sorted(sentence_scores, key=sentence_scores.get, reverse=True)[:num_sentences]
    summary = ' '.join([sent.text for sent in summarized_sentences])
    return summary

# Download metadata as JSON
@app.route('/download/<file_name>', methods=['GET'])
def download_metadata(file_name):
    document = collection.find_one({"file_name": file_name})
    if not document:
        return jsonify({'error': 'Document not found'}), 404

    # Remove the MongoDB ObjectId from the document
    document.pop('_id', None)

    json_file_path = f"{file_name}_metadata.json"
    with open(json_file_path, 'w') as json_file:
        json.dump(document, json_file)

    return send_file(json_file_path, as_attachment=True)
