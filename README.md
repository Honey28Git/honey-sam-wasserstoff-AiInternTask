# honey-sam-wasserstoff-AiInternTask
## PDF Parsing and Summarization App
A web application for efficient parsing, keyword extraction, metadata gathering, and summarization of PDF documents. This app processes multiple PDFs, extracts domain-specific information, and stores results in MongoDB. With an intuitive web interface, users can upload PDFs, parse their content, view extracted data, and download results in JSON format. Designed with a focus on concurrency, resource management, and a clean UI.

### Features
- Parallel PDF Processing: Efficient handling of multiple PDFs with concurrency.
- Metadata Extraction: Title, author, keywords, file path, size, memory usage, and processing time.
- Summarization: Dynamic summarization of document content tailored to document length and domain.
- MongoDB Integration: Metadata and summaries stored in MongoDB for easy retrieval and management.
- Web Interface: Upload and process files, view parsed data, and download results in a user-friendly format.
- Stylized Display: Metadata fields highlighted in a clean, structured layout, with color-coded elements and a read-only summary box.

```project-directory/
│
├── app.py                # Main Flask app with endpoints for file upload, parsing, and display
├── pdf_processing.log    # Log file for tracking processing events and errors
├── requirements.txt      # Python dependencies for the application
├── static/
│   ├── styles.css        # Custom CSS for styling the web interface
│   └── script.js         # JavaScript for handling frontend functionality
├── templates/
│   └── upload.html       # HTML template for file upload and result display
└── README.md             # Project documentation
```

## Installation 
1. Clone the Repository
   in bash: git clone https://github.com/yourusername/pdf-parsing-summarization-app.git
cd pdf-parsing-summarization-app

2. Set up Virtual Environment
   in bash: python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate

3. Install Dependencies
   in bash: pip install -r requirements.txt
4. Set Up MongoDB
    Ensure MongoDB is running locally or provide a remote MongoDB URI in the app configuration.
## Usage
1. Run the Application
   python app.py
2. Access the web interface
- Open a web browser and navigate to [https://pdf-parser-ggcw.onrender.com/).
- Upload a PDF file using the provided interface.
3. View Results
  After parsing, metadata fields such as title, author, keywords, and summary will display.
  Click “Download Results” to export the metadata and summary as a JSON file.
4. Configuration
    MongoDB Connection: Modify app.py to connect to your MongoDB instance.
    Concurrency Settings: Adjust as needed for optimal performance with larger PDF batches.
    Summary Length: Customize summarization length within the summarization function as needed.
## Contributing
- Fork the repository.
- Create a new branch with a descriptive name.
- Make your changes and push to your fork.
- Open a pull request.

## Solution Explanation
- This app enables the efficient parsing and summarization of PDFs. It allows users to upload multiple PDFs, which are processed concurrently to manage system resources effectively.
- The extracted information is saved in a MongoDB database, where users can retrieve and download metadata.

## Key Components
- Metadata Extraction: The app extracts file name, file path, title, author, keywords, and size.
- Summarization: Generates a concise summary of the PDF content, dynamically adjusted based on document length.
- Web Interface: A user-friendly interface for file uploads, displaying parsed results, and downloading metadata as JSON.
- Concurrency: Processes PDFs in parallel to optimize resource usage and reduce processing time.

## Acknowledgments
- Flask for the web framework.
- pdfplumber for PDF parsing.
- MongoDB for storage.
