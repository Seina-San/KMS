
import streamlit as st
import openai
import sqlite3
import hashlib

# Set OpenAI API Key
openai.api_key = "your-api-key-here"

# Initialize database
conn = sqlite3.connect("notes.db", check_same_thread=False)
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, user_id INTEGER, content TEXT, FOREIGN KEY(user_id) REFERENCES users(id))")
conn.commit()

# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Function to verify login
def login_user(username, password):
    c.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, hash_password(password)))
    return c.fetchone()

# Function to register user
def register_user(username, password):
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hash_password(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

# Function to fetch notes for a user
def get_notes(user_id):
    c.execute("SELECT * FROM notes WHERE user_id = ?", (user_id,))
    return c.fetchall()

# Function to search notes
def search_notes(user_id, query):
    c.execute("SELECT * FROM notes WHERE user_id = ? AND content LIKE ?", (user_id, f"%{query}%"))
    return c.fetchall()

# Function to summarize text
def summarize_text(text):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": f"Summarize this note: {text}"}]
    )
    return response["choices"][0]["message"]["content"].strip()

# Streamlit UI
st.title("AI-Powered Knowledge Management System")

# User authentication
if "user_id" not in st.session_state:
    st.subheader("Login / Register")
    option = st.radio("Select an option:", ["Login", "Register"])
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if option == "Login" and st.button("Login"):
        user = login_user(username, password)
        if user:
            st.session_state.user_id = user[0]
            st.success("Login successful!")
            st.experimental_rerun()
        else:
            st.error("Invalid username or password")
    
    if option == "Register" and st.button("Register"):
        if register_user(username, password):
            st.success("Registration successful! Please login.")
        else:
            st.error("Username already exists")
    
    st.stop()

st.subheader(f"Welcome, {username}!")

# Note input
note = st.text_area("Write your note here:")
if st.button("Save Note"):
    c.execute("INSERT INTO notes (user_id, content) VALUES (?, ?)", (st.session_state.user_id, note))
    conn.commit()
    st.success("Note saved successfully!")

# AI Summarization
if st.button("Summarize Note"):
    summary = summarize_text(note)
    st.write("**Summary:**", summary)

# Search notes
search_query = st.text_input("Search notes:")
if search_query:
    results = search_notes(st.session_state.user_id, search_query)
    st.subheader("Search Results")
    for n in results:
        st.write(f"**{n[0]}:** {n[2]}")

# Display saved notes
st.subheader("Saved Notes")
notes = get_notes(st.session_state.user_id)
for n in notes:
    st.write(f"**{n[0]}:** {n[2]}")

# Logout option
if st.button("Logout"):
    del st.session_state.user_id
    st.experimental_rerun()
