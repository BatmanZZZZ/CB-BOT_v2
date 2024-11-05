import re
import os
import time
import logging
from langchain.callbacks.base import BaseCallbackHandler
from Chatbot_new import *
from streamlit_chat import message
import streamlit as st
from langchain.callbacks import get_openai_callback

if not os.path.isdir('Logs'):
    os.makedirs('Logs')
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        filename='Logs/Queries.log'  # Specify the log file name and path
    )


class StreamHandler(BaseCallbackHandler):
    def __init__(self, container, initial_text=" ", display_method='markdown'):
        self.container = container
        self.text = initial_text
        self.display_method = display_method

    def on_llm_new_token(self, token: str, **kwargs) -> None:

        self.text += token

        display_function = getattr(self.container, self.display_method, None)
        if display_function is not None:
            self.container.markdown(self.text + "▌")
        else:
            raise ValueError(f"Invalid display_method: {self.display_method}")


if "model_initialized" not in st.session_state:
    # st.write("Calling again")
    st.session_state["model_initialized"] = True
    bot = ChatbotResponse()
    st.session_state["bot"] = bot
else:
    # st.write("In else modal already loaded")
    bot = st.session_state["bot"]
st.title("Central Bank Chatbot")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
if "disabled" not in st.session_state:
    st.session_state["disabled"] = False


def disable():
    st.session_state["disabled"] = True


# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input

if prompt := st.chat_input("Query"):
    start_time = time.time()
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        # Display assistant response in chat message container

        stream_container = st.empty()
        stream_handler = StreamHandler(stream_container, display_method='write')

        message_placeholder = stream_container
        bot.set_stream_handler(stream_handler)
        logging.info(f"\nACTUAL QUERY : \n{prompt}")
        
        # Add spinner while waiting for the response
        with st.spinner("Thinking..."):
            with get_openai_callback() as cb:
                chain, context_dict, dest, ref_query = bot.get_query_response(prompt)
                context = context_dict['input_documents']
                response = chain.run(context_dict)
                st.write(time.time() - start_time)
                with st.sidebar:
                    st.write(f"{ref_query}")
                    st.write(f"{dest}")
                    st.write(f"Total Tokens: {cb.total_tokens}")
                    st.write(f"Prompt Tokens: {cb.prompt_tokens}")
                    st.write(f"Completion Tokens: {cb.completion_tokens}")
                    st.write(f"No of documents sent = {len(context)}")
                    st.write("# Sources Include")
                    st.write(context)
        logging.info(f"\nCONTEXT :  \n{context}")
        logging.info(f"\nBOT RESPONSE : \n{response}")
        st.session_state.messages.append({"role": "assistant", "content": response.replace("▌", '')})

