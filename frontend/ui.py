#ui.py
import streamlit as st
import requests
import time
import json

API_URL = "https://academic-agent-ycnm.onrender.com/ask"

st.set_page_config(page_title="Academic Agent", layout="centered")

# ---------- HEADER + MODE ----------
col1, col2 = st.columns([6, 2])

with col1:
    st.title("Academic Agent")

with col2:
    mode = st.selectbox("Mode", ["Auto", "Math", "Conversion", "Concept"])

# ---------- SESSION ----------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------- CONTROLS ----------
col3, col4 = st.columns([1, 1])

with col3:
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

with col4:
    if st.session_state.messages:
        st.download_button(
            "Download Chat",
            json.dumps(st.session_state.messages, indent=2),
            file_name="chat_history.json"
        )

# ---------- DISPLAY CHAT ----------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "meta" in msg:
            st.caption(msg["meta"])

# ---------- INPUT ----------
if prompt := st.chat_input("Ask something..."):

    # Apply mode prefix
    if mode == "Math":
        prompt = f"Solve mathematically: {prompt}"
    elif mode == "Conversion":
        prompt = f"Convert units: {prompt}"
    elif mode == "Concept":
        prompt = f"Explain concept: {prompt}"

    # Save user message
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    # ---------- API CALL ----------
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):

            start_time = time.time()

            try:
                res = requests.post(API_URL, json={"input": prompt}, timeout=60)
                data = res.json()

                reply = str(data.get("response", data.get("error", "No response")))
                
                # Optional tool info (if backend supports)
                tool_used = data.get("tool_used", "LLM")

            except Exception as e:
                reply = f"Error: {str(e)}"
                tool_used = "Error"

            end_time = time.time()

            response_time = f"{end_time - start_time:.2f}s"

            # Display response
            st.markdown(reply)

            # ---------- META INFO ----------
            meta_info = f"Tool: {tool_used} | Time: {response_time}"
            st.caption(meta_info)

    # Save assistant response with metadata
    st.session_state.messages.append({
        "role": "assistant",
        "content": reply,
        "meta": meta_info
    })
