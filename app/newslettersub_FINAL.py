import os
import json
import logging
import smtplib
import re
import datetime
import io
from typing import List, Dict, Any, Optional
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import get_settings, get_path
import streamlit as st
import openai
from serpapi import GoogleSearch
from pydantic import BaseModel, EmailStr, Field, validator
import markdown
from dateutil import parser as date_parser

settings = get_settings()
openai.api_key = settings.openai_api_key
SERPAPI_API_KEY = settings.serpapi_api_key
EMAIL_HOST = settings.email_host or 'smtp.gmail.com'
EMAIL_PORT = settings.email_port or 587
EMAIL_USER = settings.email_user
EMAIL_PASSWORD = settings.email_password
EMAIL_FROM = settings.email_from or settings.email_user

# Setup logging to StringIO for display in Streamlit
log_stream = io.StringIO()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=log_stream
)
logger = logging.getLogger(__name__)

# Ensure output directory exists
OUTPUT_DIR = get_path('data', 'newsletter_output')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_css():
    st.markdown("""
    <style>
    /* Main colors */
    :root {
        --primary-color: #005e7c;
        --secondary-color: #cf352f;
        --background-color: #ffffff;
        --card-bg-color: #f3f5f9;
        --text-color: #333333;
        --light-text: #666666;
        --sidebar-bg: #005e7c;
        --sidebar-text: #f3f5f9;
    }
    
    /* Base styling */
    .main {
        background-color: var(--background-color);
        color: var(--text-color);
    }
    
    /* Headings */
    h1, h2, h3, h4, h5, h6 {
        color: var(--primary-color);
        font-weight: 600;
    }
    
    /* Cards */
    .card {
        background-color: var(--card-bg-color);
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    
    /* Buttons */
    .stButton > button {
        background-color: var(--secondary-color) !important;
        color: white !important;
        border: none !important;
        border-radius: 5px !important;
        padding: 10px 24px !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        opacity: 0.9 !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1) !important;
    }
    
    /* Sidebar - Updated with new colors */
    [data-testid="stSidebar"] {
        background-color: var(--sidebar-bg) !important;
    }
    
    [data-testid="stSidebar"] .css-1d391kg,
    [data-testid="stSidebar"] .css-1wrcr25,
    [data-testid="stSidebar"] .css-ocqkz7,
    [data-testid="stSidebar"] .css-1avcm0n {
        background-color: var(--sidebar-bg) !important;
    }
    
    /* Sidebar text color */
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] div {
        color: var(--sidebar-text) !important;
    }
    
    /* Sidebar headings */
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4,
    [data-testid="stSidebar"] h5,
    [data-testid="stSidebar"] h6,
    [data-testid="stSidebar"] .section-header,
    [data-testid="stSidebar"] .sub-section {
        color: var(--sidebar-text) !important;
    }
    
    /* Sidebar input fields - with black text for email field */
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] textarea {
        background-color: white !important;
        color: black !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
    }
    
    /* Email input field specific styling */
    [data-testid="stSidebar"] [aria-label="Email address"] {
        color: black !important;
    }
    
    /* Make sure the placeholder is visible */
    [data-testid="stSidebar"] input::placeholder {
        color: #888888 !important;
    }
    
    /* Sidebar card background */
    [data-testid="stSidebar"] .card {
        background-color: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }
    
    /* Highlights */
    .highlight {
        color: var(--secondary-color);
        font-weight: 600;
    }
    
    /* Important text */
    .important-text {
        color: var(--secondary-color);
        font-weight: 500;
    }
    
    /* Section headers */
    .section-header {
        color: var(--primary-color);
        font-size: 1.5rem;
        font-weight: 600;
        margin-top: 30px;
        margin-bottom: 15px;
        padding-bottom: 8px;
        border-bottom: 2px solid var(--primary-color);
    }
    
    /* Sub-section headers */
    .sub-section {
        color: var(--primary-color);
        font-size: 1.2rem;
        font-weight: 500;
        margin-top: 20px;
        margin-bottom: 10px;
    }
    
    /* Logo container */
    .logo-container {
        display: flex;
        align-items: center;
        margin-bottom: 20px;
    }
    
    .logo-text {
        color: var(--primary-color);
        font-size: 1.8rem;
        font-weight: 700;
        margin-left: 10px;
    }
    
    /* Profile summary card */
    .profile-card {
        background-color: var(--card-bg-color);
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        border-left: 5px solid var(--primary-color);
    }
    
    /* Newsletter content */
    .newsletter-content {
        background-color: var(--card-bg-color);
        border-radius: 10px;
        padding: 25px;
        margin-top: 20px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
    }
    
    /* Success message */
    .success-msg {
        background-color: #d4edda;
        color: #155724;
        padding: 10px 15px;
        border-radius: 5px;
        margin-bottom: 15px;
    }
    
    /* Error message */
    .error-msg {
        background-color: #f8d7da;
        color: #721c24;
        padding: 10px 15px;
        border-radius: 5px;
        margin-bottom: 15px;
    }
    
    /* Info box */
    .info-box {
        background-color: #cce5ff;
        color: #004085;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 15px;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: var(--card-bg-color);
        border-radius: 5px 5px 0 0;
        padding: 10px 20px;
        color: var(--text-color);
    }
    
    .stTabs [aria-selected="true"] {
        background-color: var(--primary-color) !important;
        color: white !important;
    }
    
    /* Progress bar */
    .stProgress > div > div {
        background-color: var(--primary-color);
    }
    
    /* Sidebar button styling to ensure visibility */
    [data-testid="stSidebar"] .stButton > button {
        background-color: var(--secondary-color) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
    }
    
    /* Sidebar expander styling */
    [data-testid="stSidebar"] [data-testid="stExpander"] {
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }
    
    /* Additional styling for all input text to be black */
    input, textarea, [role="combobox"] {
        color: black !important;
    }
    
    /* Ensure text is visible when typing in sidebar inputs */
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] [role="combobox"],
    [data-testid="stSidebar"] textarea {
        background-color: white !important;
        color: black !important;
    }
    
    /* Toggle switch styling */
    .toggle-container {
        display: flex;
        align-items: center;
        margin: 15px 0;
    }
    
    .toggle-label {
        margin-right: 10px;
        font-weight: 500;
    }
    
    /* Custom styling for the market mode toggle */
    .market-toggle {
        background-color: var(--card-bg-color);
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 15px;
        border-left: 3px solid var(--primary-color);
    }
    
    /* Custom tag styling for goals and topics */
    .custom-tag {
        display: inline-block;
        background-color: rgba(0, 94, 124, 0.1);
        color: var(--primary-color);
        padding: 5px 10px;
        border-radius: 15px;
        margin: 3px;
        font-size: 0.9rem;
    }
    
    /* Goal-specific section styling */
    .goal-section {
        background-color: rgba(207, 53, 47, 0.05);
        border-left: 3px solid var(--secondary-color);
        padding: 15px;
        margin: 15px 0;
        border-radius: 5px;
    }
    
    /* Custom topic input styling */
    .custom-topic-input {
        margin-top: 15px;
        padding: 10px;
        background-color: var(--card-bg-color);
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# Pydantic models
class UserInterests(BaseModel):
    topics: List[str] = Field(default_factory=list)
    sectors: List[str] = Field(default_factory=list)
    companies: List[str] = Field(default_factory=list)
    investment_types: List[str] = Field(default_factory=list)
    risk_profile: str = "Moderate"
    time_horizon: str = "Medium-term"
    custom_topics: List[str] = Field(default_factory=list)  # New field for custom topics
    
    @validator('topics', 'sectors', 'companies', 'investment_types', 'custom_topics')
    def deduplicate_lists(cls, v):
        return list(set(v))

# Update the UserProfile class definition to properly include custom_topics
class UserProfile(BaseModel):
    name: str
    email: EmailStr
    age: Optional[int] = None
    occupation: Optional[str] = None
    financial_goals: Optional[List[str]] = Field(default_factory=list)
    existing_investments: Optional[List[str]] = Field(default_factory=list)
    risk_appetite: Optional[str] = None
    free_text_description: Optional[str] = None
    income: Optional[Dict[str, Any]] = None
    expenses: Optional[Dict[str, Any]] = None
    assets: Optional[Dict[str, Any]] = None
    liabilities: Optional[Dict[str, Any]] = None
    goals: Optional[Dict[str, Any]] = None
    age_specific: Optional[Dict[str, Any]] = None
    custom_topics: List[str] = Field(default_factory=list)  # Properly defined with default
    goal_details: Optional[Dict[str, Any]] = None

def load_profile_from_file(file_content) -> UserProfile:
    """Load user profile from a JSON file."""
    try:
        profile_data = json.loads(file_content)
        logger.info("Successfully loaded profile data from file")
        
        # Extract basic information
        name = profile_data.get("personal", {}).get("name", "User")
        age = profile_data.get("personal", {}).get("age")
        risk_appetite = profile_data.get("personal", {}).get("risk_tolerance", "Moderate")
        
        # Extract financial goals
        financial_goals = []
        goals_data = profile_data.get("goals", {})
        age_specific_data = profile_data.get("age_specific", {})
        
        # Add goals from the goals section
        if goals_data.get("emergency_fund"):
            financial_goals.append("Emergency Fund")
        if goals_data.get("pay_off_debt"):
            financial_goals.append("Debt Repayment")
        if goals_data.get("vacation"):
            financial_goals.append("Vacation Planning")
        if goals_data.get("down_payment"):
            financial_goals.append("Home Down Payment")
        if goals_data.get("education"):
            financial_goals.append("Education Funding")
        if goals_data.get("tax_saving"):
            financial_goals.append("Tax Saving")
        if goals_data.get("retirement"):
            financial_goals.append("Retirement Planning")
        if goals_data.get("financial_independence"):
            financial_goals.append("Financial Independence")
        if goals_data.get("child_marriage"):
            financial_goals.append("Child Marriage Planning")
        
        # Add goals from age_specific section
        if age_specific_data.get("financial_goals"):
            financial_goals.extend(age_specific_data.get("financial_goals", []))
        
        # Extract existing investments from assets
        existing_investments = []
        assets = profile_data.get("assets", {})
        if assets.get("cash", 0) > 0:
            existing_investments.append("Cash/Savings")
        if assets.get("equity", 0) > 0:
            existing_investments.append("Equity Investments")
        if assets.get("epf_ppf", 0) > 0:
            existing_investments.append("EPF/PPF")
        if assets.get("real_estate", 0) > 0:
            existing_investments.append("Real Estate")
        if assets.get("gold", 0) > 0:
            existing_investments.append("Gold")
        
        # Add products used as investments
        products_used = age_specific_data.get("products_used", [])
        for product in products_used:
            if "mutual fund" in product.lower():
                existing_investments.append("Mutual Funds")
            if "fd" in product.lower() or "fixed deposit" in product.lower():
                existing_investments.append("Fixed Deposits")
            if "stock" in product.lower():
                existing_investments.append("Stocks")
            if "bond" in product.lower():
                existing_investments.append("Bonds")
        
        # Create a description from various profile elements
        description_parts = []
        
        # Add income information
        income = profile_data.get("income", {})
        total_income = (
            income.get("primary_income", 0) +
            income.get("secondary_income", 0) +
            income.get("other_income", 0)
        )
        if total_income > 0:
            description_parts.append(f"Monthly income of INR {total_income}.")
        
        # Add expense information
        expenses = profile_data.get("expenses", {})
        total_expenses = sum(expenses.values())
        if total_expenses > 0:
            description_parts.append(f"Monthly expenses of approximately INR {total_expenses}.")
        
        # Add liability information
        liabilities = profile_data.get("liabilities", {})
        total_liabilities = (
            liabilities.get("home_loan", 0) +
            liabilities.get("car_loan", 0) +
            liabilities.get("education_loan", 0) +
            liabilities.get("credit_card", 0) +
            liabilities.get("personal_loan", 0) +
            liabilities.get("other_debt", 0)
        )
        if total_liabilities > 0:
            description_parts.append(f"Total debt of INR {total_liabilities}.")
        
        # Add specific loan details
        if liabilities.get("education_loan", 0) > 0:
            description_parts.append(
                f"Education loan of INR {liabilities.get('education_loan')} " +
                f"at {liabilities.get('education_loan_interest_rate', 0)}% interest."
            )
        if liabilities.get("home_loan", 0) > 0:
            description_parts.append(
                f"Home loan of INR {liabilities.get('home_loan')} " +
                f"at {liabilities.get('home_loan_interest_rate', 0)}% interest."
            )
        
        # Add financial challenges
        if age_specific_data.get("financial_challenges"):
            challenges = age_specific_data.get("financial_challenges", [])
            description_parts.append(f"Financial challenges include: {', '.join(challenges)}.")
        
        # Add other goals
        if goals_data.get("other_goal"):
            description_parts.append(f"Other financial goals: {goals_data.get('other_goal')}.")
        
        # Add investing comfort level
        if age_specific_data.get("investing_comfort"):
            description_parts.append(f"Comfort level with investing: {age_specific_data.get('investing_comfort')}.")
        
        # Add credit score understanding
        if age_specific_data.get("credit_score_understanding"):
            description_parts.append(f"Credit score understanding: {age_specific_data.get('credit_score_understanding')}.")
        
        # Combine all description parts
        free_text_description = " ".join(description_parts)
        
        # Create a dummy email if not provided
        email = f"{name.lower().replace(' ', '.')}@example.com"
        
        # Extract detailed goal information
        goal_details = {}
        
        # Retirement goal details
        if goals_data.get("retirement"):
            retirement_details = {
                "target_age": goals_data.get("retirement_age", 60),
                "monthly_income_needed": goals_data.get("retirement_monthly_income", 50000),
                "current_retirement_savings": assets.get("retirement_savings", 0)
            }
            goal_details["retirement"] = retirement_details
        
        # Education goal details
        if goals_data.get("education"):
            education_details = {
                "target_amount": goals_data.get("education_amount", 1000000),
                "years_remaining": goals_data.get("education_years", 5),
                "current_savings": assets.get("education_fund", 0)
            }
            goal_details["education"] = education_details
        
        # Home purchase goal details
        if goals_data.get("down_payment"):
            home_details = {
                "target_amount": goals_data.get("down_payment_amount", 2000000),
                "years_remaining": goals_data.get("down_payment_years", 3),
                "current_savings": assets.get("home_fund", 0)
            }
            goal_details["home_purchase"] = home_details
        
        return UserProfile(
            name=name,
            email=email,
            age=age,
            occupation=None,  # Not provided in the profile format
            financial_goals=financial_goals,
            existing_investments=existing_investments,
            risk_appetite=risk_appetite,
            free_text_description=free_text_description,
            income=income,
            expenses=expenses,
            assets=assets,
            liabilities=liabilities,
            goals=goals_data,
            age_specific=age_specific_data,
            goal_details=goal_details,
            custom_topics=[]  # Initialize with empty list
        )
    except Exception as e:
        logger.error(f"Error loading profile from file: {str(e)}")
        raise ValueError(f"Failed to parse profile file: {str(e)}")

# Functions to extract interests
def extract_interests_from_json(profile: UserProfile) -> UserInterests:
    """Extract structured interests from a user profile."""
    interests = UserInterests()
    
    # Add custom topics if available
    if hasattr(profile, 'custom_topics') and profile.custom_topics:
        interests.custom_topics = profile.custom_topics
        # Also add custom topics to general topics for search purposes
        interests.topics.extend(profile.custom_topics)
    
    # Map financial goals to topics
    if profile.financial_goals:
        goal_to_topic = {
            "retirement": ["retirement planning", "pension funds"],
            "education": ["education financing", "student loans"],
            "home": ["real estate", "home loans", "property market"],
            "wealth": ["wealth management", "high-growth investments"],
            "passive income": ["dividend stocks", "rental income", "passive income"],
            "tax saving": ["tax-saving investments", "ELSS", "tax planning"],
            "emergency fund": ["liquid funds", "emergency savings", "financial safety net"],
            "debt": ["debt management", "loan repayment strategies"],
            "financial independence": ["FIRE movement", "passive income", "wealth building"]
        }
        
        for goal in profile.financial_goals:
            goal_lower = goal.lower()
            for key, topics in goal_to_topic.items():
                if key in goal_lower:
                    interests.topics.extend(topics)
    
    # Map existing investments to sectors and investment types
    if profile.existing_investments:
        investment_mapping = {
            "stocks": {
                "investment_types": ["equity", "stocks"],
                "sectors": []
            },
            "mutual funds": {
                "investment_types": ["mutual funds"],
                "sectors": []
            },
            "bonds": {
                "investment_types": ["debt", "bonds"],
                "sectors": []
            },
            "real estate": {
                "investment_types": ["real estate"],
                "sectors": ["property"]
            },
            "gold": {
                "investment_types": ["commodities", "gold"],
                "sectors": ["precious metals"]
            },
            "crypto": {
                "investment_types": ["cryptocurrency"],
                "sectors": ["digital assets"]
            },
            "fd": {
                "investment_types": ["fixed deposits", "debt"],
                "sectors": ["banking"]
            },
            "ppf": {
                "investment_types": ["government schemes", "tax-saving"],
                "sectors": []
            },
            "epf": {
                "investment_types": ["retirement funds", "government schemes"],
                "sectors": []
            },
            "cash": {
                "investment_types": ["savings", "liquid funds"],
                "sectors": ["banking"]
            }
        }
        
        for investment in profile.existing_investments:
            investment_lower = investment.lower()
            for key, mappings in investment_mapping.items():
                if key in investment_lower:
                    interests.investment_types.extend(mappings["investment_types"])
                    interests.sectors.extend(mappings["sectors"])
            
            # Extract company names if mentioned
            company_match = re.search(r'in\s+([A-Za-z\s]+)', investment_lower)
            if company_match:
                interests.companies.append(company_match.group(1).strip())
    
    # Extract additional sectors based on age-specific data
    if profile.age_specific and "financial_goals" in profile.age_specific:
        for goal in profile.age_specific.get("financial_goals", []):
            if "student loan" in goal.lower() or "education loan" in goal.lower():
                interests.topics.append("education loan repayment")
                interests.sectors.append("banking")
            if "invest" in goal.lower():
                interests.topics.append("investment basics")
                interests.topics.append("beginner investing")
    
    # Extract companies from products used
    if profile.age_specific and "products_used" in profile.age_specific:
        for product in profile.age_specific.get("products_used", []):
            if "upi" in product.lower():
                interests.topics.append("digital payments")
                interests.sectors.append("fintech")
    
    # Set risk profile based on risk appetite
    if profile.risk_appetite:
        risk_mapping = {
            "low": "Conservative",
            "conservative": "Conservative",
            "medium": "Moderate",
            "moderate": "Moderate",
            "high": "Aggressive",
            "aggressive": "Aggressive"
        }
        risk_lower = profile.risk_appetite.lower()
        for key, value in risk_mapping.items():
            if key in risk_lower:
                interests.risk_profile = value
                break
    
    # Set time horizon based on age and goals
    if profile.age and profile.age < 30:
        # Younger investors typically have longer time horizons
        interests.time_horizon = "Long-term"
    elif profile.age and profile.age > 50:
        # Older investors may have shorter time horizons
        interests.time_horizon = "Short-term"
    else:
        interests.time_horizon = "Medium-term"
    
    # If retirement is a goal, adjust time horizon
    if profile.goals and profile.goals.get("retirement") and profile.age:
        retirement_age = profile.goals.get("retirement_age", 60)
        years_to_retirement = retirement_age - profile.age
        if years_to_retirement > 20:
            interests.time_horizon = "Long-term"
        elif years_to_retirement > 10:
            interests.time_horizon = "Medium-term"
        else:
            interests.time_horizon = "Short-term"
    
    # Add income-based topics
    if profile.income:
        total_income = (
            profile.income.get("primary_income", 0) +
            profile.income.get("secondary_income", 0) +
            profile.income.get("other_income", 0)
        )
        if total_income < 25000:
            interests.topics.extend(["budget management", "affordable investing", "small-cap funds"])
        elif total_income < 75000:
            interests.topics.extend(["mid-cap investments", "SIPs", "tax optimization"])
        else:
            interests.topics.extend(["wealth management", "portfolio diversification", "alternative investments"])
    
    # Add liability-based topics
    if profile.liabilities:
        if profile.liabilities.get("education_loan", 0) > 0:
            interests.topics.extend(["education loan repayment", "debt management"])
        if profile.liabilities.get("home_loan", 0) > 0:
            interests.topics.extend(["home loan optimization", "interest rate trends"])
            interests.sectors.append("real estate")
        if profile.liabilities.get("credit_card", 0) > 0:
            interests.topics.extend(["credit card debt management", "debt consolidation"])
    
    # Add custom topics if they exist
    if profile.custom_topics:
        interests.topics.extend(profile.custom_topics)
        interests.custom_topics = profile.custom_topics
    
    # Add default topics if none extracted
    if not interests.topics:
        interests.topics = ["Indian stock market", "personal finance", "investment strategies"]
    
    # Add default sectors if none extracted
    if not interests.sectors:
        interests.sectors = ["banking", "technology", "consumer goods"]
    
    # Add default investment types if none extracted
    if not interests.investment_types:
        interests.investment_types = ["stocks", "mutual funds", "fixed deposits"]
    
    return interests

def extract_interests_with_openai(profile: UserProfile) -> UserInterests:
    """Extract interests using OpenAI when structured data is insufficient."""
    logger.info("Extracting interests using OpenAI")
    
    # Prepare the prompt
    system_prompt = """
    You are a financial advisor specializing in Indian markets. Extract structured information from the user's profile.
    Return ONLY a JSON object with the following fields:
    - topics: List of financial topics the user might be interested in
    - sectors: List of market sectors relevant to the user
    - companies: List of specific companies mentioned or implied
    - investment_types: List of investment vehicles the user might prefer
    - risk_profile: One of "Conservative", "Moderate", or "Aggressive"
    - time_horizon: One of "Short-term", "Medium-term", or "Long-term"
    - custom_topics: Include any custom topics the user has specified
    """
    
    # Create a comprehensive profile description for OpenAI
    profile_description = f"""
    User Profile:
    Name: {profile.name}
    Age: {profile.age if profile.age else 'Not specified'}
    Risk Appetite: {profile.risk_appetite if profile.risk_appetite else 'Not specified'}
    Financial Goals: {', '.join(profile.financial_goals) if profile.financial_goals else 'Not specified'}
    Existing Investments: {', '.join(profile.existing_investments) if profile.existing_investments else 'Not specified'}
    Custom Topics of Interest: {', '.join(profile.custom_topics) if profile.custom_topics else 'None specified'}
    
    Income Details:
    {json.dumps(profile.income) if profile.income else 'Not provided'}
    
    Expense Details:
    {json.dumps(profile.expenses) if profile.expenses else 'Not provided'}
    
    Asset Details:
    {json.dumps(profile.assets) if profile.assets else 'Not provided'}
    
    Liability Details:
    {json.dumps(profile.liabilities) if profile.liabilities else 'Not provided'}
    
    Goal Details:
    {json.dumps(profile.goals) if profile.goals else 'Not provided'}
    
    Age-Specific Details:
    {json.dumps(profile.age_specific) if profile.age_specific else 'Not provided'}
    
    Additional Description: {profile.free_text_description if profile.free_text_description else 'Not provided'}
    """
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": profile_description}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        content = response.choices[0].message.content
        
        # Extract JSON from the response
        try:
            # Try to parse the entire response as JSON
            interests_dict = json.loads(content)
        except json.JSONDecodeError:
            # If that fails, try to extract JSON using regex
            match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
            if match:
                try:
                    interests_dict = json.loads(match.group(1))
                except json.JSONDecodeError:
                    logger.error("Failed to parse JSON from OpenAI response")
                    return UserInterests()
            else:
                logger.error("No JSON found in OpenAI response")
                return UserInterests()
        
        # Create UserInterests object
        interests = UserInterests(
            topics=interests_dict.get("topics", []),
            sectors=interests_dict.get("sectors", []),
            companies=interests_dict.get("companies", []),
            investment_types=interests_dict.get("investment_types", []),
            risk_profile=interests_dict.get("risk_profile", "Moderate"),
            time_horizon=interests_dict.get("time_horizon", "Medium-term"),
            custom_topics=interests_dict.get("custom_topics", [])
        )
        
        # Add custom topics from profile if they exist
        if profile.custom_topics:
            interests.custom_topics = profile.custom_topics
        
        return interests
    except Exception as e:
        logger.error(f"Error extracting interests with OpenAI: {str(e)}")
        return UserInterests()

# News gathering functions
def serpapi_search(query: str, num_results: int = 10, is_global: bool = False) -> List[Dict[str, Any]]:
    """Perform a Google search for financial news using SerpAPI."""
    try:
        # Add market focus to the query
        if is_global:
            search_query = f"{query} financial news"
            gl_param = "us"  # Default to US for global news
        else:
            search_query = f"{query} India financial news"
            gl_param = "in"  # India for Indian market focus
        
        # Calculate date range for the past week
        today = datetime.datetime.now()
        one_week_ago = (today - datetime.timedelta(days=7))
        
        # Format date for SerpAPI (tbs parameter)
        # qdr:w means past week
        time_range = "qdr:w"
        
        logger.info(f"Searching with SerpAPI for: '{search_query}' (limited to past 7 days, {'global' if is_global else 'Indian'} market)")
        
        # Set up the search parameters
        params = {
            "engine": "google",
            "q": search_query,
            "api_key": SERPAPI_API_KEY,
            "num": num_results,
            "tbs": time_range,  # Time-based search: past week
            "tbm": "nws",       # Search type: news
            "gl": gl_param,     # Country: India or US based on mode
            "hl": "en"          # Language: English
        }
        
        # Execute the search
        search = GoogleSearch(params)
        results = search.get_dict()
        
        # Extract news results
        news_results = results.get("news_results", [])
        if not news_results:
            # Fallback to organic results if no news results
            news_results = results.get("organic_results", [])
        
        logger.info(f"Found {len(news_results)} initial results for query: {query}")
        
        # Extract relevant information
        news_items = []
        filtered_out = 0
        
        for item in news_results:
            # Extract publication date if available
            pub_date = item.get("date", "")
            
            # Verify the publication date is within the past week
            is_recent = True
            if pub_date:
                try:
                    # SerpAPI often returns relative dates like "2 days ago"
                    if "ago" in pub_date.lower():
                        # It's already recent, no need to parse
                        pass
                    else:
                        # Try to parse the date
                        article_date = date_parser.parse(pub_date)
                        # Check if article is within the past 7 days
                        if (today - article_date).days > 7:
                            is_recent = False
                            filtered_out += 1
                            logger.debug(f"Filtered out article from {article_date.strftime('%Y-%m-%d')} (too old)")
                except Exception as date_error:
                    logger.debug(f"Could not parse date '{pub_date}': {str(date_error)}")
            
            if is_recent:
                # Extract publisher/source
                source = item.get("source", "")
                if not source:
                    # Try to extract from link if source is not available
                    link = item.get("link", "")
                    if link:
                        source = link.split("//")[-1].split("/")[0]
                        source = source.replace("www.", "")
                
                news_items.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "publisher": source,
                    "date": pub_date,
                    "query": query,  # Store the query that found this item for context
                    "market": "global" if is_global else "indian"  # Add market type
                })
        
        logger.info(f"Kept {len(news_items)} recent news items, filtered out {filtered_out} older items")
        return news_items
    except Exception as e:
        logger.error(f"Error in SerpAPI search: {str(e)}")
        return []

def search_financial_news(interests: UserInterests, is_global: bool = False) -> List[Dict[str, Any]]:
    """Search for financial news based on user interests using SerpAPI."""
    all_news = []
    
    # General financial news
    if is_global:
        general_query = "global stock market financial news"
    else:
        general_query = "Indian stock market financial news"
    
    all_news.extend(serpapi_search(general_query, 5, is_global))
    
    # News from specific sources
    if is_global:
        sources = ["Bloomberg", "Financial Times", "Wall Street Journal", "CNBC"]
    else:
        sources = ["Economic Times", "Moneycontrol", "Livemint", "Business Standard"]
    
    for source in sources:
        source_news = serpapi_search(f"site:{source.lower().replace(' ', '')}.com finance", 2, is_global)
        all_news.extend(source_news)
    
    # News related to user interests
    if interests.topics:
        for topic in interests.topics[:3]:  # Limit to top 3 topics
            topic_news = serpapi_search(f"{topic} finance", 2, is_global)
            all_news.extend(topic_news)
    
    # Add custom topics with higher priority
    if interests.custom_topics:
        for topic in interests.custom_topics:
            custom_topic_news = serpapi_search(f"{topic} finance", 3, is_global)
            all_news.extend(custom_topic_news)
    
    if interests.sectors:
        for sector in interests.sectors[:3]:  # Limit to top 3 sectors
            sector_news = serpapi_search(f"{sector} sector market", 2, is_global)
            all_news.extend(sector_news)
    
    if interests.companies:
        for company in interests.companies[:3]:  # Limit to top 3 companies
            company_news = serpapi_search(f"{company} stock", 2, is_global)
            all_news.extend(company_news)
    
    # Add some market statistics
    if is_global:
        stats_news = serpapi_search("S&P 500 Dow Jones market statistics", 3, is_global)
    else:
        stats_news = serpapi_search("Sensex Nifty market statistics", 3, is_global)
    
    all_news.extend(stats_news)
    
    # Add some market analysis
    if is_global:
        analysis_news = serpapi_search("global market analysis forecast", 3, is_global)
    else:
        analysis_news = serpapi_search("Indian market analysis forecast", 3, is_global)
    
    all_news.extend(analysis_news)
    
    # Filter out duplicates
    return filter_duplicate_news(all_news)

def filter_duplicate_news(news_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter out duplicate news items based on title similarity."""
    filtered_news = []
    seen_titles = set()
    
    for item in news_items:
        title = item.get("title", "").lower()
        
        # Skip if title is too short
        if len(title) < 10:
            continue
        
        # Check for near-duplicates
        is_duplicate = False
        for seen_title in seen_titles:
            # Simple similarity check - if more than 70% of words are the same
            title_words = set(title.split())
            seen_words = set(seen_title.split())
            
            if len(title_words) == 0:
                is_duplicate = True
                break
            
            common_words = title_words.intersection(seen_words)
            similarity = len(common_words) / len(title_words)
            
            if similarity > 0.7:
                is_duplicate = True
                break
        
        if not is_duplicate:
            seen_titles.add(title)
            filtered_news.append(item)
    
    return filtered_news

def generate_financial_newsletter_with_openai(
    news_items: List[Dict[str, Any]], 
    interests: UserInterests, 
    profile: UserProfile,
    is_global: bool = False
) -> str:
    """Generate a personalized financial newsletter using OpenAI with recent news only."""
    logger.info("Generating newsletter with OpenAI")
    
    # Get the date range for the week
    today = datetime.datetime.now()
    week_start = (today - datetime.timedelta(days=7)).strftime("%d %b %Y")
    week_end = today.strftime("%d %b %Y")
    
    # Prepare the news data
    news_data = ""
    for i, item in enumerate(news_items[:15]):  # Limit to 15 news items
        news_data += f"[{i+1}] Title: {item.get('title', '')}\n"
        news_data += f"    Source: {item.get('publisher', '')}\n"
        news_data += f"    Summary: {item.get('snippet', '')}\n"
        news_data += f"    Link: {item.get('link', '')}\n"
        if item.get('date'):
            news_data += f"    Published: {item.get('date')}\n"
        news_data += f"    Found via search: {item.get('query', 'general search')}\n\n"
    
    # Extract goal details for personalization
    goal_details = ""
    if profile.goal_details:
        goal_details = "Specific Financial Goals:\n"
        
        # Retirement goal
        if "retirement" in profile.goal_details:
            retirement = profile.goal_details["retirement"]
            goal_details += f"- Retirement: Planning to retire at age {retirement.get('target_age', 60)}, "
            goal_details += f"needs monthly income of INR {retirement.get('monthly_income_needed', 50000):,}, "
            goal_details += f"current retirement savings: INR {retirement.get('current_retirement_savings', 0):,}\n"
        
        # Education goal
        if "education" in profile.goal_details:
            education = profile.goal_details["education"]
            goal_details += f"- Education Funding: Target amount INR {education.get('target_amount', 1000000):,}, "
            goal_details += f"within {education.get('years_remaining', 5)} years, "
            goal_details += f"current savings: INR {education.get('current_savings', 0):,}\n"
        
        # Home purchase goal
        if "home_purchase" in profile.goal_details:
            home = profile.goal_details["home_purchase"]
            goal_details += f"- Home Purchase: Down payment target INR {home.get('target_amount', 2000000):,}, "
            goal_details += f"within {home.get('years_remaining', 3)} years, "
            goal_details += f"current savings: INR {home.get('current_savings', 0):,}\n"
    
    # Prepare the system prompt
    if is_global:
        market_focus = "global markets"
        market_indices = "major global indices like S&P 500, NASDAQ, Dow Jones, FTSE, Nikkei, etc."
    else:
        market_focus = "Indian markets"
        market_indices = "Indian indices like Sensex, Nifty, etc."
    
    system_prompt = f"""
    You are an expert {market_focus} financial analyst writing a personalized weekly newsletter.
    Your task is to create a comprehensive, well-structured newsletter that covers ONLY THE MOST RECENT financial news
    from the PAST WEEK, with a focus on the recipient's specific interests and financial goals.
    
    The newsletter should include:
    1. A brief market overview for the past week (specifically the last 7 days) focusing on {market_focus}
    2. Analysis of key recent news items, organized by relevance to the user's interests
    3. Sector-specific insights based on the user's interests
    4. Investment recommendations aligned with the user's risk profile and financial goals
    5. A dedicated section addressing the user's specific financial goals with actionable advice
    6. A short outlook for the coming week
    
    Emphasize the recency of the information - all news should be from the past week only.
    MAKE SURE TO CITE SOURCES AND INCLUDE LINKS TO THE ORIGINAL ARTICLES.
    
    Use a professional but accessible tone. Include specific numbers, percentages, and data points when available.
    Format the newsletter in Markdown with clear sections, bullet points, and occasional emphasis.
    
    When discussing market performance, reference {market_indices}.
    
    Do not sign the newsletter or include any personal information about yourself.
    """
    
    # Prepare the user prompt with personalization
    user_prompt = f"""
    Generate a personalized financial newsletter for {profile.name}, an investor with the following profile:
    
    INTERESTS:
    - Topics of interest: {', '.join(interests.topics)}
    - Market sectors: {', '.join(interests.sectors)}
    - Preferred investment types: {', '.join(interests.investment_types)}
    - Risk profile: {interests.risk_profile}
    - Time horizon: {interests.time_horizon}
    
    CUSTOM TOPICS SPECIFICALLY REQUESTED:
    {', '.join(interests.custom_topics) if interests.custom_topics else 'None specified'}
    
    FINANCIAL GOALS:
    {', '.join(profile.financial_goals) if profile.financial_goals else 'None specified'}
    
    {goal_details}
    
    Here are the recent news items from the past week ({week_start} to {week_end}) to incorporate:
    {news_data}
    
    Create a comprehensive newsletter that analyzes these RECENT news items in the context of the investor's interests and goals.
    Focus on the most relevant stories, provide insights, and suggest potential investment actions aligned with their risk profile.
    
    Make sure to include a dedicated section titled "YOUR FINANCIAL GOALS" that provides specific advice related to their stated goals.
    
    Make sure to emphasize that all information is current and from the past week only.
    """
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=2500
        )
        newsletter_content = response.choices[0].message.content
        
        # Add a header with the date range and market focus
        market_type = "Global" if is_global else "Indian"
        header = f"# {market_type} Financial Markets Weekly Newsletter\n## {week_start} - {week_end}\n\n"
        
        # Add a personalized greeting
        greeting = f"Dear {profile.name},\n\nHere's your personalized financial newsletter based on your interests and goals.\n\n"
        
        return header + greeting + newsletter_content
    except Exception as e:
        logger.error(f"Error generating newsletter with OpenAI: {str(e)}")
        market_type = "Global" if is_global else "Indian"
        return f"# {market_type} Financial Markets Weekly Newsletter\n## {week_start} - {week_end}\n\nWe apologize, but we encountered an error while generating your newsletter. Please try again later."

def generate_personalized_news(profile: UserProfile, custom_topics: List[str] = None, is_global: bool = False) -> str:
    """Generate a personalized financial newsletter based on user profile."""
    # Create a progress bar
    progress_bar = st.progress(0)
    
    # Phase 1: Extract interests
    logger.info(f"Generating newsletter for {profile.name} (Market focus: {'Global' if is_global else 'Indian'})")
    progress_bar.progress(10)
    
    # Update profile with custom topics if provided
    if custom_topics:
        if not hasattr(profile, 'custom_topics'):
            profile.custom_topics = []
        profile.custom_topics = custom_topics
    # Try to extract interests from structured data first
    interests = extract_interests_from_json(profile)
    
    # If we don't have enough data, use OpenAI
    if len(interests.topics) <= 3 and profile.free_text_description:
        interests = extract_interests_with_openai(profile)
    
    # Add custom topics to interests
    if custom_topics:
        interests.custom_topics = custom_topics
    
    logger.info(f"Extracted interests: {interests.dict()}")
    progress_bar.progress(30)
    
    # Phase 2: Collect and filter news
    logger.info(f"Collecting news articles (Market focus: {'Global' if is_global else 'Indian'})")
    news_items = search_financial_news(interests, is_global)
    logger.info(f"Collected {len(news_items)} news items after filtering")
    progress_bar.progress(60)
    
    # Save the raw news data
    market_type = "global" if is_global else "indian"
    output_file = OUTPUT_DIR / f"raw_news_data_{market_type}_{datetime.datetime.now().strftime('%Y%m%d')}.json"
    with output_file.open('w', encoding='utf-8') as f:
        json.dump(news_items, f, indent=2, ensure_ascii=False)
    
    # Phase 3: Generate the newsletter
    logger.info("Generating personalized newsletter")
    newsletter = generate_financial_newsletter_with_openai(news_items, interests, profile, is_global)
    progress_bar.progress(90)
    
    # Save the newsletter
    today = datetime.datetime.now()
    week_start = (today - datetime.timedelta(days=7)).strftime("%Y%m%d")
    week_end = today.strftime("%Y%m%d")
    filename = OUTPUT_DIR / f"financial_newsletter_{market_type}_{week_start}_{week_end}.md"
    
    # Use UTF-8 encoding when writing to file
    with filename.open('w', encoding='utf-8') as f:
        f.write(newsletter)
    
    logger.info(f"Newsletter saved to {filename}")
    progress_bar.progress(100)
    
    return newsletter

# Email functionality
def load_subscribers() -> List[str]:
    """Load the list of newsletter subscribers."""
    subscribers_file = OUTPUT_DIR / "subscribers.json"
    if subscribers_file.exists():
        try:
            return json.loads(subscribers_file.read_text())
        except json.JSONDecodeError:
            return []
    return []

def save_subscriber(email: str) -> None:
    """Save a new subscriber to the list."""
    subscribers = load_subscribers()
    if email not in subscribers:
        subscribers.append(email)
    
    subscribers_file = OUTPUT_DIR / "subscribers.json"
    subscribers_file.write_text(json.dumps(subscribers))

def send_newsletter_via_email(newsletter_content: str, recipient_email: str, is_global: bool = False) -> bool:
    """Send the newsletter to a subscriber via email."""
    try:
        # Log the email configuration for debugging
        logger.info(f"Attempting to send email to {recipient_email}")
        logger.info(f"Using email server: {EMAIL_HOST}:{EMAIL_PORT}")
        logger.info(f"Using sender address: {EMAIL_FROM}")
        
        # Get the date range for the week
        today = datetime.datetime.now()
        week_start = (today - datetime.timedelta(days=7)).strftime("%d %b %Y")
        week_end = today.strftime("%d %b %Y")
        
        # Create the email
        msg = MIMEMultipart("alternative")
        market_type = "Global" if is_global else "Indian"
        msg["Subject"] = f"{market_type} Financial Markets Weekly Newsletter: {week_start} - {week_end}"
        msg["From"] = EMAIL_FROM
        msg["To"] = recipient_email
        
        # Convert markdown to HTML
        html_content = markdown.markdown(newsletter_content)
        
        # Add some basic styling
        styled_html = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
                h1 {{ color: #005e7c; }}
                h2 {{ color: #005e7c; }}
                h3 {{ color: #005e7c; }}
                a {{ color: #cf352f; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #777; border-top: 1px solid #ddd; padding-top: 10px; }}
                .highlight {{ color: #cf352f; font-weight: bold; }}
                .goal-section {{ background-color: rgba(207, 53, 47, 0.05); border-left: 3px solid #cf352f; padding: 15px; margin: 15px 0; }}
            </style>
        </head>
        <body>
            {html_content}
            <div class="footer">
                <p>This newsletter is generated based on recent financial news and your interests.</p>
                <p>(c) {today.year} {market_type} Financial Markets Newsletter</p>
            </div>
        </body>
        </html>
        """
        
        # Attach parts with explicit UTF-8 encoding
        text_part = MIMEText(newsletter_content, "plain", "utf-8")
        html_part = MIMEText(styled_html, "html", "utf-8")
        msg.attach(text_part)
        msg.attach(html_part)
        
        # Send the email with more detailed error handling
        logger.info("Connecting to email server...")
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            # Enable debug output
            server.set_debuglevel(1)
            logger.info("Starting TLS...")
            server.starttls()
            logger.info("Attempting login...")
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            logger.info("Sending message...")
            server.send_message(msg)
        
        logger.info(f"Newsletter successfully sent to {recipient_email}")
        return True
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"Authentication failed: {str(e)}")
        st.error(f"Email authentication failed. Please check your username and password.")
        return False
    except smtplib.SMTPConnectError as e:
        logger.error(f"Connection to the SMTP server failed: {str(e)}")
        st.error(f"Could not connect to the email server. Please check your internet connection and server settings.")
        return False
    except smtplib.SMTPServerDisconnected as e:
        logger.error(f"Server disconnected: {str(e)}")
        st.error(f"The email server unexpectedly disconnected. Please try again later.")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error: {str(e)}")
        st.error(f"An error occurred while sending the email: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error sending email to {recipient_email}: {str(e)}")
        st.error(f"Failed to send email: {str(e)}")
        return False

# Streamlit app
def main():
    st.set_page_config(
        page_title="Personalized Financial Market Newsletters",
        page_icon="[Trend]",
        layout="wide"
    )
    
    load_css()
    
    with st.sidebar:
        st.image("logo2.png", width=150)
        st.title("Personalized Financial Market Newsletters")
        
        # Check if SerpAPI key is configured
        if not SERPAPI_API_KEY:
            st.error("[WARN] SerpAPI API key is not configured. Please add SERPAPI_API_KEY to your .env file.")
            st.stop()
        
        # Sidebar for email subscription
        st.sidebar.header("Subscribe to Newsletter")
        subscriber_email = st.sidebar.text_input("Enter your email to subscribe:")
        if st.sidebar.button("Subscribe"):
            if re.match(r"[^@]+@[^@]+\.[^@]+", subscriber_email):
                save_subscriber(subscriber_email)
                st.sidebar.success(f"[OK] {subscriber_email} subscribed successfully!")
            else:
                st.sidebar.error("Please enter a valid email address.")
    
    # Market mode toggle at the top of the main area
    st.markdown('<div class="market-toggle">', unsafe_allow_html=True)
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("Market Focus")
        st.write("Choose which market to focus on for your newsletter")
    with col2:
        market_mode = st.radio(
            "Select Market Focus:",
            ["Indian Market", "Global Market"],
            index=0,
            key="market_mode"
        )
    is_global = market_mode == "Global Market"
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Main tabs
    tab1, tab2, tab3 = st.tabs(["User Profile", "Interest Analysis", "Generate Weekly Newsletter"])
    with tab1:
        st.header("User Profile")
        st.markdown("### Upload Your Financial Profile")
        uploaded_file = st.file_uploader("Upload profile JSON file", type=["json"])
        
        if uploaded_file is not None:
            try:
                # Read the file content
                file_content = uploaded_file.read().decode("utf-8")

                # Load the profile
                profile = load_profile_from_file(file_content)

                # Display profile summary
                st.success("Profile loaded successfully!")
                st.subheader("Profile Summary")

                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Name:** {profile.name}")
                    st.write(f"**Age:** {profile.age if profile.age else 'Not specified'}")
                    st.write(f"**Risk Appetite:** {profile.risk_appetite if profile.risk_appetite else 'Not specified'}")

                with col2:
                    st.write("**Financial Goals:**")
                    if profile.financial_goals:
                        for goal in profile.financial_goals:
                            st.markdown(f'<span class="custom-tag">{goal}</span>', unsafe_allow_html=True)
                    else:
                        st.write("No goals specified")

                # Show assets and liabilities if available
                if profile.assets or profile.liabilities:
                    st.subheader("Financial Summary")
                    col1, col2 = st.columns(2)

                    with col1:
                        if profile.assets:
                            st.write("**Assets:**")
                            for asset, value in profile.assets.items():
                                if value > 0:
                                    st.write(f"- {asset.replace('_', ' ').title()}: INR {value:,}")

                    with col2:
                        if profile.liabilities:
                            st.write("**Liabilities:**")
                            for liability, value in profile.liabilities.items():
                                if value > 0 and not liability.endswith("_rate") and not liability.endswith("_years"):
                                    st.write(f"- {liability.replace('_', ' ').title()}: INR {value:,}")

                # Custom topics input
                st.subheader("Add Custom Topics of Interest")
                st.markdown('<div class="custom-topic-input">', unsafe_allow_html=True)
                custom_topics_input = st.text_area(
                    "Enter additional topics you're interested in (one per line):",
                    help="These topics will be prioritized in your newsletter"
                )

                if custom_topics_input:
                    custom_topics = [topic.strip() for topic in custom_topics_input.split('\n') if topic.strip()]
                    if not hasattr(profile, 'custom_topics'):
                        profile.custom_topics = []
                    profile.custom_topics = custom_topics

                    st.write("**Your Custom Topics:**")
                    for topic in custom_topics:
                        st.markdown(f'<span class="custom-tag">{topic}</span>', unsafe_allow_html=True)

                st.markdown('</div>', unsafe_allow_html=True)

                # Save to session state
                st.session_state.user_profile = profile
            except Exception as e:
                st.error(f"Error loading profile: {str(e)}")

        
    with tab2:
        st.header("Your Interest Analysis")
        
        if "user_profile" in st.session_state:
            profile = st.session_state.user_profile
            
            # Extract interests
            interests = extract_interests_from_json(profile)
            
            # If we don't have enough data, use OpenAI
            if len(interests.topics) <= 3 and profile.free_text_description:
                if st.button("Analyze with AI"):
                    with st.spinner("Analyzing your interests with AI..."):
                        interests = extract_interests_with_openai(profile)
                    st.session_state.user_interests = interests
            else:
                st.session_state.user_interests = interests
            
            if "user_interests" in st.session_state:
                interests = st.session_state.user_interests
                
                # Display market mode
                st.markdown(f"**Market Focus:** {'Global Markets' if is_global else 'Indian Markets'}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Topics of Interest")
                    for topic in interests.topics:
                        st.markdown(f'<span class="custom-tag">{topic}</span>', unsafe_allow_html=True)
                    
                    if interests.custom_topics:
                        st.subheader("Your Custom Topics")
                        for topic in interests.custom_topics:
                            st.markdown(f'<span class="custom-tag">{topic}</span>', unsafe_allow_html=True)
                    
                    st.subheader("Market Sectors")
                    for sector in interests.sectors:
                        st.markdown(f'<span class="custom-tag">{sector}</span>', unsafe_allow_html=True)
                
                with col2:
                    # st.subheader("Companies of Interest")
                    # if interests.companies:
                    #     for company in interests.companies:
                    #         st.markdown(f'<span class="custom-tag">{company}</span>', unsafe_allow_html=True)
                    # else:
                    #     st.write("No specific companies identified.")
                    
                    st.subheader("Investment Preferences")
                    st.write(f"**Risk Profile:** {interests.risk_profile}")
                    st.write(f"**Time Horizon:** {interests.time_horizon}")
                    st.write("**Preferred Investment Types:**")
                    for inv_type in interests.investment_types:
                        st.markdown(f'<span class="custom-tag">{inv_type}</span>', unsafe_allow_html=True)
                
                # Allow editing custom topics
                st.subheader("Edit Custom Topics")
                st.markdown('<div class="custom-topic-input">', unsafe_allow_html=True)
                
                # Pre-fill with existing custom topics
                existing_topics = "\n".join(interests.custom_topics) if interests.custom_topics else ""
                
                updated_topics_input = st.text_area(
                    "Update your custom topics (one per line):",
                    value=existing_topics,
                    key="update_topics"
                )
                
                if st.button("Update Topics"):
                    updated_topics = [topic.strip() for topic in updated_topics_input.split('\n') if topic.strip()]
                    interests.custom_topics = updated_topics
                    profile.custom_topics = updated_topics
                    st.session_state.user_interests = interests
                    st.session_state.user_profile = profile
                    st.success("Custom topics updated successfully!")
                
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("Please load or create a profile in the User Profile tab first.")
    
    with tab3:
        st.header("Generate Weekly Newsletter")
        
        if "user_profile" in st.session_state:
            # Display market mode
            st.markdown(f"**Current Market Focus:** {'Global Markets' if is_global else 'Indian Markets'}")
            st.write("You can change the market focus using the toggle at the top of the page.")
            
            # Get custom topics if they exist
            custom_topics = None
            if hasattr(st.session_state.user_profile, 'custom_topics') and st.session_state.user_profile.custom_topics:
                custom_topics = st.session_state.user_profile.custom_topics
            
            if st.button("Generate Newsletter"):
                with st.spinner(f"Generating your personalized {'global' if is_global else 'Indian'} financial newsletter..."):
                    newsletter = generate_personalized_news(
                        st.session_state.user_profile, 
                        custom_topics=custom_topics,
                        is_global=is_global
                    )
                    st.session_state.newsletter = newsletter
                    st.session_state.newsletter_is_global = is_global
            
            if "newsletter" in st.session_state:
                st.markdown(st.session_state.newsletter)
                
                # Download button
                today = datetime.datetime.now()
                week_start = (today - datetime.timedelta(days=7)).strftime("%Y%m%d")
                week_end = today.strftime("%Y%m%d")
                market_type = "global" if st.session_state.newsletter_is_global else "indian"
                filename = f"financial_newsletter_{market_type}_{week_start}_{week_end}.md"
                
                st.download_button(
                    label="Download Newsletter",
                    data=st.session_state.newsletter,
                    file_name=filename,
                    mime="text/markdown"
                )
                
                # Email newsletter option
                st.subheader("Email Newsletter")
                recipient_email = st.text_input("Email address to send newsletter to:")
                
                if st.button("Send Newsletter"):
                    if re.match(r"[^@]+@[^@]+\.[^@]+", recipient_email):
                        with st.spinner("Sending newsletter..."):
                            success = send_newsletter_via_email(
                                st.session_state.newsletter, 
                                recipient_email,
                                st.session_state.newsletter_is_global
                            )
                            if success:
                                st.success(f"Newsletter sent to {recipient_email} successfully!")
                            else:
                                st.error("Failed to send newsletter. Check the logs for details.")
                    else:
                        st.error("Please enter a valid email address.")
        else:
            st.info("Please load or create a profile in the User Profile tab first.")
    
    # Display logs in an expander at the bottom
    with st.expander("View Logs"):
        st.code(log_stream.getvalue())

if __name__ == "__main__":
    main()
