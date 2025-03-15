import streamlit as st
import requests
import json
import os
from datetime import datetime
from typing import List, Dict, Any

# API configuration
API_URL = os.environ.get("API_URL", "http://backend:8000")

# Page configuration
st.set_page_config(
    page_title="Food Event Chatbot",
    page_icon="🍕",
    layout="wide"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "processing_status" not in st.session_state:
    st.session_state.processing_status = None

if "api_status" not in st.session_state:
    st.session_state.api_status = None

# Functions
def check_api_status():
    """Check API status"""
    try:
        response = requests.get(f"{API_URL}/status")
        if response.status_code == 200:
            return response.json()
        return {"error": f"API returned status code {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def process_calendar(ical_url: str, force_reprocess: bool = False):
    """Process calendar data"""
    try:
        response = requests.post(
            f"{API_URL}/process",
            json={"ical_url": ical_url, "force_reprocess": force_reprocess}
        )
        
        if response.status_code == 200:
            return response.json()
        
        return {"status": "error", "message": f"API returned status code {response.status_code}"}
    
    except Exception as e:
        return {"status": "error", "message": str(e)}

def query_chatbot(question: str):
    """Query chatbot"""
    # Format chat history
    chat_history = []
    for msg in st.session_state.messages:
        chat_history.append({
            "message": msg["content"],
            "is_user": msg["role"] == "user"
        })
    
    try:
        response = requests.post(
            f"{API_URL}/query",
            json={"question": question, "chat_history": {"messages": chat_history}}
        )
        
        if response.status_code == 200:
            return response.json()
        
        return {
            "status": "error", 
            "answer": f"Error: API returned status code {response.status_code}",
            "metadata": {}
        }
    
    except Exception as e:
        return {"status": "error", "answer": f"Error: {str(e)}", "metadata": {}}

# UI Components
def render_sidebar():
    """Render sidebar"""
    st.sidebar.title("🍕 Food Event Chatbot")
    
    # Configuration section
    st.sidebar.header("Calendar Configuration")
    
    ical_url = st.sidebar.text_input(
        "iCal URL",
        value="https://api.lu.ma/ics/get?entity=discover&id=discplace-BDj7GNbGlsF7Cka",
        help="URL to the iCal file to process"
    )
    
    # Process calendar button
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("Process Calendar", type="primary", use_container_width=True):
            with st.spinner("Processing calendar..."):
                result = process_calendar(ical_url)
                st.session_state.processing_status = result
    
    with col2:
        if st.button("Force Reprocess", type="secondary", use_container_width=True):
            with st.spinner("Reprocessing calendar..."):
                result = process_calendar(ical_url, force_reprocess=True)
                st.session_state.processing_status = result
    
    # Display processing status
    if st.session_state.processing_status:
        status = st.session_state.processing_status.get("status", "unknown")
        message = st.session_state.processing_status.get("message", "")
        
        if status == "processing":
            st.sidebar.info(f"Status: {status}\n{message}")
        elif status == "success":
            st.sidebar.success(f"Status: {status}\n{message}")
        elif status == "skipped":
            st.sidebar.warning(f"Status: {status}\n{message}")
        else:
            st.sidebar.error(f"Status: {status}\n{message}")
    
    # API Status
    st.sidebar.header("System Status")
    if st.sidebar.button("Check API Status", type="secondary"):
        st.session_state.api_status = check_api_status()
    
    if st.session_state.api_status:
        if "error" in st.session_state.api_status:
            st.sidebar.error(f"API Error: {st.session_state.api_status['error']}")
        else:
            processed = st.session_state.api_status.get("processed", False)
            status_color = "🟢" if processed else "🟠"
            
            st.sidebar.markdown(f"""
            **API Status:** {status_color} {'Ready' if processed else 'Not Ready'}
            
            **Data:**
            - Calendar Data: {'✅' if st.session_state.api_status.get('ical_data_exists', False) else '❌'}
            - Event Summaries: {'✅' if st.session_state.api_status.get('summary_data_exists', False) else '❌'}
            
            {f"**Last Processed:** {st.session_state.api_status.get('processed_timestamp', '')}" if processed else ""}
            """)
    
    # About section
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    **About**
    
    This chatbot helps you find events with free food. Upload calendar data first, then ask questions about events.
    """)

def render_chat_interface():
    """Render chat interface"""
    st.title("Food Event Chatbot")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about food events..."):
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get response from API
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("Thinking...")
            
            # Query API
            response = query_chatbot(prompt)
            
            if response.get("status") == "error":
                message_placeholder.error(response.get("answer", "An error occurred"))
            else:
                answer = response.get("answer", "No answer provided")
                sources = response.get("sources", [])
                
                # Format answer with sources if available
                full_response = answer
                
                if sources:
                    full_response += "\n\n**Sources:**\n"
                    for i, source in enumerate(sources, 1):
                        source_title = source.get("title", f"Source {i}")
                        source_url = source.get("url", "#")
                        full_response += f"{i}. [{source_title}]({source_url})\n"
                
                message_placeholder.markdown(full_response)
                
                # Add assistant message to chat
                st.session_state.messages.append({"role": "assistant", "content": full_response})

# Main function
def main():
    render_sidebar()
    
    # Check if API is ready
    api_status = check_api_status()
    if "error" in api_status:
        st.error(f"Cannot connect to API: {api_status['error']}")
        st.info("Make sure the backend service is running")
        return
    
    # Check if data has been processed
    if not api_status.get("processed", False):
        st.warning("Calendar data has not been processed yet. Please process the calendar data first.")
        
        # Show sample questions
        st.markdown("""
        ## Getting Started
        
        1. Enter the iCal URL in the sidebar (default is provided)
        2. Click "Process Calendar" button
        3. Wait for processing to complete (this may take a few minutes)
        4. Come back here to chat about food events
        """)
        return
    
    # Render chat interface
    render_chat_interface()

if __name__ == "__main__":
    main()