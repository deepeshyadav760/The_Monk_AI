import streamlit as st
import requests
import json
from datetime import datetime
import base64
from io import BytesIO
import time
from streamlit_mic_recorder import mic_recorder
from streamlit_cookies_manager import EncryptedCookieManager

# Page config
st.set_page_config(
    page_title="The Monk AI",
    page_icon="🕉️",
    layout="wide",
    initial_sidebar_state="auto"
)

# --- FIX: Initialize the Cookie Manager at the very top ---
# This creates the 'cookies' object that was previously undefined.
# Use a strong, secret password, preferably from environment variables or Streamlit secrets.
cookies = EncryptedCookieManager(
    password="a_very_strong_and_secret_password_for_the_monk_ai_app",
)
if not cookies.ready():
    # Wait for the component to be ready before proceeding.
    st.stop()

# Constants
API_BASE_URL = "http://localhost:8000"

# Session state initialization
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'access_token' not in st.session_state:
    st.session_state.access_token = None
if 'user_info' not in st.session_state:
    st.session_state.user_info = {}
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'current_session_id' not in st.session_state:
    st.session_state.current_session_id = None
if 'user_mode' not in st.session_state:
    st.session_state.user_mode = "beginner"

# Custom CSS for responsive design and chat styling
st.markdown("""
<style>
    /* Responsive design */
    @media (max-width: 768px) {
        .main-header {
            font-size: 2.5rem !important;
            margin-left: 0px !important;
            text-align: center;
        }
        .subtitle {
            margin-left: 0px !important;
            text-align: center;
        }
        .chat-container {
            padding: 1rem !important;
        }
        .chat-message {
            max-width: 90% !important;
            padding: 1rem !important;
        }
    }
    
    /* Chat message styling */
    .user-message {
        background: linear-gradient(135deg, #81C784, #66BB6A) !important;
        color: black !important;
        margin-left: auto !important;
        margin-right: 0 !important;
        border-radius: 15px 15px 0 15px !important;
        border: none !important;
        text-align: right !important;
    }
    
    .assistant-message {
        background: linear-gradient(135deg, #FFB380, #FFCC80) !important;
        color: black !important;
        margin-left: 0 !important;
        margin-right: auto !important;
        border-radius: 15px 15px 15px 0 !important;
        border: none !important;
        text-align: left !important;
    }
    
    .chat-message {
        padding: 1rem 1.5rem;
        margin: 0.8rem 0;
        max-width: 70%;
        position: relative;
        backdrop-filter: blur(10px);
        font-family: 'Arial', sans-serif;
        font-size: 1rem;
        line-height: 1.5;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* Welcome message */
    .welcome-message {
        text-align: center;
        padding: 1rem 2rem;
        background: linear-gradient(135deg, rgba(255, 107, 53, 0.1), rgba(156, 39, 176, 0.05));
        border-radius: 20px;
        margin: 2rem 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(15px);
    }
    
    .welcome-title {
        color: #FF6B35;
        font-family: 'Arial', sans-serif;
        font-size: 1.8rem;
        margin-bottom: 1rem;
        font-weight: bold;
    }
    
    .welcome-text {
        color: #333;
        font-family: 'Arial', sans-serif;
        font-size: 1.1rem;
    }
    
    /* Additional styling for other elements */
    .hindi-translation {
        background: linear-gradient(135deg, rgba(156, 39, 176, 0.15), rgba(186, 104, 200, 0.08));
        padding: 1.2rem 1.8rem;
        margin: 1rem 0;
        border-radius: 12px;
        border: 1px solid rgba(156, 39, 176, 0.3);
        color: #333;
        font-family: 'Arial', sans-serif;
    }
    
    .citation-container {
        background: linear-gradient(135deg, rgba(255, 107, 53, 0.1), rgba(247, 147, 30, 0.05));
        border-left: 4px solid #ff6b35;
        border-radius: 0 15px 15px 0;
        margin: 1.5rem 0;
        padding: 1.5rem 2rem;
        backdrop-filter: blur(10px);
    }
</style>
""", unsafe_allow_html=True)

# Helper functions
def make_authenticated_request(method, endpoint, data=None, files=None):
    """Make authenticated API request and handle expired tokens."""
    if not st.session_state.get('access_token'):
        return None

    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    
    try:
        if method == "GET":
            response = requests.get(f"{API_BASE_URL}{endpoint}", headers=headers)
        elif method == "POST":
            if files:
                response = requests.post(f"{API_BASE_URL}{endpoint}", headers=headers, data=data, files=files)
            else:
                headers["Content-Type"] = "application/json"
                response = requests.post(f"{API_BASE_URL}{endpoint}", headers=headers, json=data)
        elif method == "PUT":
            headers["Content-Type"] = "application/json"
            response = requests.put(f"{API_BASE_URL}{endpoint}", headers=headers, json=data)
        elif method == "DELETE":
            response = requests.delete(f"{API_BASE_URL}{endpoint}", headers=headers)
        
        response.raise_for_status()
        return response

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            st.error("Your session has expired. Please log in again.")
            cookies['access_token'] = '' # Clear the invalid cookie
            cookies.save()
            st.session_state.clear()
            st.rerun()
        else:
            st.error(f"API Error: {e.response.json().get('detail', e.response.text)}")
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {e}")
    
    return None

def login_page():
    """Enhanced Login/Register page"""
    st.markdown(
        """
        <h1 class="main-header" 
            style="margin-left: 520px; 
                color: #FF9933;
                font-size: 57px; 
                text-shadow: 
                        2px 2px 4px #000, 
                        -2px -2px 4px #ffcc99,
                        0 0 10px #ff6600;">
            The Monk AI
        </h1>
        """,
        unsafe_allow_html=True
    )

    st.markdown('<p class="subtitle" style="margin-left: 460px; font-size:22px">Seek wisdom from the sacred texts of Hinduism</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2 = st.tabs(["🚪 Login", "📝 Register"])
        
        with tab1:
            st.markdown('<h3 class="auth-form-header">Welcome Back, Seeker!</h3>', unsafe_allow_html=True)
            with st.form("login_form"):
                email = st.text_input("📧 Email Address", placeholder="Enter your email", key="login_email")
                password = st.text_input("🔐 Password", type="password", placeholder="Enter your password", key="login_password")
                
                login_button = st.form_submit_button("🕉️ Begin Journey")
                
                if login_button:
                    try:
                        response = requests.post(f"{API_BASE_URL}/auth/login", json={
                            "email": email,
                            "password": password
                        })
                        
                        if response.status_code == 200:
                            data = response.json()
                            token = data["access_token"]
                            st.session_state.access_token = token
                            st.session_state.logged_in = True

                            # Save token to the browser cookie for persistence
                            cookies['access_token'] = token
                            cookies.save()
                            
                            user_response = make_authenticated_request("GET", "/auth/me")
                            if user_response and user_response.status_code == 200:
                                st.session_state.user_info = user_response.json()
                                st.session_state.user_mode = st.session_state.user_info.get("preferred_mode", "beginner")
                            
                            st.success("🙏 Welcome back! Your spiritual journey continues...")
                            time.sleep(1.5)
                            st.rerun()
                        else:
                            st.error(f"❌ {response.json().get('detail', 'Invalid email or password.')}")
                    except Exception as e:
                        st.error(f"🚫 Login failed: {str(e)}")
        
        with tab2:
            st.markdown('<h3 class="auth-form-header">Join Our Sacred Community!</h3>', unsafe_allow_html=True)
            with st.form("register_form"):
                full_name = st.text_input("👤 Full Name", placeholder="Enter your full name", key="register_name")
                email = st.text_input("📧 Email Address", placeholder="Enter your email", key="register_email")
                password = st.text_input("🔐 Password", type="password", placeholder="Create a strong password", key="register_password")
                confirm_password = st.text_input("🔐 Confirm Password", type="password", placeholder="Confirm your password", key="register_confirm_password")
                preferred_mode = st.selectbox("🎓 Learning Path", ["beginner", "expert"], 
                                            format_func=lambda x: "🌱 Beginner (Guided Learning)" if x == "beginner" else "🧠 Expert (Advanced Insights)",
                                            key="register_mode")
                
                register_button = st.form_submit_button("🕉️ Start Your Journey")
                
                if register_button:
                    if password != confirm_password:
                        st.error("❌ Passwords don't match. Please try again.")
                    elif len(password) < 6:
                        st.error("❌ Password must be at least 6 characters long.")
                    else:
                        try:
                            response = requests.post(f"{API_BASE_URL}/auth/register", json={
                                "email": email,
                                "password": password,
                                "full_name": full_name,
                                "preferred_mode": preferred_mode
                            })
                            
                            if response.status_code == 200:
                                st.success("🎉 Registration successful! Please login to begin your spiritual journey.")
                            else:
                                error_msg = response.json().get("detail", "Registration failed")
                                st.error(f"❌ {error_msg}")
                        except Exception as e:
                            st.error(f"🚫 Registration failed: {str(e)}")

def chat_interface():
    """Enhanced chat interface"""
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(
            """
            <h1 class="main-header" 
                style="margin-left: 173px; 
                    color: #FF9933; 
                    text-size: 57px;
                    text-shadow: 
                            2px 2px 4px #000, 
                            -2px -2px 4px #ffcc99,
                            0 0 10px #ff6600;">
                The Monk AI
            </h1>
            """,
            unsafe_allow_html=True
        )

    with col2:
        current_mode = st.selectbox(
            "🎓 Learning Mode", ["beginner", "expert"],
            index=0 if st.session_state.user_mode == "beginner" else 1,
            key="mode_selector",
            format_func=lambda x: "🌱 Beginner" if x == "beginner" else "🧠 Expert"
        )
        st.session_state.user_mode = current_mode
    
    if not st.session_state.chat_history:
        st.markdown("""
        <div class="welcome-message">
            <h3 class="welcome-title">🙏 Namaste! What spiritual wisdom do you seek today?</h3>
        </div>
        """, unsafe_allow_html=True)
    
    display_chat_history()
    
    with st.container():
        st.markdown('<div class="fixed-input">', unsafe_allow_html=True)
        user_input = st.text_area(
            "💭 Share your spiritual question...", 
            key="user_input", 
            label_visibility="collapsed",
            placeholder="Type your question here..."
        )
        
        col_a, col_b, col_c = st.columns([4, 1, 1])
        with col_a:
            if st.button("🔍 Seek Wisdom", type="primary", use_container_width=True, key="seek_wisdom_button"):
                if user_input.strip():
                    process_query(user_input, "text")
        with col_b:
            audio = mic_recorder(
                start_prompt="🎤", stop_prompt="⏹️", key='voice_recorder', just_once=True,
            )
            if audio and audio['bytes']:
                st.info("🎙️ Transcribing your voice...")
                process_query(audio['bytes'], "voice")
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<div style="height: 100px;"></div>', unsafe_allow_html=True)


def process_query(input_data, input_type="text"):
    """Process user query for both text and voice"""
    if input_type == "text":
        user_message_content = input_data
        st.session_state.chat_history.append({
            "role": "user", 
            "content": user_message_content, 
            "timestamp": datetime.now().isoformat()
        })
        
        data = {
            "query": input_data,
            "mode": st.session_state.user_mode,
            "session_id": st.session_state.current_session_id
        }
        with st.spinner("🔮 Seeking wisdom from the ancient scriptures..."):
            response = make_authenticated_request("POST", "/chat/query", data=data)
    
    elif input_type == "voice":
        user_message_content = "[🎤 Voice message]"
        st.session_state.chat_history.append({
            "role": "user", 
            "content": user_message_content, 
            "timestamp": datetime.now().isoformat()
        })
        
        files = {'audio_file': ('voice_query.wav', input_data, 'audio/wav')}
        data = {
            "mode": st.session_state.user_mode,
            "session_id": st.session_state.current_session_id or ""
        }
        with st.spinner("🔮 Translating your spoken words into ancient wisdom..."):
            response = make_authenticated_request("POST", "/chat/voice-query", data=data, files=files)

    # This part remains the same
    if response and response.status_code == 200:
        result = response.json()
        st.session_state.current_session_id = result["session_id"]
        
        assistant_message = {
            "role": "assistant",
            "content": result["answer"],
            "hindi_translation": result["hindi_translation"],
            "citations": result["citations"],
            "recommendations": result["recommendations"],
            "keywords_explained": result.get("keywords_explained"),
            "timestamp": datetime.now().isoformat()
        }
        st.session_state.chat_history.append(assistant_message)
        st.rerun()
    else:
        # Only pop if a response failed, not if it was None (e.g., auth error handled in make_request)
        if response is not None:
            st.session_state.chat_history.pop()
            st.error("Failed to get a response from the Monk AI. Please try again.")
            st.rerun()


def display_chat_history():
    """Display enhanced chat messages"""
    for message in st.session_state.chat_history:
        role = message.get("role")
        if role == "user":
            st.markdown(f'''<div style="display: flex; justify-content: flex-end; margin: 10px 0;"><div class="chat-message user-message"><strong>You:</strong><br>{message["content"]}</div></div>''', unsafe_allow_html=True)
        elif role == "assistant":
            st.markdown(f'''<div style="display: flex; justify-content: flex-start; margin: 10px 0;"><div class="chat-message assistant-message"><strong>🕉️ The Monk AI:</strong><br>{message["content"]}</div></div>''', unsafe_allow_html=True)
            
            if message.get("hindi_translation"):
                st.markdown(f'''<div style="display: flex; justify-content: flex-start; margin: 10px 0;"><div class="hindi-translation"><div style="color: #ff6b35; font-weight: 600; margin-bottom: 0.5rem;">🕉️ हिंदी अनुवाद:</div>{message["hindi_translation"]}</div></div>''', unsafe_allow_html=True)
            
            if message.get("keywords_explained"):
                st.markdown('<div class="citation-header">📚 Spiritual Terms Explained</div>', unsafe_allow_html=True)
                for term, explanation in message["keywords_explained"].items():
                    st.markdown(f'''<div style="display: flex; justify-content: flex-start; margin: 10px 0;"><div class="keyword-explanation"><span style="color: #ff6b35; font-weight: 600;">{term.title()}:</span> {explanation}</div></div>''', unsafe_allow_html=True)
            
            if message.get("citations"):
                st.markdown('<div class="citation-container"><div style="color: #ff6b35; font-weight: 600; font-size: 1.2rem;">📖 Sacred Sources & References</div></div>', unsafe_allow_html=True)
                for i, citation in enumerate(message["citations"], 1):
                    st.markdown(f'''<div style="display: flex; justify-content: flex-start; margin: 10px 0;"><div class="citation-item"><span style="background: linear-gradient(135deg, #ff6b35, #f7931e); color: white; width: 24px; height: 24px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 0.9rem; font-weight: bold; margin-right: 0.8rem;">{i}</span><div><div style="color: #ff6b35; font-weight: 600; font-size: 1rem;">{citation["book"]}</div><div style="color: #666; font-size: 0.9rem; margin: 0.3rem 0;">"{citation["content_preview"]}"</div></div></div></div>''', unsafe_allow_html=True)
            
            if message.get("recommendations"):
                recs = "".join(f"<li>{book}</li>" for book in message["recommendations"])
                st.markdown(f'''<div style="display: flex; justify-content: flex-start; margin: 10px 0;"><div style="background: linear-gradient(135deg, rgba(76, 175, 80, 0.15), rgba(129, 199, 132, 0.08)); padding: 1.5rem 2rem; margin: 1.5rem 0; border-radius: 15px; border: 1px solid rgba(76, 175, 80, 0.3); color: #2e7d32;"><div style="color: #4caf50; font-weight: 600; font-size: 1.2rem; margin-bottom: 1rem;">📚 Recommended Texts</div><ul>{recs}</ul></div></div>''', unsafe_allow_html=True)

def load_chat_session(session_id):
    """Load a specific chat session from the backend."""
    try:
        response = make_authenticated_request("GET", f"/chat/sessions/{session_id}")
        if response and response.status_code == 200:
            session_data = response.json()
            st.session_state.current_session_id = session_id
            st.session_state.chat_history = session_data.get("messages", [])
            st.rerun()
    except Exception as e:
        st.error(f"Error loading chat session: {str(e)}")

def sidebar():
    """Enhanced sidebar with chat sessions and user profile."""
    with st.sidebar:
        if st.session_state.user_info:
            st.markdown(f"""
            <div style="padding: 1rem; background: rgba(255, 255, 255, 0.05); border-radius: 10px; text-align: center; margin-top: 2rem;">
                <div style="color: #ff6b35; font-weight: 600;margin-top:-75px">
                    🙏 Welcome, {st.session_state.user_info.get('full_name', 'Seeker')}
                </div>
            </div>
            """, unsafe_allow_html=True)

        if st.button("🚪 Logout", use_container_width=True, key="logout_button"):
            # Clear the cookie and the session state
            cookies['access_token'] = ''
            cookies.save()
            st.session_state.clear()
            st.rerun()

        st.markdown("---")

        try:
            response = make_authenticated_request("GET", "/chat/sessions")
            if response and response.status_code == 200:
                sessions = response.json()
                if sessions:
                    st.markdown("**🕉️ Previous Conversations:**")
                    for session in sessions[:15]:
                        session_title = session["title"][:28] + "..." if len(session["title"]) > 28 else session["title"]
                        if st.button(f"💭 {session_title}", key=f"session_{session['session_id']}", use_container_width=True):
                            load_chat_session(session["session_id"])
                else:
                    st.info("No previous conversations yet.")
        except Exception as e:
            st.error(f"Error loading sessions: {str(e)}")

def restore_session_from_cookie():
    """
    Checks for a token in cookies and tries to restore the user session.
    Returns True if the session is successfully restored, False otherwise.
    """
    token = cookies.get('access_token')
    if not token:
        return False
    
    st.session_state.access_token = token
    user_response = make_authenticated_request("GET", "/auth/me")

    if user_response and user_response.status_code == 200:
        st.session_state.user_info = user_response.json()
        st.session_state.user_mode = st.session_state.user_info.get("preferred_mode", "beginner")
        st.session_state.logged_in = True
        return True
    
    return False

def main():
    """Main application entry point with persistent login logic."""
    if st.session_state.get('logged_in'):
        sidebar()
        chat_interface()
    elif restore_session_from_cookie():
        st.rerun()
    else:
        login_page()

if __name__ == "__main__":
    main()