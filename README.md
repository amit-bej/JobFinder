# JobFinder Assistant

JobFinder Assistant is a smart job search application that combines web scraping with AI-powered resume analysis. It helps users find relevant job openings on Naukri.com that match their skills and experience.

## Features

-   **Resume Analysis**: Upload your resume (PDF, DOCX, TXT) to automatically extract skills and years of experience using RAG (Retrieval Augmented Generation).
-   **Job Scraping**: Automated scraping of job listings from Naukri.com based on role and location.
-   **Smart Matching**: Matches your resume details against scraped jobs to recommend the best fits.
-   **Interactive UI**: Built with Streamlit for an easy-to-use interface.

## LLM Configuration

The project is currently configured to use **Ollama** with the `gemma3:1b` model for text generation and `nomic-embed-text` for embeddings.

**To use your own LLM (Local or API-based):**
1.  Open `utils/Rag.py`.
2.  Modify the `getResponse` function to call your desired LLM (e.g., OpenAI, Anthropic, or a different local model).
3.  Modify the `embed` function if you wish to use a different embedding model.


## Prerequisites

-   Python 3.8+
-   Chrome Browser
-   ChromeDriver (compatible with your Chrome version)

## Installation

1.  Clone the repository:
    ```bash
    git clone <repository-url>
    cd JobFinder
    ```

2.  Install the required dependencies:
    ```bash
    pip install streamlit pandas selenium chromadb langchain
    # Add other dependencies as needed
    ```

3.  **Driver Setup**:
    -   Download the ChromeDriver matching your Chrome version.
    -   Place the `chromedriver.exe` in the `drivers/` folder (create the folder if it doesn't exist).
    -   *Note: The `drivers/` folder is ignored by git.*

## Usage

1.  Run the Streamlit application:
    ```bash
    streamlit run app.py
    ```

2.  **Steps in the App**:
    -   **Upload Resume**: Upload your resume in the sidebar.
    -   **View Analysis**: The app will display your extracted skills and experience.
    -   **Scrape Jobs**: Enter a Job Role and Location, then click "Scrape Jobs".
    -   **View Recommendations**: The app will verify and list jobs that match your profile.

## Project Structure

-   `app.py`: Main application entry point.
-   `scrapper/`: Contains logic for web scraping (Selenium).
-   `utils/`: Utility functions for RAG and text extraction.
-   `drivers/`: Directory for browser drivers (ignored).
-   `work/`: Directory for temporary work files (ignored).
