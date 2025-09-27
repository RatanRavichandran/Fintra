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
from agents import debt_manager

apply_global_styles()



st.header("Debt Management")

# Check if user has completed profile
if not st.session_state.user_data['personal'].get('name'):
    st.warning("Please complete your profile setup first to receive debt management recommendations.")
else:
    tabs = st.tabs(["Overview", "Debt Details", "Debt Reduction Strategies"])
    
    with tabs[0]:
        st.markdown('<div class="sub-header">Debt Management Overview</div>', unsafe_allow_html=True)
        
        # Calculate debt metrics
        total_debt = sum([
            st.session_state.user_data['liabilities'].get('home_loan', 0),
            st.session_state.user_data['liabilities'].get('car_loan', 0),
            st.session_state.user_data['liabilities'].get('education_loan', 0),
            st.session_state.user_data['liabilities'].get('credit_card', 0),
            st.session_state.user_data['liabilities'].get('personal_loan', 0),
            st.session_state.user_data['liabilities'].get('other_debt', 0)
        ])
        
        total_assets = sum(st.session_state.user_data['assets'].values())
        debt_to_asset_ratio = total_debt / total_assets if total_assets > 0 else float('inf')
        
        monthly_income = sum([
            st.session_state.user_data['income'].get('primary_income', 0),
            st.session_state.user_data['income'].get('secondary_income', 0),
            st.session_state.user_data['income'].get('other_income', 0)
        ])
        
        # Estimate monthly debt payments (simplified)
        monthly_debt_payment = 0
        
        # Home loan EMI calculation (if applicable)
        if st.session_state.user_data['liabilities'].get('home_loan', 0) > 0:
            home_loan_amount = st.session_state.user_data['liabilities'].get('home_loan', 0)
            home_loan_rate = st.session_state.user_data['liabilities'].get('home_loan_rate', 7.5) / 100 / 12  # Monthly rate
            home_loan_term = st.session_state.user_data['liabilities'].get('home_loan_term', 20) * 12  # Months
            
            if home_loan_rate > 0:
                home_loan_emi = home_loan_amount * home_loan_rate * (1 + home_loan_rate) ** home_loan_term / ((1 + home_loan_rate) ** home_loan_term - 1)
                monthly_debt_payment += home_loan_emi
        
        # Credit card minimum payment (typically 5% of outstanding)
        if st.session_state.user_data['liabilities'].get('credit_card', 0) > 0:
            credit_card_min_payment = st.session_state.user_data['liabilities'].get('credit_card', 0) * 0.05
            monthly_debt_payment += credit_card_min_payment
        
        # Simplified estimation for other loans (assuming 3-year term for car loan, 5-year for education, 2-year for personal)
        if st.session_state.user_data['liabilities'].get('car_loan', 0) > 0:
            car_loan_emi = st.session_state.user_data['liabilities'].get('car_loan', 0) / 36  # Simplified
            monthly_debt_payment += car_loan_emi
        
        if st.session_state.user_data['liabilities'].get('education_loan', 0) > 0:
            education_loan_emi = st.session_state.user_data['liabilities'].get('education_loan', 0) / 60  # Simplified
            monthly_debt_payment += education_loan_emi
        
        if st.session_state.user_data['liabilities'].get('personal_loan', 0) > 0:
            personal_loan_emi = st.session_state.user_data['liabilities'].get('personal_loan', 0) / 24  # Simplified
            monthly_debt_payment += personal_loan_emi
        
        # Calculate debt-to-income ratio
        debt_to_income_ratio = monthly_debt_payment / monthly_income if monthly_income > 0 else float('inf')
        
        # Display debt summary cards
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="card">
                <h3>Debt Summary</h3>
                <p><strong>Total Debt:</strong> INR {total_debt:,.2f}</p>
                <p><strong>Monthly Debt Payment:</strong> INR {monthly_debt_payment:,.2f}</p>
                <p><strong>Debt-to-Income Ratio:</strong> {debt_to_income_ratio * 100:.1f}%</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Determine debt health status
            if debt_to_income_ratio < 0.36:
                debt_health = "Healthy [OK]"
                debt_health_desc = "Your debt level is manageable."
            elif debt_to_income_ratio < 0.43:
                debt_health = "Moderate [WARN]"
                debt_health_desc = "Your debt is at a moderate level."
            else:
                debt_health = "High Risk [STOP]"
                debt_health_desc = "Your debt level is high. Consider debt reduction strategies."
            
            st.markdown(f"""
            <div class="card">
                <h3>Debt Health</h3>
                <p><strong>Status:</strong> {debt_health}</p>
                <p>{debt_health_desc}</p>
                <p><strong>Debt-to-Asset Ratio:</strong> {debt_to_asset_ratio:.2f}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            # Calculate high-interest debt
            high_interest_debt = st.session_state.user_data['liabilities'].get('credit_card', 0) + st.session_state.user_data['liabilities'].get('personal_loan', 0)
            high_interest_percentage = (high_interest_debt / total_debt) * 100 if total_debt > 0 else 0
            
            st.markdown(f"""
            <div class="card">
                <h3>High-Interest Debt</h3>
                <p><strong>Amount:</strong> INR {high_interest_debt:,.2f}</p>
                <p><strong>Percentage of Total:</strong> {high_interest_percentage:.1f}%</p>
                <p><strong>Priority:</strong> {'High [STOP]' if high_interest_percentage > 30 else 'Medium [WARN]' if high_interest_percentage > 10 else 'Low [OK]'}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Display debt breakdown chart
        if total_debt > 0:
            st.markdown("#### Debt Breakdown")
            
            # Create debt breakdown chart
            debt_data = pd.DataFrame({
                'Category': ['Home Loan', 'Car Loan', 'Education Loan', 'Credit Card', 'Personal Loan', 'Other Debt'],
                'Amount': [
                    st.session_state.user_data['liabilities'].get('home_loan', 0),
                    st.session_state.user_data['liabilities'].get('car_loan', 0),
                    st.session_state.user_data['liabilities'].get('education_loan', 0),
                    st.session_state.user_data['liabilities'].get('credit_card', 0),
                    st.session_state.user_data['liabilities'].get('personal_loan', 0),
                    st.session_state.user_data['liabilities'].get('other_debt', 0)
                ]
            })
            debt_data = debt_data[debt_data['Amount'] > 0]  # Filter out zero values
            
            if not debt_data.empty:
                fig = px.pie(debt_data, values='Amount', names='Category', title='Debt Breakdown')
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
            
            # Create debt payoff timeline
            st.markdown("#### Estimated Debt Payoff Timeline")
            
            # Calculate payoff time for each debt type (simplified)
            payoff_data = []
            
            if st.session_state.user_data['liabilities'].get('home_loan', 0) > 0:
                home_loan_years = st.session_state.user_data['liabilities'].get('home_loan_term', 20)
                payoff_data.append({
                    'Debt Type': 'Home Loan',
                    'Years to Payoff': home_loan_years,
                    'Amount': st.session_state.user_data['liabilities'].get('home_loan', 0)
                })
            
            if st.session_state.user_data['liabilities'].get('car_loan', 0) > 0:
                payoff_data.append({
                    'Debt Type': 'Car Loan',
                    'Years to Payoff': 3,  # Assuming 3-year term
                    'Amount': st.session_state.user_data['liabilities'].get('car_loan', 0)
                })
            
            if st.session_state.user_data['liabilities'].get('education_loan', 0) > 0:
                payoff_data.append({
                    'Debt Type': 'Education Loan',
                    'Years to Payoff': 5,  # Assuming 5-year term
                    'Amount': st.session_state.user_data['liabilities'].get('education_loan', 0)
                })
            
            if st.session_state.user_data['liabilities'].get('personal_loan', 0) > 0:
                payoff_data.append({
                    'Debt Type': 'Personal Loan',
                    'Years to Payoff': 2,  # Assuming 2-year term
                    'Amount': st.session_state.user_data['liabilities'].get('personal_loan', 0)
                })
            
            if st.session_state.user_data['liabilities'].get('credit_card', 0) > 0:
                # Estimate credit card payoff time (assuming 10% of balance paid monthly)
                cc_balance = st.session_state.user_data['liabilities'].get('credit_card', 0)
                cc_payment = cc_balance * 0.10
                cc_rate = st.session_state.user_data['liabilities'].get('credit_card_rate', 36) / 100 / 12
                
                # Simplified calculation
                months = 0
                remaining = cc_balance
                while remaining > 1 and months < 120:  # Cap at 10 years
                    months += 1
                    interest = remaining * cc_rate
                    remaining = remaining + interest - cc_payment
                
                payoff_data.append({
                    'Debt Type': 'Credit Card',
                    'Years to Payoff': round(months / 12, 1),
                    'Amount': st.session_state.user_data['liabilities'].get('credit_card', 0)
                })
            
            if payoff_data:
                payoff_df = pd.DataFrame(payoff_data)
                
                # Create horizontal bar chart for payoff timeline
                fig = px.bar(
                    payoff_df, 
                    x='Years to Payoff', 
                    y='Debt Type', 
                    orientation='h',
                    color='Amount',
                    color_continuous_scale='Viridis',
                    title='Estimated Years to Payoff Each Debt'
                )
                fig.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.success("You have no debt! Great job maintaining a debt-free lifestyle.")
        
        # Debt reduction recommendations summary
        st.markdown("#### Debt Reduction Recommendations")
        
        if st.session_state.debt_plan:
            # Check if we already have a summary
            if 'debt_summary' not in st.session_state or st.button("Refresh Summary", key="refresh_debt_summary"):
                with st.spinner("Extracting key recommendations..."):
                    # Create a prompt for the OpenAI model
                    summary_prompt = f"""
                    The following is a debt reduction plan:
                    
                    {st.session_state.debt_plan}
                    
                    Extract the top 3 most important debt reduction recommendations from this plan.
                    Format each recommendation as a concise, actionable bullet point.
                    Focus on specific debt payoff strategies, refinancing options, or ways to reduce interest costs.
                    """
                    
                    # Use the debt_manager agent to generate the summary
                    summary_response = debt_manager.run(summary_prompt, stream=False)
                    
                    # Store the summary in session state
                    st.session_state.debt_summary = summary_response.content
            
            # Display the summary
            if st.session_state.debt_summary:
                # Split the summary into bullet points (still need minimal regex to clean up formatting)
                import re
                bullet_points = [point.strip() for point in re.split(r'\n+', st.session_state.debt_summary) if point.strip()]
                
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
            if st.button("View Full Debt Reduction Plan", key="view_all_debt_recs"):
                tabs[2].selectbox = True  # Switch to debt reduction strategies tab
        else:
            st.info("Generate a debt reduction plan to see recommendations here.")
        
        # Quick actions
        st.markdown("#### Quick Actions")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Generate Debt Reduction Plan", key="gen_debt_plan_overview"):
                tabs[2].selectbox = True  # Switch to debt reduction strategies tab
                st.session_state.debt_plan = None  # Reset to trigger regeneration
        
    
    with tabs[1]:
        st.markdown('<div class="sub-header">Your Debt Overview</div>', unsafe_allow_html=True)
        
        # Calculate total debt
        total_debt = sum([
            st.session_state.user_data['liabilities'].get('home_loan', 0),
            st.session_state.user_data['liabilities'].get('car_loan', 0),
            st.session_state.user_data['liabilities'].get('education_loan', 0),
            st.session_state.user_data['liabilities'].get('credit_card', 0),
            st.session_state.user_data['liabilities'].get('personal_loan', 0),
            st.session_state.user_data['liabilities'].get('other_debt', 0)
        ])
        
        if total_debt > 0:
            # Create debt breakdown chart
            debt_data = pd.DataFrame({
                'Category': ['Home Loan', 'Car Loan', 'Education Loan', 'Credit Card', 'Personal Loan', 'Other Debt'],
                'Amount': [
                    st.session_state.user_data['liabilities'].get('home_loan', 0),
                    st.session_state.user_data['liabilities'].get('car_loan', 0),
                    st.session_state.user_data['liabilities'].get('education_loan', 0),
                    st.session_state.user_data['liabilities'].get('credit_card', 0),
                    st.session_state.user_data['liabilities'].get('personal_loan', 0),
                    st.session_state.user_data['liabilities'].get('other_debt', 0)
                ],
                'Interest Rate': [
                    st.session_state.user_data['liabilities'].get('home_loan_rate', 7.5),
                    st.session_state.user_data['liabilities'].get('car_loan_rate', 9.0),
                    st.session_state.user_data['liabilities'].get('education_loan_rate', 8.0),
                    st.session_state.user_data['liabilities'].get('credit_card_rate', 7.0),
                    st.session_state.user_data['liabilities'].get('personal_loan_rate', 14.0),
                    st.session_state.user_data['liabilities'].get('other_debt_rate', 10.0)
                ]
            })
            debt_data = debt_data[debt_data['Amount'] > 0]  # Filter out zero values
            
            # Calculate interest paid per month for each debt
            debt_data['Monthly Interest'] = debt_data['Amount'] * debt_data['Interest Rate'] / 100 / 12
            
            # Sort by interest rate (highest first)
            debt_data = debt_data.sort_values('Interest Rate', ascending=False)
            
            # Display debt table
            st.markdown("#### Your Debts (Sorted by Interest Rate)")
            
            # Format the table for display
            display_data = debt_data.copy()
            display_data['Amount'] = display_data['Amount'].apply(lambda x: f"INR {x:,.2f}")
            display_data['Interest Rate'] = display_data['Interest Rate'].apply(lambda x: f"{x:.2f}%")
            display_data['Monthly Interest'] = display_data['Monthly Interest'].apply(lambda x: f"INR {x:,.2f}")
            
            st.table(display_data)
            
            # Display debt breakdown chart
            st.markdown("#### Debt Breakdown")
            
            fig = px.pie(debt_data, values='Amount', names='Category', title='Debt Breakdown by Amount')
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
            
            # Display interest cost breakdown
            st.markdown("#### Monthly Interest Cost Breakdown")
            
            fig = px.pie(debt_data, values='Monthly Interest', names='Category', title='Monthly Interest Cost Breakdown')
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
            
        #     # Display debt-to-income ratio
        #     monthly_income = sum([
        #         st.session_state.user_data['income'].get('primary_income', 0),
        #         st.session_state.user_data['income'].get('secondary_income', 0),
        #         st.session_state.user_data['income'].get('other_income', 0)
        #     ])
            
        #     # Estimate monthly debt payments (simplified)
        #     monthly_debt_payment = debt_data['Monthly Interest'].sum() * 2  # Rough estimate: interest + principal
        #     debt_to_income_ratio = monthly_debt_payment / monthly_income if monthly_income > 0 else float('inf')
            
        #     st.markdown("#### Debt-to-Income Ratio")
            
        #     # Create a gauge chart for debt-to-income ratio
        #     fig = go.Figure(go.Indicator(
        #         mode = "gauge+number",
        #         value = debt_to_income_ratio * 100,
        #         title = {'text': "Debt-to-Income Ratio (%)"},
        #         gauge = {
        #             'axis': {'range': [None, 100]},
        #             'bar': {'color': "darkblue"},
        #             'steps': [
        #                 {'range': [0, 36], 'color': "green"},
        #                 {'range': [36, 43], 'color': "yellow"},
        #                 {'range': [43, 100], 'color': "red"}
        #             ],
        #             'threshold': {
        #                 'line': {'color': "red", 'width': 4},
        #                 'thickness': 0.75,
        #                 'value': debt_to_income_ratio * 100
        #             }
        #         }
        #     ))
            
        #     st.plotly_chart(fig, use_container_width=True)
            
        #     # Add interpretation
        #     if debt_to_income_ratio < 0.36:
        #         st.success("Your debt-to-income ratio is healthy (below 36%). This is generally considered good by lenders.")
        #     elif debt_to_income_ratio < 0.43:
        #         st.warning("Your debt-to-income ratio is moderate (between 36% and 43%). This is typically the maximum allowed for many mortgage loans.")
        #     else:
        #         st.error("Your debt-to-income ratio is high (above 43%). This may make it difficult to get new loans and indicates potential financial stress.")
        # else:
        #     st.success("You have no debt! Great job maintaining a debt-free lifestyle.")
    
    with tabs[2]:
        st.markdown('<div class="sub-header">Debt Reduction Strategies</div>', unsafe_allow_html=True)
        
        # Generate debt reduction plan if not already generated
        if not st.session_state.debt_plan or st.button("Generate Debt Reduction Plan"):
            with st.spinner("Analyzing your debt situation and generating recommendations..."):
                # Prepare user debt profile
                debt_profile = f"""
                Name: {st.session_state.user_data['personal'].get('name')}
                Age: {st.session_state.user_data['personal'].get('age')}
                
                Current Debts:
                - Home Loan: INR {st.session_state.user_data['liabilities'].get('home_loan', 0):,.2f} at {st.session_state.user_data['liabilities'].get('home_loan_rate', 7.5)}% interest
                - Car Loan: INR {st.session_state.user_data['liabilities'].get('car_loan', 0):,.2f} at {st.session_state.user_data['liabilities'].get('car_loan_rate', 9.0)}% interest
                - Education Loan: INR {st.session_state.user_data['liabilities'].get('education_loan', 0):,.2f} at {st.session_state.user_data['liabilities'].get('education_loan_rate', 8.0)}% interest
                - Credit Card: INR {st.session_state.user_data['liabilities'].get('credit_card', 0):,.2f} at {st.session_state.user_data['liabilities'].get('credit_card_rate', 7.0)}% interest
                - Personal Loan: INR {st.session_state.user_data['liabilities'].get('personal_loan', 0):,.2f} at {st.session_state.user_data['liabilities'].get('personal_loan_rate', 14.0)}% interest
                - Other Debt: INR {st.session_state.user_data['liabilities'].get('other_debt', 0):,.2f} at {st.session_state.user_data['liabilities'].get('other_debt_rate', 10.0)}% interest
                
                Monthly Income: INR {sum([
                    st.session_state.user_data['income'].get('primary_income', 0),
                    st.session_state.user_data['income'].get('secondary_income', 0),
                    st.session_state.user_data['income'].get('other_income', 0)
                ]):,.2f}
                
                Monthly Expenses: INR {sum(st.session_state.user_data['expenses'].values()):,.2f}
                """
                
                # Generate debt reduction plan
                debt_prompt = f"""
                User debt profile: {debt_profile}
                
                Provide a detailed debt reduction plan for this Indian user. Include:
                1. Prioritization of which debts to pay off first (e.g., avalanche method, snowball method)
                2. Specific strategies for high-interest debt like credit cards
                3. Refinancing options available in India
                4. Balance transfer opportunities for credit cards
                5. Tax benefits related to certain loans in India (e.g., home loan interest deduction under Section 24)
                6. A month-by-month plan for debt reduction
                
                Make the recommendations specific to the Indian financial context.
                """
                
                debt_response = debt_manager.run(debt_prompt, stream=False)
                st.session_state.debt_plan = debt_response.content
                
                # Clear any existing summary when generating a new plan
                if 'debt_summary' in st.session_state:
                    del st.session_state.debt_summary
        
        # Display debt reduction plan
        if st.session_state.debt_plan:
            st.markdown(st.session_state.debt_plan)
            
            # Add download button for the debt plan
            st.download_button(
                label="Download Debt Reduction Plan",
                data=st.session_state.debt_plan,
                file_name=f"debt_reduction_plan_{datetime.now().strftime('%Y%m%d')}.md",
                mime="text/markdown"
            )
        else:
            st.info("Click the 'Generate Debt Reduction Plan' button to get personalized recommendations.")
    
