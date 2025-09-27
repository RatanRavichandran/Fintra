from __future__ import annotations

import streamlit as st

from ui import apply_global_styles, load_logo

st.set_page_config(page_title='Your Finance Planner', page_icon='[Finance]', layout='wide')
apply_global_styles()

load_logo()
st.title('Welcome to Your Finance Planner')
st.write('Use the cards below to jump directly to any section.')

cards = [
    ('Profile_Setup', '[Note]', 'Profile Setup', 'Upload and manage your profile'),
    ('Financial_Planner', '[Work]', 'Financial Planner', 'Generate your personalised plan'),
    ('Investment_Manager', '[Trend]', 'Investment Manager', 'Get investment recommendations'),
    ('Debt_Manager', '[Card]', 'Debt Manager', 'Analyse and reduce your debt'),
    ('Subscription_Manager', '[Alert]', 'Subscription Manager', 'Optimise your subscriptions'),
    ('Retirement_Planner', '[Retirement]', 'Retirement Planner', 'Plan for your future'),
]

for row in [cards[:3], cards[3:]]:
    cols = st.columns(3)
    for col, (page, icon, title, desc) in zip(cols, row):
        link = f"/{page.replace(' ', '%20')}"
        card_markup = f"""
        <a class="card-link" href="{link}">
          <div class="card">
            <div class="card-icon">{icon}</div>
            <div class="card-title">{title}</div>
            <div class="card-desc">{desc}</div>
            <div class="card-arrow">-></div>
          </div>
        </a>
        """
        col.markdown(card_markup, unsafe_allow_html=True)
