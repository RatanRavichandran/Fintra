import json
import streamlit as st
from ui import apply_global_styles

# Set page configuration
st.set_page_config(
    page_title="Your Finance Planner",
    page_icon="[Finance]",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_global_styles()


# Initialize session state variables if they don't exist
if 'user_data' not in st.session_state:
    st.session_state.user_data = {
        'personal': {},
        'income': {},
        'expenses': {},
        'assets': {},
        'liabilities': {},
        'goals': {},
        'subscriptions': []
    }

if 'financial_plan' not in st.session_state:
    st.session_state.financial_plan = None

if 'investment_plan' not in st.session_state:
    st.session_state.investment_plan = None

if 'debt_plan' not in st.session_state:
    st.session_state.debt_plan = None

if 'subscription_analysis' not in st.session_state:
    st.session_state.subscription_analysis = None


# a small helper to render the conversation
def render_chat():
    for user_msg, bot_msg in st.session_state.chat_history:
        st.markdown(f"**You:** {user_msg}")
        st.markdown(f"**Bot:** {bot_msg}")
        
def load_profile_from_file(uploaded_file):
    try:
        # Read content from the uploaded file
        content = uploaded_file.read()
        
        # Parse JSON from content
        profile_data = json.loads(content)
        
        # Validate and structure the data
        required_sections = ['personal', 'income', 'expenses', 'assets', 'liabilities', 'goals']
        if not all(section in profile_data for section in required_sections):
            raise ValueError("Profile file missing required sections")
            
        # Update session state
        st.session_state.user_data = profile_data
        return True
    except Exception as e:
        st.error(f"Error loading profile: {str(e)}")
        return False

st.markdown('<div class="main-header">Profile Management</div>', unsafe_allow_html=True)

# File uploader
uploaded_file = st.file_uploader("Upload your profile data file (JSON format)", type=['json'])
if uploaded_file is not None:
    if load_profile_from_file(uploaded_file):
        st.success("Profile loaded successfully!")
        
        # Display loaded profile data
        st.write("Personal Information:")
        st.write(st.session_state.user_data['personal'])
        
        st.write("\nIncome Details:")
        st.write(st.session_state.user_data['income'])
        
        st.write("\nExpenses:")
        st.write(st.session_state.user_data['expenses'])
        
        st.write("\nAssets:")
        st.write(st.session_state.user_data['assets'])
        
        st.write("\nLiabilities:")
        st.write(st.session_state.user_data['liabilities'])
        
        st.write("\nFinancial Goals:")
        st.write(st.session_state.user_data['goals'])