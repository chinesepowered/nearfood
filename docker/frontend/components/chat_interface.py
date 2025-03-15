import streamlit as st
from typing import List, Dict, Any, Callable

def render_message(message: Dict[str, Any]):
    """Render a chat message"""
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

def render_chat_history(messages: List[Dict[str, Any]]):
    """Render the full chat history"""
    for message in messages:
        render_message(message)

def chat_input_handler(prompt: str, on_submit: Callable[[str], Dict[str, Any]]):
    """Handle chat input and submission"""
    if not prompt:
        return
    
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get bot response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")
        
        # Get response from callback
        response = on_submit(prompt)
        
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
            
            # Add assistant message to chat history
            st.session_state.messages.append({"role": "assistant", "content": full_response})

def clear_chat_button():
    """Button to clear chat history"""
    if st.button("Clear Chat", type="secondary"):
        st.session_state.messages = []
        st.rerun()