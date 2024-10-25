import os
import pdfplumber
import logging
import re
from collections import Counter
from nltk.corpus import stopwords
import pymongo
import spacy
import time
import psutil
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(level=logging.INFO, filename="pdf_processing.log", filemode="a")

# Download stopwords if not already downloaded
import nltk
nltk.download('stopwords')

# Load English stop words
stop_words = set(stopwords.words('english'))

# Load the spaCy model
nlp = spacy.load("en_core_web_sm")

# Retrieve MongoDB connection URI from environment variables
mongodb_uri = os.getenv('MONGODB_URI')  # Fetch the MongoDB URI

# MongoDB setup
mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
db = mongo_client['pdf_database']
collection = db['pdf_metadata']

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

def save_to_mongodb(file_path, title, authors, keywords, summary, time_taken, memory_usage):
    document = {
        "file_name": os.path.basename(file_path),
        "file_path": file_path,
        "file_size": os.path.getsize(file_path),
        "title": title,
        "author": authors,
        "keywords": keywords,
        "summary": summary,
        "time_taken_sec": time_taken,
        "memory_usage_mb": memory_usage
    }
    collection.insert_one(document)

def process_pdf(file_path):
    start_time = time.time()
    process = psutil.Process(os.getpid())
    title, authors, keywords_list, summary = parse_pdf_metadata_and_summarize(file_path)
    time_taken = time.time() - start_time
    memory_usage = process.memory_info().rss / (1024 * 1024)
    save_to_mongodb(file_path, title, authors, keywords_list, summary, time_taken, memory_usage)
    print(f"Processed: {os.path.basename(file_path)}")

if __name__ == "__main__":
    pdf_folder_path = r"C:\Users\honey\Documents\Data Science\Wasserstoff\PDFs"
    pdf_files = [os.path.join(pdf_folder_path, f) for f in os.listdir(pdf_folder_path) if f.endswith('.pdf')]

    with ThreadPoolExecutor(max_workers=4) as executor:  # Use 4 threads (adjust as needed)
        futures = {executor.submit(process_pdf, pdf_file): pdf_file for pdf_file in pdf_files}
        for future in as_completed(futures):
            future.result()  # To raise exceptions if any

    print("All tasks completed.")
