import streamlit as st
from openai import OpenAI
import time
import os
import json


INITIAL_MSG = "I want to enroll my Quest device"


# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({"role": "user", "content": INITIAL_MSG})

if 'show_intro_button' not in st.session_state:
    st.session_state.show_intro_button = True

if 'first_assistant_run_finished' not in st.session_state:
    st.session_state.first_assistant_run_finished = False

if 'assistant_finished' not in st.session_state:
    st.session_state.assistant_finished = False

if not st.session_state.show_intro_button and "client" not in st.session_state:
    st.session_state['client'] = \
        OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

if not st.session_state.show_intro_button and "assistant" not in st.session_state:
    st.session_state['assistant'] = \
        st.session_state.client.beta.assistants.retrieve('asst_pArjrUQzOBeE34nlGc9vz68y')

if not st.session_state.show_intro_button and "thread" not in st.session_state:
    st.session_state["thread"] = \
        st.session_state['client'].beta.threads.create()


def on_intro_button_click():
    st.session_state.show_intro_button = False

def assistant_run(prompt):
    client = st.session_state.client

     # Display assistant response in chat message container
    with st.chat_message("assistant"):
        with st.spinner('Assistant is thinking...'):
            message = client.beta.threads.messages.create(
                thread_id=st.session_state["thread"].id,
                role="user",
                content=prompt,
            )
            run = client.beta.threads.runs.create(
                thread_id=st.session_state["thread"].id,
                assistant_id=st.session_state["assistant"].id,
            )
            while run.status == "queued" or run.status == "in_progress":
                run = client.beta.threads.runs.retrieve(
                    thread_id=st.session_state["thread"].id,
                    run_id=run.id,
                )
                time.sleep(0.5)
            if run.required_action is None:
                messages = client.beta.threads.messages.list(
                    thread_id=st.session_state["thread"].id, order="asc", after=message.id
                )
                for message in messages.data:
                    for content in message.content:
                        st.markdown(content.text.value)
                        st.session_state.messages.append({"role": "assistant", "content": content.text.value})
            else:
                assistant_run_results_fn = \
                    run.required_action.submit_tool_outputs.tool_calls[0]
                assistant_run_results = assistant_run_results_fn.function.arguments
                final_message = \
                    "Assistant finished running.\n\nDevice will be configured using the following spec:\n```\n{}\n```".format(
                        assistant_run_results
                    )
                st.markdown(final_message)
                st.session_state.messages.append({"role": "assistant", "content": final_message})
                st.session_state.assistant_finished = True


if st.session_state.show_intro_button:
    st.button('Click to start AI Device Enrollment Demo', on_click=on_intro_button_click)

if not st.session_state.show_intro_button:
    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if not st.session_state.first_assistant_run_finished:
        assistant_run(INITIAL_MSG)
        st.session_state.first_assistant_run_finished = True

    if st.session_state.assistant_finished:
        pass
    else:
        # Accept user input
        if prompt := st.chat_input("Send your message to Admin Assistant"):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            # Display user message in chat message container
            with st.chat_message("user"):
                st.markdown(prompt)

            assistant_run(prompt)
