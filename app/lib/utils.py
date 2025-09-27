from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd
import streamlit as st

try:  # pragma: no cover - optional dependency when running tests
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore

from config import get_settings

settings = get_settings()


@dataclass
class SimilarProfile:
    name: str
    summary: str
    income: str
    investments: str
    notes: str


def _ensure_dataframe(path: str) -> pd.DataFrame:
    try:
        return pd.read_excel(path)
    except Exception as exc:
        st.warning(f"Could not read {path}: {exc}. Loading sample data instead.")
        return create_sample_funds_data()


def load_funds_data(file_path: str) -> pd.DataFrame:
    """Load and normalise fund data from an Excel source."""
    df = _ensure_dataframe(file_path)
    df.columns = [col.strip() for col in df.columns]
    return df


def create_sample_funds_data() -> pd.DataFrame:
    """Return an in-memory fallback dataset when the Excel file is missing."""
    return pd.DataFrame({
        'Scheme Name': [f'Sample Fund {i}' for i in range(1, 11)],
        'Benchmark': ['Nifty 50', 'Sensex', 'Nifty Next 50', 'Nifty 50', 'Sensex'] * 2,
        'Scheme Riskometer': ['Low', 'Moderately Low', 'Moderate', 'Moderately High', 'High'] * 2,
        'Benchmark Riskometer': ['Low', 'Moderate', 'Moderately High', 'High', 'High'] * 2,
        'NAV Date': ['2023-12-31'] * 10,
        'NAV Regular': [25.75, 35.42, 45.67, 28.93, 22.45, 150.78, 32.56, 28.90, 42.67, 38.92],
        'NAV Direct': [27.82, 38.75, 48.92, 31.45, 24.67, 155.43, 33.78, 30.12, 45.89, 41.23],
        'Return 1 Year (%) Regular': [5.2, 8.7, 12.5, 15.8, 18.2, 10.5, 3.8, 4.5, 9.8, 14.2],
        'Return 1 Year (%) Direct': [6.1, 9.8, 13.7, 17.2, 19.5, 11.2, 4.2, 5.0, 10.9, 15.5],
        'Return 1 Year (%) Benchmark': [4.8, 8.2, 11.9, 14.5, 16.8, 10.5, 3.5, 4.2, 9.2, 13.8],
        'Return 3 Year (%) Regular': [6.8, 10.2, 14.5, 18.2, 20.5, 12.8, 4.5, 5.2, 11.5, 16.8],
        'Return 3 Year (%) Direct': [7.9, 11.5, 15.8, 19.5, 22.0, 13.5, 5.0, 5.8, 12.8, 18.2],
        'Return 3 Year (%) Benchmark': [6.2, 9.5, 13.8, 17.2, 19.2, 12.8, 4.2, 4.8, 10.8, 15.5],
        'Return 5 Year (%) Regular': [7.5, 11.2, 15.8, 19.5, 22.8, 13.5, 5.2, 6.0, 12.5, 17.8],
        'Return 5 Year (%) Direct': [8.7, 12.5, 17.2, 21.0, 24.5, 14.2, 5.8, 6.5, 13.8, 19.2],
        'Return 5 Year (%) Benchmark': [7.0, 10.5, 15.0, 18.5, 21.5, 13.5, 4.8, 5.5, 11.8, 16.5],
        'Return 10 Year (%) Regular': [8.2, 12.0, 16.5, 20.5, 24.0, 14.2, 6.0, 6.8, 13.2, 18.5],
        'Return 10 Year (%) Direct': [9.5, 13.5, 18.0, 22.0, 25.8, 15.0, 6.5, 7.2, 14.5, 20.0],
        'Return 10 Year (%) Benchmark': [7.8, 11.2, 15.8, 19.5, 22.8, 14.2, 5.5, 6.2, 12.5, 17.5],
        'Return Since Launch Regular': [8.5, 12.5, 17.0, 21.0, 24.5, 14.5, 6.2, 7.0, 13.5, 19.0],
        'Return Since Launch Direct': [9.8, 14.0, 18.5, 22.5, 26.2, 15.2, 6.8, 7.5, 14.8, 20.5],
        'Return Since Launch Benchmark': [8.0, 11.8, 16.2, 20.0, 23.2, 14.5, 5.8, 6.5, 12.8, 18.0],
        'Daily AUM (Cr.)': [5250, 8750, 12500, 4500, 2800, 15000, 9500, 7200, 6500, 3800],
    })


def map_risk_tolerance_to_riskometer(risk_tolerance: int) -> str:
    if risk_tolerance <= 2:
        return 'Low'
    if risk_tolerance <= 4:
        return 'Moderately Low'
    if risk_tolerance <= 6:
        return 'Moderate'
    if risk_tolerance <= 8:
        return 'Moderately High'
    return 'High'


def get_investment_horizon_category(years_to_retirement: int) -> str:
    if years_to_retirement <= 5:
        return 'Short-term'
    if years_to_retirement <= 15:
        return 'Medium-term'
    return 'Long-term'


def recommend_funds(
    funds_df: pd.DataFrame,
    risk_tolerance: int,
    investment_horizon: str,
    target_amount: float,
    current_savings: float,
) -> pd.DataFrame:
    risk_category = map_risk_tolerance_to_riskometer(risk_tolerance)
    risk_col = funds_df.get('Scheme Riskometer')
    filtered_funds = funds_df

    if isinstance(risk_col, pd.Series):
        pattern_map = {
            'Low': 'Low',
            'Moderately Low': 'Moderately Low|Low to Moderate',
            'Moderate': 'Moderate',
            'Moderately High': 'Moderately High|Moderate to High',
            'High': 'High',
        }
        pattern = pattern_map.get(risk_category, 'Moderate')
        filtered_funds = funds_df[risk_col.str.contains(pattern, case=False, na=False)]

    if filtered_funds.empty:
        filtered_funds = funds_df.head(10)

    return filtered_funds.head(10)


def load_user_profiles(path: str) -> pd.DataFrame:
    try:
        return pd.read_json(path, lines=False)
    except Exception as exc:
        st.warning(f'Could not read {path}: {exc}. Loading sample profiles.')
        return create_sample_user_profiles()


def create_sample_user_profiles() -> pd.DataFrame:
    data = [
        {
            'name': 'Asha',
            'age': 35,
            'income': 1200000,
            'summary': 'Mid career professional focused on balancing mortgage payments with equity investments.',
            'investments': 'Mix of index funds and national pension system contributions.',
            'notes': 'Looks for steady long term growth and tax efficiency.',
        },
        {
            'name': 'Rahul',
            'age': 29,
            'income': 850000,
            'summary': 'Young professional ramping up investments with a higher risk appetite.',
            'investments': 'SIPs across small cap and flexi cap funds.',
            'notes': 'Open to tactical changes as income increases.',
        },
    ]
    return pd.DataFrame(data)


def get_similar_profile(profiles_df: pd.DataFrame, target_age: int) -> Optional[SimilarProfile]:
    if profiles_df.empty:
        return None

    profiles_df['age_diff'] = np.abs(profiles_df['age'] - target_age)
    row = profiles_df.sort_values('age_diff').iloc[0]
    return SimilarProfile(
        name=row.get('name', 'Peer'),
        summary=row.get('summary', ''),
        income=str(row.get('income', 'N/A')),
        investments=row.get('investments', ''),
        notes=row.get('notes', ''),
    )


@lru_cache(maxsize=1)
def _get_openai_client() -> Optional[OpenAI]:  # pragma: no cover
    if OpenAI is None or not settings.are_llm_keys_configured:
        return None
    return OpenAI(api_key=settings.openai_api_key)


def get_openai_recommendation(
    user_data: Dict[str, Any],
    simulation_results: Dict[str, Any],
    investment_horizon: str,
    recommended_funds: Optional[pd.DataFrame] = None,
) -> Dict[str, str]:
    client = _get_openai_client()
    stats = simulation_results.get('stats', {})

    if client is None:
        st.info('Set OPENAI_API_KEY to receive AI generated retirement guidance.')
        return {
            'summary': 'Configure the OpenAI API key to enable personalised recommendations.',
            'strategy': '- Increase monthly savings if the projected corpus is below your target.\n- Diversify between equity and debt instruments aligned with your risk profile.\n- Review and rebalance once a year.',
            'next_steps': '- Update the settings with your API key.\n- Re run the simulation to generate insights.\n- Consult a certified advisor for tailored planning.',
        }

    personal = user_data.get('personal', {})
    age = personal.get('age') or user_data.get('current_age')
    retirement_age = user_data.get('retirement_age') or personal.get('retirement_age')
    years_to_retirement = retirement_age - age if age and retirement_age else 'unknown'
    current_savings = user_data.get('current_savings', 0)
    monthly_contribution = user_data.get('monthly_contribution', 0)
    target_amount = user_data.get('target_retirement_amount', 0)
    risk_tolerance = personal.get('risk_tolerance') or user_data.get('risk_tolerance', 'N/A')

    prompt = f"""
Investor profile:
- Age: {age}
- Planned retirement age: {retirement_age} ({years_to_retirement} years from now)
- Current retirement corpus: INR {current_savings:,}
- Monthly contribution: INR {monthly_contribution:,}
- Target corpus: INR {target_amount:,}
- Risk tolerance (1 conservative, 10 aggressive): {risk_tolerance}
- Investment horizon assessment: {investment_horizon}

Simulation summary:
- Median projected corpus: INR {stats.get('median_final_value', 0):,.0f}
- Mean projected corpus: INR {stats.get('mean_final_value', 0):,.0f}
- 10th percentile: INR {stats.get('percentile_10', 0):,.0f}
- 90th percentile: INR {stats.get('percentile_90', 0):,.0f}
- Probability of reaching target: {stats.get('success_rate', 'N/A')}%

Provide:
1. summary (two sentences on the retirement outlook)
2. strategy (three bullet style lines separated by newlines with actionable guidance)
3. next_steps (three bullet style lines separated by newlines focusing on immediate actions)

Respond as JSON with keys summary, strategy, next_steps.
"""

    if recommended_funds is not None and not recommended_funds.empty:
        prompt += '\nReference funds to consider:\n'
        for _, fund in recommended_funds.head(5).iterrows():
            name = fund.get('Scheme Name', 'Fund')
            risk = fund.get('Scheme Riskometer', 'N/A')
            prompt += f"- {name} (risk: {risk})\n"

    try:
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {'role': 'system', 'content': 'You are a retirement planning advisor for Indian households.'},
                {'role': 'user', 'content': prompt},
            ],
            response_format={'type': 'json_object'},
            temperature=0.4,
        )
        return json.loads(response.choices[0].message.content)
    except Exception as exc:  # pragma: no cover - depends on remote API
        st.error(f'Could not fetch AI recommendations: {exc}')
        return {
            'summary': 'We could not generate advice due to an API error.',
            'strategy': '- Re run the simulation later when the service is available.\n- Focus on aligning savings with the projected gap.\n- Consider consulting a financial planner for detailed projections.',
            'next_steps': '- Double check your API credentials.\n- Try again after some time.\n- Maintain an emergency fund covering at least six months of expenses.',
        }
