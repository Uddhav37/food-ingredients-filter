# Deployment Guide - Ingredient Health Analyzer

This guide covers deploying the Ingredient Health Analyzer to Google Cloud Platform using Cloud Run.

## Prerequisites

- Google Cloud Platform account
- `gcloud` CLI installed and configured
- Docker installed (for local testing)
- Required API keys (see Environment Variables section)

## Environment Variables

The application requires the following environment variables:

### Required Variables

| Variable | Description | How to Obtain |
|----------|-------------|---------------|
| `GCP_PROJECT_ID` | Your Google Cloud project ID | From GCP Console |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account JSON (local) or use Cloud Run's default service account | Create in IAM & Admin |
| `TAVILY_API_KEY` | API key for Tavily search | Sign up at https://tavily.com |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `STREAMLIT_SERVER_PORT` | Port for Streamlit | 8501 |

## Google Cloud Setup

### 1. Create GCP Project

```bash
# Create a new project (or use existing)
gcloud projects create YOUR_PROJECT_ID --name="Ingredient Health Analyzer"

# Set as active project
gcloud config set project YOUR_PROJECT_ID
```

### 2. Enable Required APIs

```bash
# Enable Cloud Run
gcloud services enable run.googleapis.com

# Enable Cloud Vision API
gcloud services enable vision.googleapis.com

# Enable Vertex AI API
gcloud services enable aiplatform.googleapis.com

# Enable Container Registry
gcloud services enable containerregistry.googleapis.com
```

### 3. Create Service Account

```bash
# Create service account
gcloud iam service-accounts create ingredient-analyzer \
    --display-name="Ingredient Health Analyzer Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:ingredient-analyzer@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:ingredient-analyzer@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/vision.user"

# For local development, download key
gcloud iam service-accounts keys create service-account-key.json \
    --iam-account=ingredient-analyzer@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

### 4. Get Tavily API Key

1. Visit https://tavily.com
2. Sign up for a free account
3. Navigate to API Keys section
4. Copy your API key

## Deployment Options

### Option 1: Deploy to Cloud Run (Recommended)

#### Quick Deploy from Source

```bash
# Deploy directly from source code
gcloud run deploy ingredient-analyzer \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --service-account ingredient-analyzer@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --set-env-vars GCP_PROJECT_ID=YOUR_PROJECT_ID,TAVILY_API_KEY=YOUR_TAVILY_KEY \
  --memory 2Gi \
  --timeout 300
```

#### Deploy with Docker

```bash
# Build the Docker image
docker build -t gcr.io/YOUR_PROJECT_ID/ingredient-analyzer:latest .

# Push to Google Container Registry
docker push gcr.io/YOUR_PROJECT_ID/ingredient-analyzer:latest

# Deploy to Cloud Run
gcloud run deploy ingredient-analyzer \
  --image gcr.io/YOUR_PROJECT_ID/ingredient-analyzer:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --service-account ingredient-analyzer@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --set-env-vars GCP_PROJECT_ID=YOUR_PROJECT_ID,TAVILY_API_KEY=YOUR_TAVILY_KEY \
  --memory 2Gi \
  --timeout 300
```

### Option 2: Local Development with Docker

```bash
# Build the image
docker build -t ingredient-analyzer .

# Run locally
docker run -p 8501:8501 \
  -e GCP_PROJECT_ID=YOUR_PROJECT_ID \
  -e TAVILY_API_KEY=YOUR_TAVILY_KEY \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/service-account-key.json \
  -v $(pwd)/service-account-key.json:/app/service-account-key.json \
  ingredient-analyzer
```

Access at http://localhost:8501

### Option 3: Local Development without Docker

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GCP_PROJECT_ID=YOUR_PROJECT_ID
export TAVILY_API_KEY=YOUR_TAVILY_KEY
export GOOGLE_APPLICATION_CREDENTIALS=./service-account-key.json

# Run the app
streamlit run app.py
```

Access at http://localhost:8501

### Option 4: Quick Demo with ngrok

For quick demos without cloud deployment:

```bash
# Run locally
streamlit run app.py

# In another terminal, expose with ngrok
ngrok http 8501
```

Use the ngrok URL to share your demo.

## Post-Deployment

### Verify Deployment

```bash
# Get the service URL
gcloud run services describe ingredient-analyzer \
  --platform managed \
  --region us-central1 \
  --format 'value(status.url)'
```

Visit the URL to test the application.

### View Logs

```bash
# Stream logs
gcloud run services logs tail ingredient-analyzer \
  --platform managed \
  --region us-central1
```

### Update Environment Variables

```bash
# Update environment variables
gcloud run services update ingredient-analyzer \
  --platform managed \
  --region us-central1 \
  --set-env-vars NEW_VAR=value
```

## Security Best Practices

1. **Never commit secrets**: Keep `.env` files and service account keys out of version control
2. **Use Secret Manager**: For production, use Google Secret Manager instead of environment variables
3. **Restrict service account permissions**: Only grant minimum required permissions
4. **Enable authentication**: For production, remove `--allow-unauthenticated` flag
5. **Use VPC**: For sensitive data, deploy within a VPC

## Troubleshooting

### Common Issues

#### "Permission denied" errors
- Verify service account has correct IAM roles
- Check that APIs are enabled in your project

#### "Module not found" errors
- Ensure all dependencies are in requirements.txt
- Rebuild Docker image after adding dependencies

#### OCR not working
- Verify Cloud Vision API is enabled
- Check service account has `roles/vision.user`

#### Agent research failing
- Verify Vertex AI API is enabled
- Check TAVILY_API_KEY is set correctly
- Ensure service account has `roles/aiplatform.user`

#### Timeout errors
- Increase timeout: `--timeout 300` (5 minutes)
- Increase memory: `--memory 2Gi`

### Debug Mode

Enable verbose logging:

```bash
# Set environment variable
gcloud run services update ingredient-analyzer \
  --set-env-vars STREAMLIT_LOGGER_LEVEL=debug
```

## Cost Estimation

Estimated costs for moderate usage (100 analyses/day):

- **Cloud Run**: ~$5-10/month (free tier: 2M requests/month)
- **Cloud Vision API**: ~$1.50 per 1000 images (first 1000 free/month)
- **Vertex AI (Gemini)**: ~$0.00025 per 1K characters (~$5-10/month)
- **Total**: ~$10-20/month for moderate usage

Free tier covers most demo and development usage.

## Scaling Considerations

Cloud Run automatically scales based on traffic:

- **Min instances**: 0 (scales to zero when idle)
- **Max instances**: 100 (default, can be increased)
- **Concurrency**: 80 requests per instance (default)

For high traffic, consider:
- Increasing max instances
- Using Cloud CDN for static assets
- Implementing caching for common ingredients

## Support

For issues or questions:
- Check Cloud Run logs: `gcloud run services logs tail ingredient-analyzer`
- Review GCP documentation: https://cloud.google.com/run/docs
- Check Streamlit docs: https://docs.streamlit.io
