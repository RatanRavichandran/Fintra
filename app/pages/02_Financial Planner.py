import streamlit as st
from ui import apply_global_styles
from agents import financial_planner, researcher
import pandas as pd
import datetime
import plotly.express as px
from datetime import datetime
st.header("Financial Planner")
apply_global_styles()

# Check if user has completed profile
if not st.session_state.user_data['personal'].get('name'):
    st.warning("Please complete your profile setup first to receive a personalized financial plan.")
else:
    tabs = st.tabs(["Overview", "Detailed Plan"])
    
    with tabs[0]:
        st.markdown('<div class="sub-header">Financial Overview</div>', unsafe_allow_html=True)
        
        # Calculate key financial metrics
        monthly_income = sum([
            st.session_state.user_data['income'].get('primary_income', 0),
            st.session_state.user_data['income'].get('secondary_income', 0),
            st.session_state.user_data['income'].get('other_income', 0)
        ])
        monthly_expenses = sum(st.session_state.user_data['expenses'].values())
        monthly_savings = monthly_income - monthly_expenses
        savings_rate = (monthly_savings / monthly_income) * 100 if monthly_income > 0 else 0
        
        total_assets = sum(st.session_state.user_data['assets'].values())
        total_liabilities = sum([
            st.session_state.user_data['liabilities'].get('home_loan', 0),
            st.session_state.user_data['liabilities'].get('car_loan', 0),
            st.session_state.user_data['liabilities'].get('education_loan', 0),
            st.session_state.user_data['liabilities'].get('credit_card', 0),
            st.session_state.user_data['liabilities'].get('personal_loan', 0),
            st.session_state.user_data['liabilities'].get('other_debt', 0)
        ])
        net_worth = total_assets - total_liabilities
        
        # Display financial metrics in cards
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class="card">
                <h3>Monthly Cash Flow</h3>
                <p><strong>Income:</strong> INR {monthly_income:,.2f}</p>
                <p><strong>Expenses:</strong> INR {monthly_expenses:,.2f}</p>
                <p><strong>Savings:</strong> INR {monthly_savings:,.2f}</p>
                <p><strong>Savings Rate:</strong> {savings_rate:.1f}%</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="card">
                <h3>Net Worth</h3>
                <p><strong>Assets:</strong> INR {total_assets:,.2f}</p>
                <p><strong>Liabilities:</strong> INR {total_liabilities:,.2f}</p>
                <p><strong>Net Worth:</strong> INR {net_worth:,.2f}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="card">
                <h3>Financial Health</h3>
                <p><strong>Risk Tolerance:</strong> {st.session_state.user_data['personal'].get('risk_tolerance', 'Not specified')}</p>
                <p><strong>Debt-to-Asset Ratio:</strong> {total_liabilities / total_assets:.2f} {' [OK]' if total_liabilities / total_assets < 0.5 else ' [WARN]'}</p>
                <p><strong>Emergency Fund:</strong> {'Yes [OK]' if st.session_state.user_data['goals'].get('emergency_fund', False) else 'No [WARN]'}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Display income vs expenses chart
        st.markdown("#### Income vs Expenses")
        
        # Prepare data for income breakdown
        income_data = {
            'Category': ['Primary Income', 'Secondary Income', 'Other Income'],
            'Amount': [
                st.session_state.user_data['income'].get('primary_income', 0),
                st.session_state.user_data['income'].get('secondary_income', 0),
                st.session_state.user_data['income'].get('other_income', 0)
            ]
        }
        income_df = pd.DataFrame(income_data)
        income_df = income_df[income_df['Amount'] > 0]
        
        # Prepare data for expense breakdown
        expense_categories = list(st.session_state.user_data['expenses'].keys())
        expense_amounts = list(st.session_state.user_data['expenses'].values())
        expense_data = {'Category': expense_categories, 'Amount': expense_amounts}
        expense_df = pd.DataFrame(expense_data)
        expense_df = expense_df[expense_df['Amount'] > 0]
        
        # Create side-by-side charts
        col1, col2 = st.columns(2)
        
        with col1:
            if not income_df.empty:
                fig = px.pie(income_df, values='Amount', names='Category', title='Income Breakdown')
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No income data available.")
        
        with col2:
            if not expense_df.empty:
                fig = px.pie(expense_df, values='Amount', names='Category', title='Expense Breakdown')
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No expense data available.")
        
        # Display financial goals
        st.markdown("#### Your Financial Goals")
        
        goals_list = []
        for goal, value in st.session_state.user_data['goals'].items():
            if isinstance(value, bool) and value:
                if goal == 'emergency_fund':
                    goals_list.append({"Goal": "Emergency Fund", "Status": "Active", "Target": f"INR {st.session_state.user_data['goals'].get('emergency_fund_amount', 0):,.2f}"})
                elif goal == 'pay_off_debt':
                    goals_list.append({"Goal": "Pay Off Debt", "Status": "Active", "Target": f"INR {total_liabilities:,.2f}"})
                elif goal == 'vacation':
                    goals_list.append({"Goal": "Vacation", "Status": "Active", "Target": f"INR {st.session_state.user_data['goals'].get('vacation_amount', 0):,.2f}"})
                elif goal == 'down_payment':
                    goals_list.append({"Goal": "Home Down Payment", "Status": "Active", "Target": f"INR {st.session_state.user_data['goals'].get('down_payment_amount', 0):,.2f}"})
                elif goal == 'education':
                    goals_list.append({"Goal": "Education", "Status": "Active", "Target": f"INR {st.session_state.user_data['goals'].get('education_amount', 0):,.2f}"})
                elif goal == 'retirement':
                    goals_list.append({"Goal": "Retirement", "Status": "Active", "Target": f"Age {st.session_state.user_data['goals'].get('retirement_age', 60)}, INR {st.session_state.user_data['goals'].get('retirement_income', 0):,.2f}/month"})
                elif goal == 'child_marriage':
                    goals_list.append({"Goal": "Child's Marriage", "Status": "Active", "Target": f"INR {st.session_state.user_data['goals'].get('marriage_amount', 0):,.2f}"})
        
        if goals_list:
            goals_df = pd.DataFrame(goals_list)
            st.table(goals_df)
        else:
            st.info("No financial goals have been set.")
        
        # Quick actions
        st.markdown("#### Quick Actions")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Generate Financial Plan", key="gen_fin_plan_overview"):
                tabs[1].selectbox = True  # Switch to detailed plan tab
                st.session_state.financial_plan = None  # Reset to trigger regeneration
        
        with col2:
            if st.button("Download Financial Summary", key="download_summary"):
                summary_text = f"""
                # Financial Summary for {st.session_state.user_data['personal'].get('name')}
                
                ## Monthly Cash Flow
                - Income: INR {monthly_income:,.2f}
                - Expenses: INR {monthly_expenses:,.2f}
                - Savings: INR {monthly_savings:,.2f}
                - Savings Rate: {savings_rate:.1f}%
                
                ## Net Worth
                - Assets: INR {total_assets:,.2f}
                - Liabilities: INR {total_liabilities:,.2f}
                - Net Worth: INR {net_worth:,.2f}
                
                ## Financial Goals
                """
                
                for goal in goals_list:
                    summary_text += f"- {goal['Goal']}: {goal['Target']}\n"
                
                st.download_button(
                    label="Download Summary",
                    data=summary_text,
                    file_name=f"financial_summary_{datetime.now().strftime('%Y%m%d')}.md",
                    mime="text/markdown"
                )
    
    with tabs[1]:
        # Generate financial plan if not already generated
        if not st.session_state.financial_plan or st.button("Regenerate Financial Plan"):
            with st.spinner("Generating your personalized financial plan... This may take a minute."):
                # First, get research results
                user_summary = f"""Name: {st.session_state.user_data['personal'].get('name')}
                Age: {st.session_state.user_data['personal'].get('age')}
                Marital Status: {st.session_state.user_data['personal'].get('marital_status')}
                Dependents: {st.session_state.user_data['personal'].get('dependents')}
                Risk Tolerance: {st.session_state.user_data['personal'].get('risk_tolerance')}

                Monthly Income: INR {sum([
                    st.session_state.user_data['income'].get('primary_income', 0),
                    st.session_state.user_data['income'].get('secondary_income', 0),
                    st.session_state.user_data['income'].get('other_income', 0)
                ]):,.2f}

                Monthly Expenses: INR {sum(st.session_state.user_data['expenses'].values()):,.2f}

                Total Assets: INR {sum(st.session_state.user_data['assets'].values()):,.2f}
                Total Liabilities: INR {sum([
                    st.session_state.user_data['liabilities'].get('home_loan', 0),
                    st.session_state.user_data['liabilities'].get('car_loan', 0),
                    st.session_state.user_data['liabilities'].get('education_loan', 0),
                    st.session_state.user_data['liabilities'].get('credit_card', 0),
                    st.session_state.user_data['liabilities'].get('personal_loan', 0),
                    st.session_state.user_data['liabilities'].get('other_debt', 0)
                ]):,.2f}

                Financial Goals:"""
                
                # Add goals to summary
                for goal, value in st.session_state.user_data['goals'].items():
                    if isinstance(value, bool) and value:
                        user_summary += f"- {goal.replace('_', ' ').title()}\n"
                    elif goal == 'other_goal' and value:
                        user_summary += f"- Other: {value}\n"
                
                # Get research results
                research_response = researcher.run(f"User financial profile: {user_summary}", stream=False)
                
                user_name = st.session_state.user_data['personal'].get('name', 'the investor')
                plan_prompt = f"""
You are an expert financial advisor. Craft an intuitive, well-cited financial plan for {user_name} based on the profile below.

Investor Profile:
{user_summary}

Research Insights:
{research_response.content}

Your plan must include:

1. Executive Summary  
   Summarise the current financial position, goals, and risk appetite.
2. Goals Alignment  
   Map recommendations to short-term, medium-term, and long-term objectives.
3. Tailored Asset Allocation  
   - Equities: highlight suitable mutual funds with a short rationale.  
   - Debt Instruments: detail PPF, NPS, and other appropriate vehicles.  
   - ELSS and tax savers: outline options that match the profile.
4. Tax Optimization  
   Reference relevant Indian tax provisions (for example, Section 80C, 80D) with official links.
5. Top Performing Investment Vehicles  
   List high-performing funds with citations, making it clear these are informational rather than personalised recommendations.
6. Risk Management and Contingency Planning  
   Cover emergency fund strategy and insurance needs with example policies.
7. Action Plan and Timeline  
   Provide a step-by-step roadmap with milestones.

Guidelines:
- Use bullet lists and tables where appropriate.
- Cite trustworthy sources with hyperlinks.
- Base every statement on the profile or supplied research. Avoid speculation.
"""


                plan_response = financial_planner.run(plan_prompt, stream=False)
                st.session_state.financial_plan = plan_response.content
        
        # Display financial plan
        if st.session_state.financial_plan:
            st.markdown(st.session_state.financial_plan)
            
            # Add download button for the financial plan
            st.download_button(
                label="Download Financial Plan",
                data=st.session_state.financial_plan,
                file_name=f"financial_plan_{datetime.now().strftime('%Y%m%d')}.md",
                mime="text/markdown"
            )