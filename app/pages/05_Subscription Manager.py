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
from agents import subscription_manager

apply_global_styles()



st.header("Subscription Manager")

# Check if user has completed profile
if not st.session_state.user_data['personal'].get('name'):
    st.warning("Please complete your profile setup first to use the subscription manager.")
else:
    tabs = st.tabs(["Your Subscriptions", "Add Subscription", "Subscription Analysis"])
    
    with tabs[0]:
        st.markdown('<div class="sub-header">Your Subscriptions</div>', unsafe_allow_html=True)
        
        # Initialize subscriptions list if not exists
        if 'subscriptions' not in st.session_state.user_data:
            st.session_state.user_data['subscriptions'] = []
        
        # Display subscriptions
        if not st.session_state.user_data['subscriptions']:
            st.info("You haven't added any subscriptions yet. Go to the 'Add Subscription' tab to add your subscriptions.")
        else:
            # Create a DataFrame for subscriptions
            subscriptions_df = pd.DataFrame(st.session_state.user_data['subscriptions'])
            
            # Calculate total monthly and annual cost
            total_monthly = subscriptions_df['amount'].sum()
            total_annual = total_monthly * 12
            
            # Display metrics
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">INR {total_monthly:,.2f}</div>
                    <div class="metric-label">Monthly Subscription Cost</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">INR {total_annual:,.2f}</div>
                    <div class="metric-label">Annual Subscription Cost</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Display subscriptions table
            st.markdown("#### Your Subscription List")
            
            # Add edit and delete functionality
            edited_df = st.data_editor(
                subscriptions_df,
                column_config={
                    "name": "Subscription Name",
                    "category": st.column_config.SelectboxColumn(
                        "Category",
                        options=["Entertainment", "Productivity", "Utilities", "Shopping", "News", "Music", "Gaming", "Other"]
                    ),
                    "amount": "Monthly Amount (INR )",
                    "billing_cycle": st.column_config.SelectboxColumn(
                        "Billing Cycle",
                        options=["Monthly", "Quarterly", "Annual", "Biannual"]
                    ),
                    "renewal_date": "Next Renewal Date"
                },
                hide_index=True,
                num_rows="dynamic"
            )
            
            # Update subscriptions if edited
            if not edited_df.equals(subscriptions_df):
                st.session_state.user_data['subscriptions'] = edited_df.to_dict('records')
                st.success("Subscriptions updated!")
            
            # Create subscription breakdown chart
            if not subscriptions_df.empty:
                category_data = subscriptions_df.groupby('category')['amount'].sum().reset_index()
                
                fig = px.pie(category_data, values='amount', names='category', title='Subscription Breakdown by Category')
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
    
    with tabs[1]:
        st.markdown('<div class="sub-header">Add New Subscription</div>', unsafe_allow_html=True)
        
        # Form for adding new subscription
        with st.form("add_subscription_form"):
            subscription_name = st.text_input("Subscription Name")
            subscription_category = st.selectbox("Category", ["Entertainment", "Productivity", "Utilities", "Shopping", "News", "Music", "Gaming", "Other"])
            subscription_amount = st.number_input("Monthly Amount (INR )", min_value=0.0)
            billing_cycle = st.selectbox("Billing Cycle", ["Monthly", "Quarterly", "Annual", "Biannual"])
            renewal_date = st.date_input("Next Renewal Date", datetime.now() + timedelta(days=30))
            
            submitted = st.form_submit_button("Add Subscription")
            
            if submitted and subscription_name and subscription_amount > 0:
                # Add new subscription
                new_subscription = {
                    "name": subscription_name,
                    "category": subscription_category,
                    "amount": float(subscription_amount),
                    "billing_cycle": billing_cycle,
                    "renewal_date": renewal_date.strftime("%Y-%m-%d")
                }
                
                st.session_state.user_data['subscriptions'].append(new_subscription)
                st.success(f"Added {subscription_name} subscription!")
    
    with tabs[2]:
        st.markdown('<div class="sub-header">Subscription Analysis</div>', unsafe_allow_html=True)
        
        # Generate subscription analysis if not already generated
        if not st.session_state.subscription_analysis or st.button("Analyze Subscriptions"):
            with st.spinner("Analyzing your subscriptions..."):
                # Prepare subscription data
                if not st.session_state.user_data['subscriptions']:
                    st.info("You haven't added any subscriptions yet. Go to the 'Add Subscription' tab to add your subscriptions.")
                else:
                    subscription_data = f"""
                    Name: {st.session_state.user_data['personal'].get('name')}
                    
                    Monthly Income: INR {sum([
                        st.session_state.user_data['income'].get('primary_income', 0),
                        st.session_state.user_data['income'].get('secondary_income', 0),
                        st.session_state.user_data['income'].get('other_income', 0)
                    ]):,.2f}
                    
                    Subscriptions:
                    """
                    
                    for sub in st.session_state.user_data['subscriptions']:
                        subscription_data += f"- {sub['name']} ({sub['category']}): INR {sub['amount']:,.2f} per month, billed {sub['billing_cycle'].lower()}\n"
                    
                    # Generate subscription analysis
                    subscription_prompt = f"""
                    User subscription data: {subscription_data}
                    
                    Analyze the user's subscriptions and provide recommendations for optimization. Include:
                    1. Identification of potential redundant or overlapping subscriptions
                    2. Suggestions for alternative services that offer better value in India
                    3. Recommendations for changing billing cycles to save money
                    4. Prioritized list of subscriptions to keep or cancel
                    5. Calculation of potential monthly and annual savings
                    
                    Consider Indian-specific subscription services and their pricing models.
                    """
                    
                    subscription_response = subscription_manager.run(subscription_prompt, stream=False)
                    st.session_state.subscription_analysis = subscription_response.content
        
        # Display subscription analysis
        if st.session_state.subscription_analysis:
            st.markdown(st.session_state.subscription_analysis)
            
            # Add download button for the subscription analysis
            st.download_button(
                label="Download Subscription Analysis",
                data=st.session_state.subscription_analysis,
                file_name=f"subscription_analysis_{datetime.now().strftime('%Y%m%d')}.md",
                mime="text/markdown"
            )
            
            # Add subscription optimization calculator
            st.markdown("#### Subscription Optimization Calculator")
            
            # Get current subscriptions
            current_subscriptions = pd.DataFrame(st.session_state.user_data['subscriptions'])
            current_monthly_cost = current_subscriptions['amount'].sum() if not current_subscriptions.empty else 0
            
            # Create a copy for optimization
            optimized_subscriptions = current_subscriptions.copy()
            
            # Allow user to mark subscriptions for cancellation
            if not current_subscriptions.empty:
                st.markdown("Select subscriptions to cancel or modify:")
                
                for i, sub in enumerate(current_subscriptions.iterrows()):
                    sub_data = sub[1]
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.markdown(f"**{sub_data['name']}** (INR {sub_data['amount']:,.2f}/month)")
                    
                    with col2:
                        cancel = st.checkbox("Cancel", key=f"cancel_{i}")
                        if cancel:
                            optimized_subscriptions = optimized_subscriptions[optimized_subscriptions['name'] != sub_data['name']]
                    
                    with col3:
                        if not cancel:
                            discount = st.number_input("Discount %", min_value=0, max_value=100, value=0, key=f"discount_{i}")
                            if discount > 0:
                                # Apply discount to the subscription
                                optimized_subscriptions.loc[optimized_subscriptions['name'] == sub_data['name'], 'amount'] = sub_data['amount'] * (1 - discount/100)
                
                # Calculate savings
                optimized_monthly_cost = optimized_subscriptions['amount'].sum() if not optimized_subscriptions.empty else 0
                monthly_savings = current_monthly_cost - optimized_monthly_cost
                annual_savings = monthly_savings * 12
                
                st.markdown(f"""
                <div class="highlight">
                    <h3>Potential Savings</h3>
                    <p>Current Monthly Cost: INR {current_monthly_cost:,.2f}</p>
                    <p>Optimized Monthly Cost: INR {optimized_monthly_cost:,.2f}</p>
                    <p>Monthly Savings: INR {monthly_savings:,.2f}</p>
                    <p>Annual Savings: INR {annual_savings:,.2f}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Create savings visualization
                savings_data = pd.DataFrame({
                    'Category': ['Current Cost', 'Optimized Cost', 'Savings'],
                    'Monthly': [current_monthly_cost, optimized_monthly_cost, monthly_savings],
                    'Annual': [current_monthly_cost * 12, optimized_monthly_cost * 12, annual_savings]
                })
                
                fig = px.bar(savings_data, x='Category', y='Monthly', title='Monthly Subscription Cost Optimization')
                fig.update_layout(yaxis_title='Amount (INR )')
                st.plotly_chart(fig, use_container_width=True)