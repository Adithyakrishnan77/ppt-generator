import streamlit as st
from streamlit_lottie import st_lottie
import json
import threading
import time
from io import BytesIO
from pathlib import Path
import tempfile
import os

# Import our production backend
from backend import (
    generate_presentation, 
    PPTGenerationError, 
    GenerationStopped,
    validate_template,
    cleanup_temp_file
)

# --------------------------
# Page Configuration
# --------------------------

st.set_page_config(
    page_title="AI PPT Generator Pro",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    /* Main title styling */
    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        color: #1e3a8a;
        margin-bottom: 1rem;
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* Button styling */
    .stButton > button {
        width: 100%;
        height: 3rem;
        font-size: 1.1rem;
        font-weight: 600;
        border-radius: 0.5rem;
        border: none;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.2);
    }
    
    /* Stop button specific styling */
    .stop-button {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important;
    }
    
    /* Status messages */
    .status-info {
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #3b82f6;
        background-color: inear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        margin: 1rem 0;
    }
    
    .status-error {
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ef4444;
        background-color: #000204;
        margin: 1rem 0;
    }
    
    /* Template selection */
    .template-option {
        padding: 0.75rem;
        margin: 0.5rem 0;
        border-radius: 0.5rem;
        border: 2px solid #e5e7eb;
        background-color: #f9fafb;
        transition: all 0.3s ease;
    }
    
    .template-option:hover {
        border-color: #3b82f6;
        background-color: #eff6ff;
    }
</style>
""", unsafe_allow_html=True)

# --------------------------
# Session State Initialization
# --------------------------

def init_session_state():
    """Initialize session state variables"""
    defaults = {
        'generation_active': False,
        'stop_event': None,
        'generated_file': None,
        'generation_metadata': None,
        'topic_input': '',
        'error_message': None,
        'success_message': None
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# --------------------------
# UI Components
# --------------------------

def render_header():
    """Render application header"""
    st.markdown('<h1 class="main-title">🎯 AI PowerPoint Generator Pro</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p style="text-align: center; color: #6b7280; font-size: 1.1rem; margin-bottom: 2rem;">'
        'Create professional presentations instantly with AI-powered content generation'
        '</p>', 
        unsafe_allow_html=True
    )

def render_sidebar():
    """Render sidebar with formatting options"""
    st.sidebar.header("🎨 Formatting Options")
    
    # Font selection
    available_fonts = [
        "Arial", "Calibri", "Times New Roman", "Verdana",
        "Tahoma", "Courier New", "Georgia", "Comic Sans MS"
    ]
    font_name = st.sidebar.selectbox(
        "Font Family", 
        available_fonts, 
        index=1,
        help="Choose the font for your presentation content"
    )
    
    # Font size selection
    available_sizes = [8, 9, 10, 11, 12, 14, 16, 18, 20, 24, 28, 32, 36, 48, 72]
    font_size = st.sidebar.selectbox(
        "Font Size", 
        available_sizes, 
        index=4,
        help="Select the base font size for content"
    )
    
    st.sidebar.divider()
    
    # Template selection
    st.sidebar.header("📋 Template Options")
    
    template_option = st.sidebar.radio(
        "Choose a template:",
        ["Default", "Nura", "Soxo", "Upload Custom"],
        help="Select a presentation template"
    )
    
    template_path = None
    uploaded_template = None
    
    if template_option == "Nura":
        template_path = "template - nura (2).pptx"
        if not validate_template(template_path):
            st.sidebar.error("⚠️ Nura template file not found")
            template_path = None
    elif template_option == "Soxo":
        template_path = "Soxo template .pptx"
        if not validate_template(template_path):
            st.sidebar.error("⚠️ Soxo template file not found")
            template_path = None
    elif template_option == "Upload Custom":
        uploaded_template = st.sidebar.file_uploader(
            "Upload your PPTX template",
            type=["pptx"],
            help="Upload a custom PowerPoint template file"
        )
        
        if uploaded_template:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(suffix='.pptx', delete=False) as tmp_file:
                tmp_file.write(uploaded_template.getbuffer())
                template_path = tmp_file.name
    
    return font_name, font_size, template_path

def render_topic_input():
    """Render topic input section"""
    st.subheader("📝 What would you like to present about?")
    
    topic = st.text_area(
        label="Enter your topic or detailed instructions:",
        placeholder='e.g., "Create a comprehensive presentation on Machine Learning fundamentals including supervised learning, unsupervised learning, neural networks, and practical applications in healthcare"',
        height=120,
        key="topic_input_field",
        help="Be specific and detailed for better results. Include any specific requirements, audience level, or focus areas."
    )
    
    # Character count
    char_count = len(topic) if topic else 0
    color = "green" if 50 <= char_count <= 500 else "orange" if char_count > 0 else "gray"
    st.markdown(
        f'<p style="color: {color}; font-size: 0.9rem; text-align: right; margin-top: -10px;">'
        f'Characters: {char_count} (recommended: 50-500)</p>',
        unsafe_allow_html=True
    )
    
    return topic

def load_lottie_animation():
    """Load loading animation"""
    try:
        lottie_path = Path("Ripple loading animation.json")
        if lottie_path.exists():
            with open(lottie_path, "r") as f:
                return json.load(f)
    except Exception as e:
        st.warning(f"Could not load animation: {e}")
    return None

def render_status_messages():
    """Render status messages"""
    if st.session_state.error_message:
        st.markdown(
            f'<div class="status-error">❌ {st.session_state.error_message}</div>',
            unsafe_allow_html=True
        )
        st.session_state.error_message = None
    
    if st.session_state.success_message:
        st.markdown(
            f'<div class="status-info">✅ {st.session_state.success_message}</div>',
            unsafe_allow_html=True
        )
        st.session_state.success_message = None

# --------------------------
# Generation Logic
# --------------------------

def start_generation(topic, template_path, font_name, font_size):
    """Start the presentation generation process with improved state management"""
    
    # Create stop event and result container
    stop_event = threading.Event()
    result_container = {'status': 'generating', 'file_path': None, 'metadata': None, 'error': None}
    
    st.session_state.stop_event = stop_event
    st.session_state.generation_active = True
    st.session_state.generation_start_time = time.time()
    st.session_state.result_container = result_container
    
    def generation_thread():
        """Background thread for generation with result container"""
        try:
            file_path, metadata = generate_presentation(
                topic=topic,
                template_path=template_path,
                font_name=font_name,
                font_size=font_size,
                stop_event=stop_event
            )
            
            if not stop_event.is_set():
                # Update result container instead of session state directly
                result_container['status'] = 'completed'
                result_container['file_path'] = file_path
                result_container['metadata'] = metadata
                result_container['message'] = f"Successfully generated presentation!"
            else:
                result_container['status'] = 'stopped'
                result_container['message'] = 'Generation stopped by user'
                if file_path and os.path.exists(file_path):
                    cleanup_temp_file(file_path)
            
        except GenerationStopped:
            result_container['status'] = 'stopped'
            result_container['message'] = 'Generation stopped successfully'
        except PPTGenerationError as e:
            if not stop_event.is_set():
                result_container['status'] = 'error'
                result_container['error'] = str(e)
        except Exception as e:
            if not stop_event.is_set():
                result_container['status'] = 'error'
                result_container['error'] = f"Unexpected error: {str(e)}"
    
    # Start generation in background thread
    thread = threading.Thread(target=generation_thread, daemon=True)
    thread.start()

def stop_generation():
    """Stop the current generation process"""
    if st.session_state.stop_event:
        st.session_state.stop_event.set()
    
    # Update result container if it exists
    if hasattr(st.session_state, 'result_container'):
        st.session_state.result_container['status'] = 'stopped'
        st.session_state.result_container['message'] = 'Generation stopped by user'
    
    # Force stop the generation state
    st.session_state.generation_active = False
    st.session_state.stop_event = None
    
    # Clear timing
    if 'generation_start_time' in st.session_state:
        del st.session_state.generation_start_time
    
    st.session_state.success_message = "Generation stopped successfully"

# --------------------------
# Main Application
# --------------------------

def main():
    """Main application function"""
    
    # Initialize session state
    init_session_state()
    
    # Render header
    render_header()
    
    # Render sidebar and get options
    font_name, font_size, template_path = render_sidebar()
    
    # Render main content
    topic = render_topic_input()
    
    # Render status messages
    render_status_messages()
    
    # Action buttons
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if not st.session_state.generation_active:
            if st.button("🚀 Generate Presentation", type="primary", key="generate_btn"):
                if topic.strip():
                    start_generation(topic, template_path, font_name, font_size)
                    st.rerun()
                else:
                    st.session_state.error_message = "Please enter a topic before generating"
                    st.rerun()
        else:
            st.button("⏳ Generating...", disabled=True, key="generating_btn")
    
    with col2:
        if st.session_state.generation_active:
            if st.button("⏹️ Stop", key="stop_btn", help="Stop generation"):
                stop_generation()
                st.rerun()
    
    # Show loading animation during generation
    if st.session_state.generation_active:
        st.markdown("### 🔄 Generating your presentation...")
        st.markdown("This may take 1-3 minutes depending on the complexity of your topic.")
        
        # Add manual refresh button for stuck states
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("🔄 Refresh", key="manual_refresh", help="Click if generation seems stuck"):
                st.rerun()
        
        # Load and display animation
        lottie_animation = load_lottie_animation()
        if lottie_animation:
            st_lottie(lottie_animation, height=200, key="loading_animation")
        else:
            # Fallback progress bar
            progress_bar = st.progress(0)
            for i in range(100):
                if not st.session_state.generation_active:
                    break
                progress_bar.progress(i + 1)
                time.sleep(0.1)
    
    # Download section - METADATA SECTION REMOVED
    if st.session_state.generated_file and os.path.exists(st.session_state.generated_file):
        st.divider()
        st.subheader("📥 Download Your Presentation")
        # topic = st.session_state.get("topic", "Presentation")
        import re

        safe_topic = re.sub(r'[^a-zA-Z0-9_-]', '_', topic.strip()) or "Presentation"

        # Download button directly without metadata display
        try:
            with open(st.session_state.generated_file, "rb") as file:
                file_data = file.read()
            
            # st.download_button(
            #     label="📥 Download PowerPoint",
            #     data=file_data,
            #     file_name=f"presentation_{int(time.time())}.pptx",
            #     mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            #     key="download_presentation",
            #     help="Click to download your generated presentation"
            # )
            st.download_button(
                label="📥 Download PowerPoint",
                data=file_data,
                file_name=f"{safe_topic}.pptx",   # ✅ name based on topic
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                key="download_presentation",
                help="Click to download your generated presentation"
            )
            
            # Cleanup option
            if st.button("🗑️ Clear Generated File", key="cleanup_btn"):
                cleanup_temp_file(st.session_state.generated_file)
                st.session_state.generated_file = None
                st.session_state.generation_metadata = None
                st.session_state.success_message = "File cleared successfully"
                st.rerun()
                
        except Exception as e:
            st.error(f"Error preparing download: {e}")
    
    # Footer with tips
    st.divider()
    with st.expander("💡 Tips for Better Presentations"):
        st.markdown("""
        **For best results:**
        - Be specific about your topic and target audience
        - Mention desired number of slides (e.g., "create 10 slides about...")
        - Include any specific requirements or focus areas
        - For technical topics, mention if you want code examples or equations
        - Specify the presentation context (meeting, training, academic, etc.)
        
        **Example good prompts:**
        - "Create a 15-slide executive presentation on digital transformation strategies for manufacturing companies"
        - "Generate training materials on Python data analysis with pandas, including code examples and exercises"
        - "Develop a comprehensive overview of renewable energy technologies for a university-level environmental science course"
        """)
    
    # Auto-refresh during generation with improved state checking
    if st.session_state.generation_active:
        # Check result container for updates
        if hasattr(st.session_state, 'result_container'):
            result = st.session_state.result_container
            
            if result['status'] == 'completed':
                st.session_state.generated_file = result['file_path']
                st.session_state.generation_metadata = result['metadata']
                st.session_state.success_message = result['message']
                st.session_state.generation_active = False
                st.rerun()
            elif result['status'] == 'stopped':
                st.session_state.success_message = result.get('message', 'Generation stopped')
                st.session_state.generation_active = False
                st.rerun()
            elif result['status'] == 'error':
                st.session_state.error_message = result.get('error', 'Unknown error')
                st.session_state.generation_active = False
                st.rerun()
        
        # Timeout protection - 6 minutes
        if 'generation_start_time' not in st.session_state:
            st.session_state.generation_start_time = time.time()
        
        elapsed_time = time.time() - st.session_state.generation_start_time
        if elapsed_time > 360:  # 6 minutes timeout
            st.session_state.error_message = "Generation timed out after 6 minutes. Please try again with a shorter topic."
            stop_generation()
            st.rerun()
        else:
            time.sleep(1.5)  # Check every 1.5 seconds
            st.rerun()
    else:
        # Clear start time when not generating
        if 'generation_start_time' in st.session_state:
            del st.session_state.generation_start_time

if __name__ == "__main__":
    main()