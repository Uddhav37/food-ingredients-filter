"""
Ingredient Health Analyzer - Streamlit Application

A web application that analyzes product ingredient labels using OCR and AI-powered
health research to provide buy/don't buy recommendations.

INTEGRATION ARCHITECTURE:
========================
This application integrates three main components in a sequential pipeline:

1. OCR Service (ocr_service.py)
   - Input: Image bytes from uploaded file
   - Output: List of ingredient strings
   - Integration: Called in process_image() -> extract_ingredients_from_image()

2. Agent Research System (agent_research.py)
   - Input: List of ingredient strings from OCR
   - Output: List of research results with health scores
   - Integration: Called in process_image() -> research_multiple_ingredients()

3. Recommendation Generator (recommendation_service.py)
   - Input: List of research results from Agent
   - Output: Final recommendation with reasoning and summary
   - Integration: Called in process_image() -> generate_recommendation()

SESSION STATE MANAGEMENT:
========================
- analysis_results: Stores complete analysis output for display persistence
- processing: Boolean flag for processing state
- extracted_ingredients: Cached OCR results for verification display
- processing_time: Duration of complete analysis pipeline
- start_time: Timestamp when processing began

TIMING TRACKING:
===============
Processing time is tracked from image upload through final recommendation,
displayed in the results summary for user transparency.
"""

import streamlit as st
import os
from typing import Optional
from dotenv import load_dotenv

# Import our services
from ocr_service import extract_ingredients_from_image, OCRError
from agent_research import research_multiple_ingredients, AgentResearchError
from recommendation_service import generate_recommendation, RecommendationError

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Ingredient Health Analyzer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for styling
st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
    }
    .recommendation-buy {
        background-color: #d4edda;
        border: 2px solid #28a745;
        border-radius: 10px;
        padding: 20px;
        margin: 20px 0;
    }
    .recommendation-dont-buy {
        background-color: #f8d7da;
        border: 2px solid #dc3545;
        border-radius: 10px;
        padding: 20px;
        margin: 20px 0;
    }
    .ingredient-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        background-color: #f9f9f9;
    }
    .score-high {
        color: #28a745;
        font-weight: bold;
    }
    .score-medium {
        color: #ffc107;
        font-weight: bold;
    }
    .score-low {
        color: #dc3545;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables"""
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'processing' not in st.session_state:
        st.session_state.processing = False
    if 'extracted_ingredients' not in st.session_state:
        st.session_state.extracted_ingredients = None
    if 'processing_time' not in st.session_state:
        st.session_state.processing_time = None
    if 'start_time' not in st.session_state:
        st.session_state.start_time = None


def validate_environment():
    """
    Validate that required environment variables are set and credentials are valid.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    required_vars = {
        'GCP_PROJECT_ID': 'Google Cloud Project ID',
        'TAVILY_API_KEY': 'Tavily API Key',
        'GOOGLE_APPLICATION_CREDENTIALS': 'Google Application Credentials path'
    }
    
    missing = []
    invalid = []
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            missing.append(f"- {var} ({description})")
        elif var == 'GOOGLE_APPLICATION_CREDENTIALS':
            # Validate credentials file exists
            import os.path
            if not os.path.isfile(value):
                invalid.append(f"- {var}: File not found at '{value}'")
    
    if missing or invalid:
        error_msg = "⚙️ Configuration Issues Detected:\n\n"
        
        if missing:
            error_msg += "Missing required environment variables:\n" + "\n".join(missing) + "\n\n"
        
        if invalid:
            error_msg += "Invalid configuration:\n" + "\n".join(invalid) + "\n\n"
        
        error_msg += "📖 Setup Instructions:\n"
        error_msg += "1. Copy .env.example to .env\n"
        error_msg += "2. Set GCP_PROJECT_ID to your Google Cloud project ID\n"
        error_msg += "3. Set TAVILY_API_KEY (get free key at https://tavily.com)\n"
        error_msg += "4. Set GOOGLE_APPLICATION_CREDENTIALS to path of your service account JSON file\n"
        error_msg += "5. Ensure the service account has 'Cloud Vision API User' and 'Vertex AI User' roles\n\n"
        error_msg += "For detailed setup instructions, see README.md"
        
        return False, error_msg
    
    return True, None


def display_header():
    """Display application header"""
    st.markdown("<div class='main-header'>", unsafe_allow_html=True)
    st.title("🔍 Ingredient Health Analyzer")
    st.markdown("Upload a product label image to analyze ingredients and get health recommendations")
    st.markdown("</div>", unsafe_allow_html=True)


def display_image_upload():
    """
    Display image upload widget with file type and size validation.
    
    Returns:
        Uploaded file object or None
    """
    st.subheader("📸 Upload Product Label")
    
    uploaded_file = st.file_uploader(
        "Choose an image of the ingredient label",
        type=['jpg', 'jpeg', 'png', 'heic'],
        help="Supported formats: JPG, JPEG, PNG, HEIC (Max size: 10MB)"
    )
    
    if uploaded_file is not None:
        # Validate file size (10MB limit)
        file_size_mb = uploaded_file.size / (1024 * 1024)
        if file_size_mb > 10:
            st.error(f"❌ File too large: {file_size_mb:.1f}MB. Maximum size is 10MB.")
            st.info("💡 Try compressing the image or taking a new photo at lower resolution.")
            return None
        
        # Validate file is not empty
        if uploaded_file.size == 0:
            st.error("❌ File is empty. Please upload a valid image.")
            return None
        
        # Display uploaded image
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            try:
                st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
            except Exception as e:
                st.error(f"❌ Could not display image: {str(e)}")
                st.info("The file may be corrupted. Please try uploading a different image.")
                return None
    
    return uploaded_file


def display_extracted_ingredients(ingredients: list):
    """
    Display extracted ingredients list for user verification.
    
    Args:
        ingredients: List of extracted ingredient names
    """
    st.subheader("📋 Extracted Ingredients")
    st.info(f"Found {len(ingredients)} ingredients. Verify the list below:")
    
    # Display as a formatted list
    cols = st.columns(2)
    for i, ingredient in enumerate(ingredients):
        col_idx = i % 2
        with cols[col_idx]:
            st.markdown(f"✓ {ingredient}")


def get_score_class(score: int) -> str:
    """
    Get CSS class for score display based on value.
    
    Args:
        score: Health score (0-100)
        
    Returns:
        CSS class name
    """
    if score >= 70:
        return "score-high"
    elif score >= 50:
        return "score-medium"
    else:
        return "score-low"


def display_recommendation(result: dict):
    """
    Display final recommendation with color-coded styling.
    
    Args:
        result: Recommendation result dictionary
    """
    recommendation = result['recommendation']
    reasoning = result['reasoning']
    score = result['score']
    summary = result['summary']
    processing_time = result.get('processing_time', 0)
    
    # Color-coded recommendation box
    if recommendation == "BUY":
        st.markdown(f"""
            <div class='recommendation-buy'>
                <h2 style='color: #28a745; margin: 0;'>✓ {recommendation}</h2>
                <p style='font-size: 1.1em; margin-top: 10px;'>{reasoning}</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div class='recommendation-dont-buy'>
                <h2 style='color: #dc3545; margin: 0;'>✗ {recommendation}</h2>
                <p style='font-size: 1.1em; margin-top: 10px;'>{reasoning}</p>
            </div>
        """, unsafe_allow_html=True)
    
    # Display summary statistics with processing time
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Overall Score", f"{score}/100")
    
    with col2:
        st.metric("Total Ingredients", summary['total_ingredients'])
    
    with col3:
        st.metric("Healthy", summary['healthy_count'], delta_color="normal")
    
    with col4:
        st.metric("Concerning", summary['concerning_count'], delta_color="inverse")
    
    with col5:
        st.metric("Processing Time", f"{processing_time}s")


def display_ingredient_details(ingredient_details: list):
    """
    Display detailed ingredient analysis in expandable sections.
    
    Args:
        ingredient_details: List of ingredient research results
    """
    st.subheader("🔬 Detailed Ingredient Analysis")
    
    # Sort by score (lowest first to highlight concerns)
    sorted_ingredients = sorted(ingredient_details, key=lambda x: x['score'])
    
    for ingredient in sorted_ingredients:
        name = ingredient['name']
        score = ingredient['score']
        summary = ingredient['summary']
        details = ingredient.get('details', {})
        
        score_class = get_score_class(score)
        
        # Create expander for each ingredient
        with st.expander(f"{name} - Score: {score}/100"):
            st.markdown(f"<p class='{score_class}'>Health Score: {score}/100</p>", unsafe_allow_html=True)
            
            st.markdown("**Research Summary:**")
            st.write(summary)
            
            # Display categorized details if available
            if details:
                if details.get('benefits'):
                    st.markdown("**✓ Benefits:**")
                    for benefit in details['benefits']:
                        st.markdown(f"- {benefit}")
                
                if details.get('concerns'):
                    st.markdown("**⚠ Concerns:**")
                    for concern in details['concerns']:
                        st.markdown(f"- {concern}")
                
                if details.get('facts'):
                    st.markdown("**ℹ Additional Information:**")
                    for fact in details['facts']:
                        st.markdown(f"- {fact}")


def display_error(error_message: str, error_type: str = "error"):
    """
    Display user-friendly error messages.
    
    Args:
        error_message: Error message to display
        error_type: Type of error (error, warning, info)
    """
    if error_type == "error":
        st.error(f"❌ {error_message}")
    elif error_type == "warning":
        st.warning(f"⚠ {error_message}")
    else:
        st.info(f"ℹ {error_message}")


def process_image(uploaded_file) -> Optional[dict]:
    """
    Process uploaded image through the complete analysis pipeline.
    
    Integrates all components:
    1. OCR service for ingredient extraction
    2. Agent research system for health analysis
    3. Recommendation generator for final decision
    
    Args:
        uploaded_file: Streamlit uploaded file object
        
    Returns:
        Analysis results dictionary or None if processing fails
    """
    import time
    
    # Start timing
    start_time = time.time()
    st.session_state.start_time = start_time
    
    try:
        # Validate uploaded file
        if uploaded_file is None:
            display_error("No file uploaded", "error")
            return None
        
        # Read image bytes with error handling
        try:
            image_bytes = uploaded_file.read()
            if not image_bytes or len(image_bytes) == 0:
                display_error("Uploaded file is empty or corrupted", "error")
                return None
        except Exception as e:
            display_error(f"Could not read uploaded file: {str(e)}", "error")
            return None
        
        # Step 1: OCR Processing - Wire image upload to OCR service
        st.subheader("🔄 Processing")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("Extracting ingredients from image...")
        progress_bar.progress(20)
        
        # Call OCR service
        try:
            ingredients = extract_ingredients_from_image(image_bytes)
        except OCRError as e:
            progress_bar.empty()
            status_text.empty()
            display_error(str(e), "error")
            st.info("💡 Tips for better results:\n- Ensure good lighting\n- Keep the label flat and in focus\n- Capture the entire ingredients section\n- Make sure text is clearly visible")
            return None
        
        # Handle empty ingredient list
        if not ingredients or len(ingredients) == 0:
            progress_bar.empty()
            status_text.empty()
            display_error("No ingredients could be extracted from the image", "warning")
            st.info("💡 Please ensure:\n- The image shows the ingredients list clearly\n- Text is readable and not blurry\n- The ingredients section is well-lit\n- Try taking a new photo closer to the label")
            return None
        
        # Store extracted ingredients in session state
        st.session_state.extracted_ingredients = ingredients
        
        progress_bar.progress(40)
        status_text.text(f"Found {len(ingredients)} ingredients!")
        
        # Display extracted ingredients for verification
        display_extracted_ingredients(ingredients)
        
        # Step 2: Research ingredients - Connect OCR results to agent research system
        status_text.text("Researching ingredient health impacts...")
        progress_bar.progress(50)
        
        # Create progress callback for ingredient research
        research_progress = st.empty()
        failed_ingredients = []
        
        def update_research_progress(current, total, ingredient):
            progress_pct = 50 + int((current / total) * 40)
            progress_bar.progress(progress_pct)
            research_progress.text(f"Researching {current}/{total}: {ingredient}")
        
        # Call agent research system with OCR results - graceful degradation on partial failures
        try:
            ingredient_results = research_multiple_ingredients(
                ingredients,
                progress_callback=update_research_progress
            )
            
            # Check if we got any results
            if not ingredient_results or len(ingredient_results) == 0:
                progress_bar.empty()
                status_text.empty()
                research_progress.empty()
                display_error("Could not research any ingredients", "error")
                st.info("This may be due to API rate limits or connectivity issues. Please try again in a moment.")
                return None
            
            # Check for failed ingredients (graceful degradation)
            successful_results = [r for r in ingredient_results if r.get('score', 0) > 0]
            failed_count = len(ingredient_results) - len(successful_results)
            
            if failed_count > 0:
                st.warning(f"⚠️ Could not fully research {failed_count} ingredient(s). Proceeding with available data.")
            
            # Need at least some successful results
            if len(successful_results) == 0:
                progress_bar.empty()
                status_text.empty()
                research_progress.empty()
                display_error("Research failed for all ingredients", "error")
                st.info("This may be due to API issues. Please try again later.")
                return None
                
        except AgentResearchError as e:
            progress_bar.empty()
            status_text.empty()
            research_progress.empty()
            display_error(f"Research system error: {str(e)}", "error")
            st.info("💡 Please check:\n- Your API credentials are valid\n- You have internet connectivity\n- API rate limits haven't been exceeded")
            return None
        
        progress_bar.progress(90)
        status_text.text("Generating recommendation...")
        
        # Step 3: Generate recommendation - Link research results to recommendation generator
        try:
            recommendation_result = generate_recommendation(ingredient_results)
        except RecommendationError as e:
            progress_bar.empty()
            status_text.empty()
            research_progress.empty()
            display_error(f"Could not generate recommendation: {str(e)}", "error")
            return None
        
        # Calculate processing time
        end_time = time.time()
        processing_time = round(end_time - start_time, 2)
        st.session_state.processing_time = processing_time
        
        # Add timing to result
        recommendation_result['processing_time'] = processing_time
        
        progress_bar.progress(100)
        status_text.text(f"✓ Analysis complete in {processing_time}s!")
        
        # Clear progress indicators after a moment
        time.sleep(1)
        progress_bar.empty()
        status_text.empty()
        research_progress.empty()
        
        return recommendation_result
        
    except Exception as e:
        # Catch-all for unexpected errors
        display_error(f"Unexpected error during processing: {str(e)}", "error")
        st.error("An unexpected error occurred. Please try again or contact support if the issue persists.")
        
        # Log error details for debugging
        import traceback
        st.expander("🔍 Error Details (for debugging)").code(traceback.format_exc())
        
        return None


def main():
    """Main application flow"""
    # Initialize session state
    initialize_session_state()
    
    # Display header
    display_header()
    
    # Validate environment
    is_valid, error_msg = validate_environment()
    if not is_valid:
        st.error("⚙️ Configuration Error")
        st.code(error_msg)
        st.info("Please refer to the README.md for setup instructions.")
        return
    
    # Image upload section
    uploaded_file = display_image_upload()
    
    # Process button
    if uploaded_file is not None:
        if st.button("🔍 Analyze Ingredients", type="primary", use_container_width=True):
            # Set processing state and clear previous results
            st.session_state.processing = True
            st.session_state.analysis_results = None
            st.session_state.processing_time = None
            
            # Process the image through integrated pipeline
            with st.spinner("Processing..."):
                result = process_image(uploaded_file)
                
                if result:
                    # Store results in session state for persistence
                    st.session_state.analysis_results = result
            
            st.session_state.processing = False
    
    # Display results if available in session state
    if st.session_state.analysis_results:
        st.markdown("---")
        st.header("📊 Analysis Results")
        
        result = st.session_state.analysis_results
        
        # Display recommendation with timing
        display_recommendation(result)
        
        # Display detailed ingredient analysis
        st.markdown("---")
        display_ingredient_details(result['ingredient_details'])
        
        # Option to analyze another product (clears session state)
        if st.button("🔄 Analyze Another Product"):
            st.session_state.analysis_results = None
            st.session_state.extracted_ingredients = None
            st.session_state.processing_time = None
            st.session_state.start_time = None
            st.rerun()


if __name__ == "__main__":
    main()
