import streamlit as st
from langgraph_database import chatbot, get_all_threads
from langchain_core.messages import HumanMessage
import uuid

# ******************** Utility functions *******************

def generate_thread_id():
    thread_id = uuid.uuid4()
    return thread_id

def reset_chat():
    st.session_state['thread_id'] = generate_thread_id()
    add_thread(st.session_state['thread_id'])
    st.session_state['message_history'] = []

def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

def load_conversation(thread_id):
    state = chatbot.get_state(
        config = {
            'configurable': {
                'thread_id': thread_id
                }
            }
        )
    
    messages = state.values.get('messages', [])

    message_history = []

    for message in messages:
        if isinstance(message, HumanMessage):
            message_history.append({"role": "user", "content": message.content})
        else:
            message_history.append({"role": "assistant", "content": message.content})

    return message_history
 

# ******************** Session Setup *******************

# st.session_state -> dict -> messages are not erase on new ipnput until manual refresh of page
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = get_all_threads()

add_thread(st.session_state['thread_id'])


# ******************* Sidebar UI *******************

st.sidebar.title("LangGraph Chatbot")
if st.sidebar.button("New Chat"):
    reset_chat()
    st.rerun()

st.sidebar.header("Chat History")

has_chat_history = False

for thread_id in st.session_state['chat_threads']:

    messages = load_conversation(thread_id)

    if messages: 

        has_chat_history = True

        first_message = messages[0]['content']

        chat_title = first_message[:30]

        if len(first_message) > 30:
            chat_title += "..."

        if st.sidebar.button(
            chat_title,
            key=f"thread_{thread_id}"
            ):

            st.session_state['thread_id'] = thread_id

            # Load conversation into Streamlit history
            st.session_state['message_history'] = load_conversation(thread_id)

            st.rerun()

if not has_chat_history:
    st.sidebar.text("No chat history")

# ******************* Main Chat UI *******************
for message in st.session_state['message_history']:
    with st.chat_message(message["role"]):
        st.text(message["content"])

    
user_input = st.chat_input("Type your message here...")

if user_input:
    
    st.session_state['message_history'].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.text(user_input)

    CONFIG = {'configurable' : {'thread_id': st.session_state['thread_id']}} 
    
    with st.chat_message("assistant"):
        ai_message  = st.write_stream(
            message_chunk.content for message_chunk, metadata in chatbot.stream(
                {'messages' : [HumanMessage(content=user_input)]},
                config = CONFIG,
                stream_mode = "messages"
            )
        )

    st.session_state['message_history'].append({"role": "assistant", "content": ai_message})
    
