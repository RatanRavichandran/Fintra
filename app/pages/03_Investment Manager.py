from textwrap import dedent
import streamlit as st
from ui import apply_global_styles
from agno.agent import Agent
from agno.tools.serpapi import SerpApiTools
from agno.models.openai import OpenAIChat
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import pandas as pd
import numpy as np
import json
import plotly.express as px
import json
import tiktoken
from agents import investment_advisor


apply_global_styles()



# ensure our session-state keys exist
if "_last_inv_prompt" not in st.session_state:
    st.session_state._last_inv_prompt = ""
if "investment_plan" not in st.session_state:
    st.session_state.investment_plan = None
st.header("Investment Manager")

# Check if user has completed profile
if not st.session_state.user_data['personal'].get('name'):
    st.warning("Please complete your profile setup first to receive investment recommendations.")
else:
    tabs = st.tabs(["Overview", "Investment Recommendations", "Portfolio Analysis"])
    
    with tabs[0]:
        st.markdown('<div class="sub-header">Investment Overview</div>', unsafe_allow_html=True)
        
        # Calculate investment metrics
        total_investments = (
            st.session_state.user_data['assets'].get('cash', 0) +
            st.session_state.user_data['assets'].get('equity', 0) +
            st.session_state.user_data['assets'].get('epf_ppf', 0) +
            st.session_state.user_data['assets'].get('real_estate', 0) +
            st.session_state.user_data['assets'].get('gold', 0) +
            st.session_state.user_data['assets'].get('other_assets', 0)
        )
        
        monthly_income = sum([
            st.session_state.user_data['income'].get('primary_income', 0),
            st.session_state.user_data['income'].get('secondary_income', 0),
            st.session_state.user_data['income'].get('other_income', 0)
        ])
        
        # Calculate investment ratios
        investment_to_income_ratio = total_investments / (monthly_income * 12) if monthly_income > 0 else 0
        
        # Display investment summary cards
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="card">
                <h3>Investment Portfolio</h3>
                <p><strong>Total Investments:</strong> INR {total_investments:,.2f}</p>
                <p><strong>Portfolio to Annual Income Ratio:</strong> {investment_to_income_ratio:.2f}x</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Calculate equity percentage
            equity_percentage = (st.session_state.user_data['assets'].get('equity', 0) / total_investments) * 100 if total_investments > 0 else 0
            
            # Get risk profile and recommended equity allocation
            user_risk = st.session_state.user_data['personal'].get('risk_tolerance', 'Moderate')
            recommended_equity = {
                "Very Conservative": 20,
                "Conservative": 30,
                "Moderate": 50,
                "Aggressive": 70,
                "Very Aggressive": 80
            }.get(user_risk, 50)
            
            st.markdown(f"""
            <div class="card">
                <h3>Risk Profile</h3>
                <p><strong>Risk Tolerance:</strong> {user_risk}</p>
                <p><strong>Current Equity Allocation:</strong> {equity_percentage:.1f}%</p>
                <p><strong>Recommended Equity:</strong> {recommended_equity}%</p>
                <p><strong>Alignment:</strong> {'Good [OK]' if abs(equity_percentage - recommended_equity) < 10 else 'Needs Adjustment [WARN]'}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            # Calculate diversification score (simple version)
            asset_counts = sum(1 for asset_value in [
                st.session_state.user_data['assets'].get('cash', 0),
                st.session_state.user_data['assets'].get('equity', 0),
                st.session_state.user_data['assets'].get('epf_ppf', 0),
                st.session_state.user_data['assets'].get('real_estate', 0),
                st.session_state.user_data['assets'].get('gold', 0)
            ] if asset_value > 0)
            
            diversification_score = min(asset_counts * 20, 100)  # 20 points per asset class, max 100
            
            st.markdown(f"""
            <div class="card">
                <h3>Diversification</h3>
                <p><strong>Asset Classes:</strong> {asset_counts}/5</p>
                <p><strong>Diversification Score:</strong> {diversification_score}/100</p>
                <p><strong>Status:</strong> {'Well Diversified [OK]' if diversification_score >= 60 else 'Needs Diversification [WARN]'}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Display current asset allocation
        if total_investments > 0:
            st.markdown("#### Current Asset Allocation")
            
            # Create asset allocation pie chart
            asset_data = pd.DataFrame({
                'Category': ['Cash', 'Equity', 'EPF/PPF', 'Real Estate', 'Gold', 'Other'],
                'Amount': [
                    st.session_state.user_data['assets'].get('cash', 0),
                    st.session_state.user_data['assets'].get('equity', 0),
                    st.session_state.user_data['assets'].get('epf_ppf', 0),
                    st.session_state.user_data['assets'].get('real_estate', 0),
                    st.session_state.user_data['assets'].get('gold', 0),
                    st.session_state.user_data['assets'].get('other_assets', 0)
                ]
            })
            asset_data = asset_data[asset_data['Amount'] > 0]  # Filter out zero values
            
            if not asset_data.empty:
                fig = px.pie(asset_data, values='Amount', names='Category', title='Current Asset Allocation')
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True, key="overview_asset_allocation")

        else:
            st.info("No investment data available. Please update your asset information in the Profile Setup page.")
        
        # Investment recommendations summary
        st.markdown("#### Investment Recommendations Summary")
        
        if st.session_state.investment_plan:
            # Check if we already have a summary
            if 'investment_summary' not in st.session_state or st.button("Refresh Summary", key="refresh_inv_summary"):
                with st.spinner("Extracting key recommendations..."):
                    # Create a prompt for the OpenAI model
                    summary_prompt = f"""
                    The following is an investment plan:
                    
                    {st.session_state.investment_plan}
                    
                    Extract the top 3 most important investment recommendations from this plan. 
                    Format each recommendation as a concise, actionable bullet point.
                    Focus on specific investment vehicles, asset allocation advice, or tax-saving strategies.
                    """
                    
                    # Use the investment_advisor agent to generate the summary
                    summary_response = investment_advisor.run(summary_prompt, stream=False)
                    
                    # Store the summary in session state
                    st.session_state.investment_summary = summary_response.content
            
            # Display the summary
            if st.session_state.investment_summary:
                # Split the summary into bullet points (still need minimal regex to clean up formatting)
                import re
                bullet_points = [point.strip() for point in re.split(r'\n+', st.session_state.investment_summary) if point.strip()]
                
                # Display each bullet point in a highlight card
                for point in bullet_points:
                    # Remove leading bullet characters if present
                    clean_point = re.sub(r'^[\-\*->>>>--]+\s*', '', point)
                    
                    st.markdown(f"""
                    <div class="highlight">
                        <p>- {clean_point}</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Add button to view all recommendations
            if st.button("View Full Investment Plan", key="view_all_inv_recs"):
                tabs[1].selectbox = True  # Switch to recommendations tab
        else:
            st.info("Generate investment recommendations to see a summary here.")
        
        # Quick actions
        st.markdown("#### Quick Actions")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Generate Investment Recommendations", key="gen_inv_rec_overview"):
                tabs[1].selectbox = True  # Switch to recommendations tab
                st.session_state.investment_plan = None  # Reset to trigger regeneration
        

    with tabs[1]:
        # Generate investment recommendations if not already generated
        if not st.session_state.investment_plan or st.button("Generate Investment Recommendations"):
            with st.spinner("Analyzing your financial situation and generating investment recommendations..."):
                # Prepare user investment profile
                investment_profile = f"""
                Name: {st.session_state.user_data['personal'].get('name')}
                Age: {st.session_state.user_data['personal'].get('age')}
                Risk Tolerance: {st.session_state.user_data['personal'].get('risk_tolerance')}
                
                Current Investments:
                - Cash: INR {st.session_state.user_data['assets'].get('cash', 0):,.2f}
                - Equity Investments: INR {st.session_state.user_data['assets'].get('equity', 0):,.2f}
                - EPF/PPF: INR {st.session_state.user_data['assets'].get('epf_ppf', 0):,.2f}
                - Gold: INR {st.session_state.user_data['assets'].get('gold', 0):,.2f}
                
                Monthly Income: INR {sum([
                    st.session_state.user_data['income'].get('primary_income', 0),
                    st.session_state.user_data['income'].get('secondary_income', 0),
                    st.session_state.user_data['income'].get('other_income', 0)
                ]):,.2f}
                
                Monthly Expenses: INR {sum(st.session_state.user_data['expenses'].values()):,.2f}
                
                Financial Goals:
                """
                
                # Add goals to investment profile
                for goal, value in st.session_state.user_data['goals'].items():
                    if isinstance(value, bool) and value:
                        investment_profile += f"- {goal.replace('_', ' ').title()}\n"
                    elif goal == 'retirement' and value:
                        investment_profile += f"- Retirement at age {st.session_state.user_data['goals'].get('retirement_age')} with monthly income of INR {st.session_state.user_data['goals'].get('retirement_income'):,.2f}\n"
                
                # Generate investment recommendations
                investment_prompt = f"""
                User investment profile: {investment_profile}
                
                Provide detailed investment recommendations for this Indian investor. Include specific Indian investment vehicles like:
                1. Equity mutual funds (large cap, mid cap, small cap, multi cap)
                2. Debt instruments (PPF, FD, debt funds)
                3. Tax-saving investments (ELSS, NPS, PPF)
                4. Insurance products (Term insurance, health insurance)
                
                For mutual funds, suggest specific fund categories based on their risk profile. Explain the tax implications of each investment type under Indian tax laws.
                """
                st.session_state._last_inv_prompt = investment_prompt
                investment_response = investment_advisor.run(investment_prompt, stream=False)
                st.session_state.investment_plan = investment_response.content
                
                # Clear any existing summary when generating a new plan
                if 'investment_summary' in st.session_state:
                    del st.session_state.investment_summary
        
        # Display investment recommendations
        if st.session_state.investment_plan:
            st.markdown(st.session_state.investment_plan)
            
            # Add download button for the investment plan
            st.download_button(
                label="Download Investment Plan",
                data=st.session_state.investment_plan,
                file_name=f"investment_plan_{datetime.now().strftime('%Y%m%d')}.md",
                mime="text/markdown"
            )
                # --- Token counting ---
            encoder = tiktoken.encoding_for_model("gpt-4o")
            ptokens = len(encoder.encode(st.session_state._last_inv_prompt))
            rtokens = len(encoder.encode(st.session_state.investment_plan))
            total = ptokens + rtokens

            st.info(f"[Note] Token Usage - Prompt: {ptokens}, Response: {rtokens}, **Total: {total}**")
        else:
            st.info("Click **Generate Investment Recommendations** above to get started.")
    with tabs[2]:
        st.markdown('<div class="sub-header">Portfolio Analysis</div>', unsafe_allow_html=True)
        
        # Current asset allocation
        total_investments = (
            st.session_state.user_data['assets'].get('cash', 0) +
            st.session_state.user_data['assets'].get('equity', 0) +
            st.session_state.user_data['assets'].get('epf_ppf', 0) +
            st.session_state.user_data['assets'].get('real_estate', 0) +
            st.session_state.user_data['assets'].get('gold', 0) +
            st.session_state.user_data['assets'].get('other_assets', 0)
        )
        
        if total_investments > 0:
            # Create asset allocation pie chart
            asset_data = pd.DataFrame({
                'Category': ['Cash', 'Equity', 'EPF/PPF', 'Real Estate', 'Gold', 'Other'],
                'Amount': [
                    st.session_state.user_data['assets'].get('cash', 0),
                    st.session_state.user_data['assets'].get('equity', 0),
                    st.session_state.user_data['assets'].get('epf_ppf', 0),
                    st.session_state.user_data['assets'].get('real_estate', 0),
                    st.session_state.user_data['assets'].get('gold', 0),
                    st.session_state.user_data['assets'].get('other_assets', 0)
                ]
            })
            asset_data = asset_data[asset_data['Amount'] > 0]  # Filter out zero values
            
            if not asset_data.empty:
                fig = px.pie(asset_data, values='Amount', names='Category', title='Current Asset Allocation')
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True, key="portfolio_asset_allocation")

            
            # Display asset allocation metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                cash_percentage = (st.session_state.user_data['assets'].get('cash', 0) / total_investments) * 100 if total_investments > 0 else 0
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{cash_percentage:.1f}%</div>
                    <div class="metric-label">Cash</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                equity_percentage = (st.session_state.user_data['assets'].get('equity', 0) / total_investments) * 100 if total_investments > 0 else 0
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{equity_percentage:.1f}%</div>
                    <div class="metric-label">Equity</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                gold_percentage = (st.session_state.user_data['assets'].get('gold', 0) / total_investments) * 100 if total_investments > 0 else 0
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{gold_percentage:.1f}%</div>
                    <div class="metric-label">Gold</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Recommended asset allocation based on risk tolerance
            st.markdown("#### Recommended Asset Allocation")
            risk_allocations = {
                "Very Conservative": {"Equity": 20, "Debt": 60, "Gold": 10, "Cash": 10},
                "Conservative": {"Equity": 30, "Debt": 50, "Gold": 10, "Cash": 10},
                "Moderate": {"Equity": 50, "Debt": 30, "Gold": 10, "Cash": 10},
                "Aggressive": {"Equity": 70, "Debt": 20, "Gold": 5, "Cash": 5},
                "Very Aggressive": {"Equity": 80, "Debt": 10, "Gold": 5, "Cash": 5}
            }
            
            user_risk = st.session_state.user_data['personal'].get('risk_tolerance', 'Moderate')
            recommended_allocation = risk_allocations.get(user_risk, risk_allocations["Moderate"])
            
            # Create recommended allocation pie chart
            recommended_data = pd.DataFrame({
                'Category': list(recommended_allocation.keys()),
                'Percentage': list(recommended_allocation.values())
            })
            
            fig = px.pie(recommended_data, values='Percentage', names='Category', title=f'Recommended Asset Allocation ({user_risk} Risk Profile)')
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True, key="recommended_asset_allocation")

        else:
            st.info("No investment data available. Please update your asset information in the Profile Setup page.")
