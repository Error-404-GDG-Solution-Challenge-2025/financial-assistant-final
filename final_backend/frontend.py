# frontend.py
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
# from langchain.agents import ConversationalChatAgent, AgentExecutor # Not used directly now
from langchain.memory import ConversationBufferMemory
# Use FileChatMessageHistory for persistence
from langchain_community.chat_message_histories import FileChatMessageHistory
# Keep for potential future use
from langchain_community.callbacks import StreamlitCallbackHandler
from langchain_core.runnables import RunnableConfig  # Keep for potential future use
from termcolor import colored
from langchain_core.messages import SystemMessage, HumanMessage

# Import the main processing function from run.py
from run import process_query_flow
import os

# --- Configuration ---
CHAT_HISTORY_FILE = "chat_history.json"  # File to store chat history

st.set_page_config(page_title="Financial Assistant", page_icon="💰")
st.title("💰 Financial Assistant")

# --- State Initialization ---

# Initialize chat history using FileChatMessageHistory for persistence
# Use session state to ensure it's loaded once per session
if "chat_history" not in st.session_state:
    st.session_state.chat_history = FileChatMessageHistory(CHAT_HISTORY_FILE)

# Initialize ConversationBufferMemory with the file history
# Use session state to ensure it's loaded once per session
if "memory" not in st.session_state:
    st.session_state.memory = ConversationBufferMemory(
        chat_memory=st.session_state.chat_history,
        return_messages=True,
        memory_key="chat_history",  # Matches the key expected by some Langchain components
        output_key="output",  # Standard output key
        input_key="input"  # Define the input key explicitly
    )

# Initialize message list for display from memory
# This ensures UI consistency even if the file changes externally during session
if "messages" not in st.session_state:
    # Load messages from memory, which in turn loads from the file
    st.session_state.messages = st.session_state.memory.load_memory_variables({})[
        'chat_history']
    # Add initial message if history is empty
    if not st.session_state.messages:
        st.session_state.messages = [
            SystemMessage(content="How can I help you?")]
        # Save this initial state back to memory/file
        st.session_state.memory.save_context({"input": "System initialization"}, {
                                             "output": "How can I help you?"})  # Provide a dummy input


# --- Sidebar ---
st.sidebar.title("Options")

# Reset Button - Clears memory, file, and UI state
if st.sidebar.button("Reset Chat History"):
    # Clears buffer and underlying FileChatMessageHistory
    st.session_state.memory.clear()
    st.session_state.messages = [SystemMessage(
        content="Chat history cleared. How can I help you?")]
    # No need to manually clear file, memory.clear() handles it
    st.rerun()  # Rerun the app to reflect the cleared state

# Deep Research Toggle
# Use st.session_state to keep the toggle's value across reruns
if 'deep_search_active' not in st.session_state:
    st.session_state.deep_search_active = False

st.session_state.deep_search_active = st.sidebar.checkbox(
    "Enable Deep Research Mode",
    value=st.session_state.deep_search_active,
    key="deep_search_toggle"  # Assign key for stability
)
st.sidebar.caption(
    "Deep research takes longer but provides more in-depth analysis.")


# --- Chat Interface ---

# Display existing messages from st.session_state.messages
avatars = {"human": "user", "ai": "assistant",
           "system": "assistant"}  # Map types to avatars
for msg in st.session_state.messages:
    msg_type = msg.type  # 'human', 'ai', 'system'
    if msg_type in avatars:
        with st.chat_message(avatars[msg_type]):
            st.markdown(msg.content)  # Use markdown for better formatting

# Handle new user input
if prompt := st.chat_input("Ask a financial question..."):
    # Add user message to state and display it
    st.session_state.messages.append(HumanMessage(content=prompt))
    with st.chat_message("user"):
        st.markdown(prompt)
    print(colored(f"Prompt: {prompt}", "green"))
    # Process the input using the backend function
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")
        try:
            # Pass the current memory object and deep search state
            response_content = process_query_flow(
                prompt,
                st.session_state.memory,  # Pass the session's memory object
                st.session_state.deep_search_active  # Pass the toggle state
            )
            message_placeholder.markdown(response_content)
            # Add AI response to state
            st.session_state.messages.append(SystemMessage(
                content=response_content))  # Use SystemMessage or AIMessage

            # Crucially, save the context (user input + AI output) back to memory
            # This updates the buffer and persists to the file via FileChatMessageHistory
            st.session_state.memory.save_context(
                {"input": prompt}, {"output": response_content})

        except Exception as e:
            error_message = f"Sorry, an error occurred: {str(e)}"
            message_placeholder.error(error_message)
            st.session_state.messages.append(
                SystemMessage(content=error_message))
            # Save error context
            st.session_state.memory.save_context(
                {"input": prompt}, {"output": error_message})
            print(colored(f"Frontend Error: {e}", "red"))
            import traceback
            traceback.print_exc()  # Log full traceback to console for debugging

    # No need to manually rerun, Streamlit handles updates based on state changes implicitly
    # unless explicit rerun is needed after complex state manipulation.
