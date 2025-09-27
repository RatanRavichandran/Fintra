# Bridging India's Financial Literacy Gap

## The Problem We're Solving

India faces a critical financial literacy crisis. Despite being one of the world's fastest-growing economies, millions of Indian households struggle with basic financial planning, often making suboptimal decisions about savings, investments, and debt management. The challenges are multifaceted:

- **Limited Access to Professional Advice**: Traditional financial advisors are expensive and often inaccessible to middle-class families
- **Information Overload**: The financial landscape is complex with thousands of mutual funds, government schemes, and investment options
- **Cultural Barriers**: Many Indians lack confidence in financial decision-making due to limited exposure to financial concepts
- **Fragmented Tools**: Existing solutions are either too basic (simple calculators) or too complex (professional-grade platforms)
- **Lack of Personalization**: Generic advice doesn't account for Indian tax laws, cultural preferences, and local investment vehicles

This results in poor financial outcomes: inadequate retirement savings, high debt burdens, missed investment opportunities, and financial stress that affects millions of families.

## Our Solution: A Hyperpersonalized Financial Companion

Your Finance Planner is a comprehensive, personal finance platform designed specifically for Indian households. We've built a complete ecosystem that transforms complex financial planning into an accessible, personalized experience.

### Core Platform Features

#### 🎯 **Intelligent Profile Setup**
- **Conversational Onboarding**: Interactive questionnaire that adapts based on user responses
- **Comprehensive Data Collection**: Captures personal details, income streams, expenses, assets, liabilities, and financial goals
- **Smart Defaults**: Pre-populated with Indian-specific options (EPF, PPF, NPS, etc.)
- **Profile Import/Export**: JSON-based profile management for easy backup and sharing

#### 🤖 **AI-Powered Financial Planning**
- **Multi-Agent Architecture**: Specialized AI agents for different aspects of financial planning
  - **Research Agent**: Curates real-time market intelligence from trusted sources
  - **Financial Planner**: Creates personalized budgets and savings strategies
  - **Investment Advisor**: Recommends Indian-specific investment vehicles
  - **Debt Manager**: Analyzes liabilities and creates repayment strategies
  - **Subscription Optimizer**: Identifies cost-saving opportunities in recurring expenses
- **Indian Context Awareness**: All recommendations consider Indian tax laws, cultural preferences, and local investment options
- **Citation-Based Advice**: Every recommendation includes sources and references for transparency

#### 📊 **Advanced Retirement Planning**
- **Monte Carlo Simulations**: Runs 1000+ scenarios to project retirement outcomes
- **Risk-Adjusted Projections**: Considers user's risk tolerance and market volatility
- **Interactive Visualizations**: Plotly-powered charts showing wealth accumulation over time
- **Interpretation**: Natural language explanations of complex financial projections
- **Goal Tracking**: Monitors progress toward retirement income targets

#### 📈 **Investment Management**
- **Fund Analysis**: Integration with AMFI data for comprehensive mutual fund research
- **Risk Profiling**: Maps user risk tolerance to appropriate investment categories
- **Portfolio Recommendations**: Diversified investment suggestions based on age, income, and goals
- **Performance Tracking**: Historical analysis and future projections

#### 💳 **Debt & Subscription Optimization**
- **Debt Consolidation**: Analyzes multiple loans and suggests optimal repayment strategies
- **Subscription Audit**: Identifies redundant or underutilized recurring expenses
- **Savings Calculator**: Quantifies potential savings from optimization recommendations
- **Actionable Insights**: Clear next steps for implementing recommendations

#### 📧 **Financial Newsletter Studio**
- **Personalized Content**: Hypersonalized newsletters based on user interests and portfolio
- **Market Intelligence**: Weekly briefings with Indian market context
- **Email Automation**: Automated delivery with customizable templates
- **Export Options**: PDF and HTML formats for offline reading

#### 🔧 **Data Integration & Automation**
- **Government Scheme Scraper**: Automated extraction of benefits from myscheme.gov.in
- **AMFI Data Pipeline**: Automated mutual fund data updates
- **Knowledge Base**: FAISS-powered vector database for financial research
- **API Integrations**: SerpAPI for real-time market research, OpenAI for intelligent analysis

### Technical Architecture

The platform is built with modern, scalable technologies:

- **Frontend**: Streamlit for rapid prototyping and user-friendly interfaces
- **AI/ML**: OpenAI GPT-4, CrewAI and Agno Agent frameworks for intelligent analysis
- **Data Processing**: Pandas and NumPy for financial calculations and Monte Carlo simulations
- **Visualization**: Plotly for interactive charts and financial projections
- **Search & Research**: SerpAPI for real-time market intelligence
- **Vector Database**: FAISS for efficient financial knowledge retrieval
- **Web Scraping**: Selenium and BeautifulSoup for automated data collection
- **Email Automation**: SMTP integration for newsletter delivery

### Impact & Vision

Your Finance Planner addresses the core challenges facing Indian households:

- **Democratizes Financial Advice**: Makes professional-grade financial planning accessible to everyone
- **Reduces Information Asymmetry**: Provides transparent, citation-backed recommendations
- **Improves Financial Outcomes**: Helps users make informed decisions about savings, investments, and debt
- **Builds Financial Confidence**: Educates users through personalized, contextual guidance
- **Scales Financial Literacy**: Creates a foundation for better financial decision-making across India

## Repository Layout
```
app/
  agents.py               # Agent definitions with configuration guards
  config.py               # Centralised settings and path helpers
  Home.py                 # Streamlit landing page
  lib/                    # Simulation + utility helpers
  pages/                  # Streamlit multipage workflows (profile, planner, debt, etc.)
  assets/                 # UI assets (logos)
  data/                   # Questions, sample profiles, and reference sheets
  finance_knowledge_base/ # Research artefacts captured during the hackathon
  finance_docs/           # Quick reference finance copy
  newslettersub_FINAL.py  # Newsletter generator experience
  ui.py                   # Shared CSS / branding helpers
  .env.example            # Template for local secrets
  .streamlit/config.toml  # Theme configuration
  .streamlit/secrets.example.toml
scripts/
  clean_policy_content.py         # Clean policy pages via crawl4ai + OpenAI
  policy_scheme_extractor.py      # Structured scraper for myscheme.gov.in
  demo_crawler.py                 # Minimal crawl4ai usage example
  selenium_download_amfi.py       # Selenium automation to download AMFI fund data
data/
  reference/user_profiles.xlsx    # Sample policybot dataset
  sample_profiles/                # JSON/TXT examples for quick testing
docs/
  UIP.pdf                         # Hackathon context deck
requirements.txt
.gitignore
README.md
```

## Getting Started

### Prerequisites
- Python 3.8 or higher
- OpenAI API key 
- SerpAPI key (for market research)
- Email credentials (for newsletter functionality)

### Installation

1. **Clone and Setup Environment**
   ```bash
   git clone <repository-url>
   cd UIP
   python -m venv .venv
   
   # Activate virtual environment
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # macOS/Linux
   
   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Configure API Keys**
   
   **Option A: Environment Variables**
   ```bash
   # Copy the example file
   cp app/.env.example app/.env
   
   # Edit app/.env with your API keys
   OPENAI_API_KEY=your_openai_key_here
   SERPAPI_API_KEY=your_serpapi_key_here
   EMAIL_HOST=smtp.gmail.com
   EMAIL_USER=your_email@gmail.com
   EMAIL_PASSWORD=your_app_password
   ```
   
   **Option B: Streamlit Secrets**
   ```bash
   # Copy the example file
   cp app/.streamlit/secrets.example.toml app/.streamlit/secrets.toml
   
   # Edit app/.streamlit/secrets.toml with your credentials
   ```

3. **Launch the Application**
   ```bash
   streamlit run app/Home.py
   ```
   
   The app will open in your browser at `http://localhost:8501`

### First Steps

1. **Complete Profile Setup**: Navigate to "Profile Setup" and fill in your financial information
2. **Generate Financial Plan**: Use the "Financial Planner" to get personalized recommendations
3. **Explore Investment Options**: Check the "Investment Manager" for fund recommendations
4. **Analyze Your Debt**: Review the "Debt Manager" for optimization strategies
5. **Plan for Retirement**: Use the "Retirement Planner" for long-term projections

### Optional: Data Ingestion Scripts

Run these scripts to populate the system with fresh data:

```bash
# Download AMFI mutual fund data
python scripts/selenium_download_amfi.py

# Extract government schemes
python scripts/policy_scheme_extractor.py

# Clean and process policy content
python scripts/clean_policy_content.py
```

## Configuration & Data

### Configuration Management
- All sensitive configuration is managed through `app/config.py`
- Supports multiple configuration methods: Streamlit secrets, environment variables, or `.env` files
- No live API keys are included in the repository for security

### Sample Data
- **Sample Profiles**: Pre-built user profiles in `app/data/sample_profiles/` for quick testing
- **Reference Data**: `data/reference/user_profiles.xlsx` contains research datasets
- **Knowledge Base**: FAISS vector database in `app/finance_knowledge_base/` for financial research
- **Fund Data**: Excel files with mutual fund information for investment analysis

### Output Directories
- Newsletters: `app/data/newsletter_output/` (created automatically)
- User profiles: Stored in session state (can be exported as JSON)
- Simulation results: Generated on-demand with interactive visualizations

## Research & Context

The complete research foundation, including problem analysis, user personas, market sizing, and solution design, is documented in `docs/UIP.pdf`. This comprehensive deck outlines:

- **Market Research**: Analysis of financial literacy gaps in India
- **User Personas**: Detailed profiles of target users (seniors, youth, working professionals)
- **Competitive Analysis**: Evaluation of existing financial planning tools
- **Solution Design**: Technical architecture and feature prioritization
- **Impact Projections**: Expected outcomes and scalability considerations

## Development Roadmap

### Immediate Priorities
- **Persistent Storage**: Implement database integration (Supabase/MongoDB) for user profiles
- **Enhanced AI**: Replace basic agents with retrieval-augmented generation (RAG) systems
- **Testing Suite**: Comprehensive unit and integration tests for simulation engines
- **Performance Optimization**: Caching and async processing for better user experience

### Future Enhancements
- **Mobile App**: React Native or Flutter mobile application
- **API Platform**: RESTful API for third-party integrations
- **Advanced Analytics**: Machine learning models for personalized recommendations
- **Social Features**: Community-driven financial advice and peer comparisons
- **Regulatory Compliance**: Integration with Indian financial regulations and compliance requirements

## Contributing

We welcome contributions to improve! Areas where we need help:

- **Financial Expertise**: Domain knowledge for better Indian market insights
- **UI/UX Design**: Improved user interfaces and user experience flows
- **Documentation**: Enhanced guides and tutorials
- **Localization**: Support for regional languages

This project was developed during the UIP Hackathon.

## Contributors
Sayli Jain, Sri Bharath Sharma P, AV Saipriya

## Support

For questions, issues, or contributions, please refer to the project documentation or create an issue in the repository.
