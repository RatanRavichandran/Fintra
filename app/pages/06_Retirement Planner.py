import streamlit as st
from ui import apply_global_styles
from datetime import datetime, timedelta
import pathlib

from config import get_path
from lib.utils import (
    load_funds_data,
    map_risk_tolerance_to_riskometer,
    get_investment_horizon_category,
    recommend_funds,
)
from lib.simulation import (
    run_monte_carlo_simulation,
    create_simulation_plot,
    generate_simulation_interpretation,
)


apply_global_styles()


# --- Load user profile from file ---
def load_user_profile(profile_path: str | None = None) -> dict[str, int]:
    sample_path = get_path('data', 'sample_profiles', 'rahul_updated.txt')
    target_path = sample_path if profile_path is None else pathlib.Path(profile_path)
    text = target_path.read_text(encoding='utf-8')

    data = {
        'age': int(text.split('Age:')[1].split('\n')[0].strip()),
        'risk_tolerance': int(text.split('Risk Tolerance:')[1].split('\n')[0].strip()),
        'retirement_age': int(text.split('Target Retirement Age:')[1].split('\n')[0].strip()),
        'monthly_contribution': int(text.split('Investment for Retirement per month:')[1].split('\n')[0].strip()),
        'current_savings': int(text.split('Cash Savings (INR ):')[1].split('\n')[0].strip()),
        'target_monthly_income': int(text.split('Target Retirement Monthly Income:')[1].split('\n')[0].strip()),
    }
    data['annual_contribution'] = data['monthly_contribution'] * 12
    data['years_to_retirement'] = data['retirement_age'] - data['age']
    data['target_retirement_amount'] = data['target_monthly_income'] * 12 * 25
    return data


    # Parse basic values manually from known text format
    data = {
        "age": int(text.split("Age:")[1].split("\n")[0].strip()),
        "risk_tolerance": int(text.split("Risk Tolerance:")[1].split("\n")[0].strip()),
        "retirement_age": int(text.split("Target Retirement Age:")[1].split("\n")[0].strip()),
        "monthly_contribution": int(text.split("Investment for Retirement per month:")[1].split("\n")[0].strip()),
        "current_savings": int(text.split("Cash Savings (INR ):")[1].split("\n")[0].strip()),
        "target_monthly_income": int(text.split("Target Retirement Monthly Income:")[1].split("\n")[0].strip())
    }
    print("Parsed user data:", data)
    data["annual_contribution"] = data["monthly_contribution"] * 12
    data["years_to_retirement"] = data["retirement_age"] - data["age"]
    data["target_retirement_amount"] = data["target_monthly_income"] * 12 * 25  # corpus for 25 years post-retirement
    return data

user_data = load_user_profile()

# --- Monte Carlo Simulation ---
st.header("Monte Carlo Simulation")
num_simulations = st.slider("Number of Simulations", min_value=100, max_value=5000, value=1000, step=100)
expected_return = 4 + (user_data['risk_tolerance'] - 1) * 0.8
volatility = 5 + (user_data['risk_tolerance'] - 1) * 1.5

with st.spinner("Running simulation with growing contributions..."):
    periods = user_data['years_to_retirement'] * 12
    monthly_contribution_series = []
    base_monthly = user_data['monthly_contribution']
    for year in range(user_data['years_to_retirement']):
        monthly_amount = base_monthly * ((1.10) ** year)
        monthly_contribution_series.extend([monthly_amount] * 12)
    sim_results = run_monte_carlo_simulation(
    initial_investment=user_data['current_savings'],
    monthly_contributions=monthly_contribution_series,
    expected_annual_return=expected_return,
    volatility=volatility,
    num_simulations=num_simulations,
    target_amount=user_data['target_retirement_amount']
)



left_col, right_col = st.columns(2)
with left_col:
    fig = create_simulation_plot(sim_results['simulation_df'], user_data['target_retirement_amount'])
    st.plotly_chart(fig, use_container_width=True,key="simulation_plot")

with right_col:
    stats = sim_results['stats']
    st.metric("Median Final Value", f"INR {stats['median_final_value']:,.2f}")
    st.metric("Mean Final Value", f"INR {stats['mean_final_value']:,.2f}")
    st.metric("10th Percentile (Pessimistic)", f"INR {stats['percentile_10']:,.2f}")
    st.metric("90th Percentile (Optimistic)", f"INR {stats['percentile_90']:,.2f}")
    prob_target = (sim_results['simulation_df'].iloc[-1] >= user_data['target_retirement_amount']).mean() * 100
    st.metric("Probability of Reaching Target", f"{prob_target:.1f}%")
    st.metric("Success Rate", f"{stats['success_rate']:.1f}%")

# --- LLM Interpretation ---
st.subheader("Simulation Interpretation")
if 'simulation_interpretation' not in st.session_state or st.session_state.simulation_interpretation is None:
    with st.spinner("Generating simulation interpretation..."):
        interpretation = generate_simulation_interpretation(user_data, sim_results)
        if interpretation:
            st.session_state.simulation_interpretation = interpretation
else:
    interpretation = st.session_state.simulation_interpretation

if interpretation:
    st.write("### What These Results Mean For You")
    st.write(interpretation["interpretation"])

    with st.expander("### Key Statistics Explained", expanded=False):
        st.markdown("  \n".join([f"- {item}" for item in interpretation["statistics_explanation"]]), unsafe_allow_html=True)

    with st.expander("### Initial Recommendations"):
        st.markdown("  \n".join([f"- {item}" for item in interpretation["initial_recommendations"]]), unsafe_allow_html=True)
else:
    st.write("### What These Results Mean For You")
    gap = stats['median_final_value'] - user_data['target_retirement_amount']
    if prob_target >= 75:
        st.write(f"Based on the simulation, you have a strong probability ({prob_target:.1f}%) of reaching your retirement goal. Your median projected retirement savings is INR {stats['median_final_value']:,.2f}, which is INR {abs(gap):,.2f} {'above' if gap >= 0 else 'below'} your target amount of INR {user_data['target_retirement_amount']:,}.")
    elif prob_target >= 50:
        st.write(f"Based on the simulation, you have a moderate probability ({prob_target:.1f}%) of reaching your retirement goal. Your median projected retirement savings is INR {stats['median_final_value']:,.2f}, which is INR {abs(gap):,.2f} {'above' if gap >= 0 else 'below'} your target amount of INR {user_data['target_retirement_amount']:,}.")
    else:
        st.write(f"Based on the simulation, you have a low probability ({prob_target:.1f}%) of reaching your retirement goal. Your median projected retirement savings is INR {stats['median_final_value']:,.2f}, which is INR {abs(gap):,.2f} {'above' if gap >= 0 else 'below'} your target amount of INR {user_data['target_retirement_amount']:,}.")

    st.write("### Key Statistics Explained")
    st.write("""
    - **Median Final Value**: The middle value of all simulation outcomes, representing a reasonable expectation.
    - **Mean Final Value**: The average of all simulation outcomes.
    - **10th Percentile**: A pessimistic scenario - 90% of simulations performed better than this.
    - 90th Percentile: An optimistic scenario - only 10% of simulations performed better than this.
    - Probability of Reaching Target: The percentage of simulations that reached your target retirement amount.
    - Success Rate: The percentage of simulations that met a minimum threshold for retirement adequacy.
    """)

# --- Fund Recommendations ---
st.subheader("Top Funds for YOU")

funds_df = load_funds_data("data/Funds_data.xlsx")
investment_horizon = get_investment_horizon_category(user_data['years_to_retirement'])
recommended_funds = recommend_funds(
    funds_df,
    user_data['risk_tolerance'],
    investment_horizon,
    user_data['target_retirement_amount'],
    user_data['current_savings']
)

if recommended_funds.empty:
    st.warning("No funds match your criteria. Please adjust your risk tolerance or other parameters.")
else:
    st.write(f"Based on your {investment_horizon} investment horizon and risk tolerance of {user_data['risk_tolerance']}/10, we've identified the following funds that match your profile:")

    for i, fund in recommended_funds.iterrows():
        fund_name = fund.get('Scheme Name', f"Fund {i+1}")
        risk_level = fund.get('Scheme Riskometer', 'N/A')

        if investment_horizon == "Short-term" and 'Return 1 Year (%) Direct' in fund:
            returns = fund['Return 1 Year (%) Direct']
            returns_text = f"1-Year Return: {returns:.2f}%"
        elif investment_horizon == "Medium-term" and 'Return 3 Year (%) Direct' in fund:
            returns = fund['Return 3 Year (%) Direct']
            returns_text = f"3-Year Return: {returns:.2f}%"
        else:
            returns = fund.get('Return 5 Year (%) Direct', None)
            returns_text = f"5-Year Return: {returns:.2f}%" if returns else ""

        with st.expander(f"{fund_name} - {returns_text}"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Fund Name:** {fund_name}")
                st.markdown(f"**Risk Level:** {risk_level}")
                st.markdown(f"**Benchmark:** {fund.get('Benchmark', 'N/A')}")
                st.markdown(f"**NAV:** INR {fund.get('NAV Direct', 0)}")
                st.markdown(f"**AUM:** INR {fund.get('Daily AUM (Cr.)', 0):.2f} Cr")

            with col2:
                st.markdown("**Historical Returns:**")
                returns_data = {
                    "1 Year": fund.get('Return 1 Year (%) Direct', 0),
                    "3 Year": fund.get('Return 3 Year (%) Direct', 0),
                    "5 Year": fund.get('Return 5 Year (%) Direct', 0),
                    "10 Year": fund.get('Return 10 Year (%) Direct', 0)
                }
                fig = px.bar(x=list(returns_data.keys()), y=list(returns_data.values()),
                            labels={'x': 'Time Period', 'y': 'Return (%)'},
                            title="Historical Returns",
                            color_discrete_sequence=['#005e7c'])
                st.plotly_chart(fig, use_container_width=True,key=f"returns_{i}")

    st.subheader("Fund Comparison")
    comparison_data = {}
    for i, fund in recommended_funds.iterrows():
        fund_name = fund.get('Scheme Name', f"Fund {i+1}")
        if investment_horizon == "Short-term":
            comparison_data[fund_name] = fund.get('Return 1 Year (%) Direct', 0)
        elif investment_horizon == "Medium-term":
            comparison_data[fund_name] = fund.get('Return 3 Year (%) Direct', 0)
        else:
            comparison_data[fund_name] = fund.get('Return 5 Year (%) Direct', 0)

    fig = px.bar(x=list(comparison_data.keys()), y=list(comparison_data.values()),
                labels={'x': 'Fund', 'y': f'{investment_horizon} Return (%)'},
                title=f"Fund Comparison - {investment_horizon} Returns",
                color_discrete_sequence=['#005e7c'])
    st.plotly_chart(fig, use_container_width=True,key="comparison")


# --- Roadmap ---
st.header("3. Getting Started with Your Investment Journey")

# Personalized search query based on user profile
search_terms = ["how to open demat account"]
platforms = ["Zerodha", "Groww", "Upstox", "Paytm Money"]

if user_data['age'] < 25:
    search_terms.append("for students")
if user_data['risk_tolerance'] <= 4:
    search_terms.append("safe investment platforms")

# Construct search URLs dynamically using live search results (placeholder)
search_links = [
    "https://www.zerodha.com/open-account",
    "https://upstox.com/open-demat-account/",
    "https://www.paytmmoney.com/stocks"
]

st.markdown("""
**Step 1:** Choose any of the top recommended mutual funds matching your risk profile.  
**Step 2:** Open a demat or mutual fund account. Here are some personalized links to get you started:
""")

for platform, url in zip(platforms, search_links):
    st.markdown(f"- [{platform} Guide]({url})")

st.markdown(f"""
**Step 3:** Start a SIP with month {user_data["monthly_contribution"]} and increase it annually by 10%.  
**Step 4:** Review your fund performance every 6 months and rebalance yearly.  
**Step 5:** Use tax-saving options like ELSS when possible to optimize returns.  
""")
# # --- Load user profile from file ---

#     data = {
#         "age": int(text.split("Age:")[1].split("\n")[0].strip()),
#         "risk_tolerance": int(text.split("Risk Tolerance:")[1].split("\n")[0].strip()),
#         "retirement_age": int(text.split("Target Retirement Age:")[1].split("\n")[0].strip()),
#         "monthly_contribution": int(text.split("Investment for Retirement per month:")[1].split("\n")[0].strip()),
#         "current_savings": int(text.split("Cash Savings (INR ):")[1].split("\n")[0].strip()),
#         "target_monthly_income": int(text.split("Target Retirement Monthly Income:")[1].split("\n")[0].strip())
#     }
#     print("Parsed user data:", data)
#     data["annual_contribution"] = data["monthly_contribution"] * 12
#     data["years_to_retirement"] = data["retirement_age"] - data["age"]
#     data["target_retirement_amount"] = data["target_monthly_income"] * 12 * 25  # corpus for 25 years post-retirement
#     return data

# user_data = load_user_profile()

# # --- Monte Carlo Simulation ---
# st.header("Monte Carlo Simulation")
# num_simulations = st.slider("Number of Simulations", min_value=100, max_value=5000, value=1000, step=100)
# expected_return = 4 + (user_data['risk_tolerance'] - 1) * 0.8
# volatility = 5 + (user_data['risk_tolerance'] - 1) * 1.5

# with st.spinner("Running simulation with growing contributions..."):
#     periods = user_data['years_to_retirement'] * 12
#     monthly_contribution_series = []
#     base_monthly = user_data['monthly_contribution']
#     for year in range(user_data['years_to_retirement']):
#         monthly_amount = base_monthly * ((1.10) ** year)
#         monthly_contribution_series.extend([monthly_amount] * 12)
#     sim_results = run_monte_carlo_simulation(
#     initial_investment=user_data['current_savings'],
#     monthly_contributions=monthly_contribution_series,
#     expected_annual_return=expected_return,
#     volatility=volatility,
#     num_simulations=num_simulations,
#     target_amount=user_data['target_retirement_amount']
# )



# left_col, right_col = st.columns(2)
# with left_col:
#     fig = create_simulation_plot(sim_results['simulation_df'], user_data['target_retirement_amount'])
#     st.plotly_chart(fig, use_container_width=True)

# with right_col:
#     stats = sim_results['stats']
#     st.metric("Median Final Value", f"INR {stats['median_final_value']:,.2f}")
#     st.metric("Mean Final Value", f"INR {stats['mean_final_value']:,.2f}")
#     st.metric("10th Percentile (Pessimistic)", f"INR {stats['percentile_10']:,.2f}")
#     st.metric("90th Percentile (Optimistic)", f"INR {stats['percentile_90']:,.2f}")
#     prob_target = (sim_results['simulation_df'].iloc[-1] >= user_data['target_retirement_amount']).mean() * 100
#     st.metric("Probability of Reaching Target", f"{prob_target:.1f}%")
#     st.metric("Success Rate", f"{stats['success_rate']:.1f}%")

# # --- LLM Interpretation ---
# st.subheader("Simulation Interpretation")
# if 'simulation_interpretation' not in st.session_state or st.session_state.simulation_interpretation is None:
#     with st.spinner("Generating simulation interpretation..."):
#         interpretation = generate_simulation_interpretation(user_data, sim_results)
#         if interpretation:
#             st.session_state.simulation_interpretation = interpretation
# else:
#     interpretation = st.session_state.simulation_interpretation

# if interpretation:
#     st.write("### What These Results Mean For You")
#     st.write(interpretation["interpretation"])

#     with st.expander("### Key Statistics Explained", expanded=False):
#         st.markdown("  \n".join([f"- {item}" for item in interpretation["statistics_explanation"]]), unsafe_allow_html=True)

#     with st.expander("### Initial Recommendations"):
#         st.markdown("  \n".join([f"- {item}" for item in interpretation["initial_recommendations"]]), unsafe_allow_html=True)
# else:
#     st.write("### What These Results Mean For You")
#     gap = stats['median_final_value'] - user_data['target_retirement_amount']
#     if prob_target >= 75:
#         st.write(f"Based on the simulation, you have a strong probability ({prob_target:.1f}%) of reaching your retirement goal. Your median projected retirement savings is INR {stats['median_final_value']:,.2f}, which is INR {abs(gap):,.2f} {'above' if gap >= 0 else 'below'} your target amount of INR {user_data['target_retirement_amount']:,}.")
#     elif prob_target >= 50:
#         st.write(f"Based on the simulation, you have a moderate probability ({prob_target:.1f}%) of reaching your retirement goal. Your median projected retirement savings is INR {stats['median_final_value']:,.2f}, which is INR {abs(gap):,.2f} {'above' if gap >= 0 else 'below'} your target amount of INR {user_data['target_retirement_amount']:,}.")
#     else:
#         st.write(f"Based on the simulation, you have a low probability ({prob_target:.1f}%) of reaching your retirement goal. Your median projected retirement savings is INR {stats['median_final_value']:,.2f}, which is INR {abs(gap):,.2f} {'above' if gap >= 0 else 'below'} your target amount of INR {user_data['target_retirement_amount']:,}.")

#     st.write("### Key Statistics Explained")
#     st.write("""
#     - **Median Final Value**: The middle value of all simulation outcomes, representing a reasonable expectation.
#     - **Mean Final Value**: The average of all simulation outcomes.
#     - **10th Percentile**: A pessimistic scenario - 90% of simulations performed better than this.
#     - 90th Percentile: An optimistic scenario - only 10% of simulations performed better than this.
#     - Probability of Reaching Target: The percentage of simulations that reached your target retirement amount.
#     - Success Rate: The percentage of simulations that met a minimum threshold for retirement adequacy.
#     """)

# # --- Fund Recommendations ---
# st.subheader("Top Performing Funds in the last 5 years")

# funds_df = load_funds_data("data/Funds_data.xlsx")
# investment_horizon = get_investment_horizon_category(user_data['years_to_retirement'])
# recommended_funds = recommend_funds(
#     funds_df,
#     user_data['risk_tolerance'],
#     investment_horizon,
#     user_data['target_retirement_amount'],
#     user_data['current_savings']
# )

# if recommended_funds.empty:
#     st.warning("No funds match your criteria. Please adjust your risk tolerance or other parameters.")
# else:
#     st.write(f"Based on your {investment_horizon} investment horizon and risk tolerance of {user_data['risk_tolerance']}/10, we've identified the following funds that match your profile:")

#     for i, fund in recommended_funds.iterrows():
#         fund_name = fund.get('Scheme Name', f"Fund {i+1}")
#         risk_level = fund.get('Scheme Riskometer', 'N/A')

#         if investment_horizon == "Short-term" and 'Return 1 Year (%) Direct' in fund:
#             returns = fund['Return 1 Year (%) Direct']
#             returns_text = f"1-Year Return: {returns:.2f}%"
#         elif investment_horizon == "Medium-term" and 'Return 3 Year (%) Direct' in fund:
#             returns = fund['Return 3 Year (%) Direct']
#             returns_text = f"3-Year Return: {returns:.2f}%"
#         else:
#             returns = fund.get('Return 5 Year (%) Direct', None)
#             returns_text = f"5-Year Return: {returns:.2f}%" if returns else ""

#         with st.expander(f"{fund_name} - {returns_text}"):
#             col1, col2 = st.columns(2)
#             with col1:
#                 st.markdown(f"**Fund Name:** {fund_name}")
#                 st.markdown(f"**Risk Level:** {risk_level}")
#                 st.markdown(f"**Benchmark:** {fund.get('Benchmark', 'N/A')}")
#                 st.markdown(f"**NAV:** INR {fund.get('NAV Direct', 0)}")
#                 st.markdown(f"**AUM:** INR {fund.get('Daily AUM (Cr.)', 0):.2f} Cr")

#             with col2:
#                 st.markdown("**Historical Returns:**")
#                 returns_data = {
#                     "1 Year": fund.get('Return 1 Year (%) Direct', 0),
#                     "3 Year": fund.get('Return 3 Year (%) Direct', 0),
#                     "5 Year": fund.get('Return 5 Year (%) Direct', 0),
#                     "10 Year": fund.get('Return 10 Year (%) Direct', 0)
#                 }
#                 fig = px.bar(x=list(returns_data.keys()), y=list(returns_data.values()),
#                             labels={'x': 'Time Period', 'y': 'Return (%)'},
#                             title="Historical Returns",
#                             color_discrete_sequence=['#005e7c'])
#                 st.plotly_chart(fig, use_container_width=True)

#     st.subheader("Fund Comparison")
#     comparison_data = {}
#     for i, fund in recommended_funds.iterrows():
#         fund_name = fund.get('Scheme Name', f"Fund {i+1}")
#         if investment_horizon == "Short-term":
#             comparison_data[fund_name] = fund.get('Return 1 Year (%) Direct', 0)
#         elif investment_horizon == "Medium-term":
#             comparison_data[fund_name] = fund.get('Return 3 Year (%) Direct', 0)
#         else:
#             comparison_data[fund_name] = fund.get('Return 5 Year (%) Direct', 0)

#     fig = px.bar(x=list(comparison_data.keys()), y=list(comparison_data.values()),
#                 labels={'x': 'Fund', 'y': f'{investment_horizon} Return (%)'},
#                 title=f"Fund Comparison - {investment_horizon} Returns",
#                 color_discrete_sequence=['#005e7c'])
#     st.plotly_chart(fig, use_container_width=True)


# # --- Roadmap ---
# st.header("3. Getting Started with Your Investment Journey")

# # Personalized search query based on user profile
# search_terms = ["how to open demat account"]
# platforms = ["Zerodha", "Groww", "Upstox", "Paytm Money"]

# if user_data['age'] < 25:
#     search_terms.append("for students")
# if user_data['risk_tolerance'] <= 4:
#     search_terms.append("safe investment platforms")

# # Construct search URLs dynamically using live search results (placeholder)
# search_links = [
#     "https://www.zerodha.com/open-account",
#     "https://upstox.com/open-demat-account/",
#     "https://www.paytmmoney.com/stocks"
# ]

# st.markdown("""
# **Step 1:** Choose any of the top recommended mutual funds matching your risk profile.  
# **Step 2:** Open a demat or mutual fund account. Here are some personalized links to get you started:
# """)

# for platform, url in zip(platforms, search_links):
#     st.markdown(f"- [{platform} Guide]({url})")

# st.markdown("""
# **Step 3:** Start a SIP with INR 2,000/month and increase it annually by 10%.  
# **Step 4:** Review your fund performance every 6 months and rebalance yearly.  
# **Step 5:** Use tax-saving options like ELSS when possible to optimize returns.  
# """)
