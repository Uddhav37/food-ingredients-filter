# Ingredient Health Analyzer

An AI-powered application that analyzes product ingredient labels and provides health-based purchase recommendations.

## Features

- 📸 Upload product ingredient label images
- 🔍 OCR extraction using Google Cloud Vision API
- 🤖 AI-powered ingredient research using LangChain and Gemini Pro
- 🔬 Automated health impact analysis with scoring
- ✅ Clear buy/don't buy recommendations with reasoning

## Project Structure

```
.
├── app.py                   # Streamlit web application
├── ocr_service.py           # OCR extraction and ingredient parsing
├── agent_research.py        # LangChain agent for health research
├── recommendation_service.py # Recommendation generation
├── example_ocr_usage.py     # OCR service examples
├── example_agent_usage.py   # Agent research examples
├── test_ocr.py             # OCR service tests
├── test_agent.py           # Agent research tests
└── requirements.txt        # Python dependencies
```

## Setup

### Prerequisites

- Python 3.9 or higher
- Google Cloud Platform account with:
  - Cloud Vision API enabled
  - Vertex AI API enabled
  - Service account with appropriate permissions
- Tavily API key (free tier available at https://tavily.com)

### Installation

1. Clone the repository and navigate to the project directory

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
```

4. Edit `.env` file with your actual credentials:
   - `GCP_PROJECT_ID`: Your Google Cloud project ID
   - `GOOGLE_APPLICATION_CREDENTIALS`: Path to your service account JSON file
   - `TAVILY_API_KEY`: Your Tavily API key

### Running the Application

```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`

## Usage

### Testing OCR Service

```bash
python example_ocr_usage.py path/to/product_label.jpg
```

### Testing Agent Research

```bash
python example_agent_usage.py
```

### Running Tests

```bash
# Test OCR functionality
python test_ocr.py

# Test agent research functionality
python test_agent.py
```

### Using the Web Application

```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`

1. Upload an image of a product ingredient label
2. Wait for OCR extraction and AI analysis
3. Review the recommendation and detailed ingredient analysis

## Deployment

### Google Cloud Run

```bash
gcloud run deploy ingredient-analyzer \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## License

MIT
