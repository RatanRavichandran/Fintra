from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, Iterable, Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

try:  # pragma: no cover - optional dependency during tests
    from openai import OpenAI
except Exception:  # pragma: no cover - fallback if openai is unavailable
    OpenAI = None  # type: ignore

from config import get_settings

settings = get_settings()


@dataclass
class SimulationStats:
    median_final_value: float
    mean_final_value: float
    min_final_value: float
    max_final_value: float
    percentile_10: float
    percentile_90: float
    success_rate: Optional[float]

    def as_dict(self) -> Dict[str, float | None]:
        return {
            'median_final_value': self.median_final_value,
            'mean_final_value': self.mean_final_value,
            'min_final_value': self.min_final_value,
            'max_final_value': self.max_final_value,
            'percentile_10': self.percentile_10,
            'percentile_90': self.percentile_90,
            'success_rate': self.success_rate,
        }


def run_monte_carlo_simulation(
    initial_investment: float,
    monthly_contributions: Iterable[float],
    num_simulations: int = 1000,
    risk_tolerance: Optional[int] = None,
    expected_annual_return: Optional[float] = None,
    volatility: Optional[float] = None,
    target_amount: Optional[float] = None,
) -> Dict[str, Any]:
    """Run a Monte Carlo simulation for retirement planning."""

    contributions = list(monthly_contributions)
    periods = len(contributions)

    if expected_annual_return is None or volatility is None:
        risk_tolerance = risk_tolerance or 5
        expected_annual_return = 4 + (risk_tolerance - 1) * 0.8
        volatility = 5 + (risk_tolerance - 1) * 1.5

    expected_monthly_return = expected_annual_return / 12 / 100
    monthly_volatility = volatility / (12 ** 0.5) / 100

    final_values = np.zeros(num_simulations)
    all_values = np.zeros((num_simulations, periods + 1))
    all_values[:, 0] = initial_investment

    for sim in range(num_simulations):
        portfolio_value = initial_investment
        for month in range(periods):
            monthly_return = np.random.normal(expected_monthly_return, monthly_volatility)
            portfolio_value = portfolio_value * (1 + monthly_return) + contributions[month]
            all_values[sim, month + 1] = portfolio_value
        final_values[sim] = portfolio_value

    simulation_df = pd.DataFrame(all_values.T)
    simulation_df.index = range(periods + 1)

    success_rate = None
    if target_amount:
        success_rate = float(np.mean(final_values >= target_amount) * 100)

    stats = SimulationStats(
        median_final_value=float(np.median(final_values)),
        mean_final_value=float(np.mean(final_values)),
        min_final_value=float(np.min(final_values)),
        max_final_value=float(np.max(final_values)),
        percentile_10=float(np.percentile(final_values, 10)),
        percentile_90=float(np.percentile(final_values, 90)),
        success_rate=success_rate,
    )

    return {
        'simulation_df': simulation_df,
        'stats': stats.as_dict(),
    }


def create_simulation_plot(simulation_df: pd.DataFrame, target_amount: Optional[float] = None) -> go.Figure:
    """Create a Plotly figure visualising the Monte Carlo simulation results."""

    fig = go.Figure()
    median_values = simulation_df.median(axis=1)
    mean_values = simulation_df.mean(axis=1)
    percentile_10 = simulation_df.quantile(0.1, axis=1)
    percentile_90 = simulation_df.quantile(0.9, axis=1)

    fig.add_trace(go.Scatter(x=percentile_10.index, y=percentile_10.values, mode='lines', name='10th percentile', line={'color': '#fd7e14'}))
    fig.add_trace(go.Scatter(x=median_values.index, y=median_values.values, mode='lines', name='Median', line={'color': '#dc3545'}))
    fig.add_trace(go.Scatter(x=mean_values.index, y=mean_values.values, mode='lines', name='Mean', line={'color': '#0d6efd', 'dash': 'dash'}))
    fig.add_trace(go.Scatter(x=percentile_90.index, y=percentile_90.values, mode='lines', name='90th percentile', line={'color': '#198754'}))

    if target_amount is not None:
        fig.add_hline(y=target_amount, line_dash='dash', line_color='#000000', annotation_text=f'Target: INR {target_amount:,.0f}')

    fig.update_layout(
        title='Projected Retirement Corpus Over Time',
        xaxis_title='Months',
        yaxis_title='Projected value (INR)',
        template='plotly_white',
        showlegend=True,
    )
    return fig


@lru_cache(maxsize=1)
def _get_openai_client() -> Optional[OpenAI]:  # pragma: no cover - simple cache
    if OpenAI is None or not settings.are_llm_keys_configured:
        return None
    return OpenAI(api_key=settings.openai_api_key)


def _default_interpretation(stats: Dict[str, Any], target_amount: Optional[float]) -> Dict[str, str]:
    median_value = stats.get('median_final_value', 0)
    success_rate = stats.get('success_rate')
    gap = median_value - (target_amount or 0)

    summary = [
        f"Median projected retirement savings: INR {median_value:,.0f}.",
        f"Gap to target: INR {abs(gap):,.0f} {'surplus' if gap >= 0 else 'shortfall'}.",
    ]
    if success_rate is not None:
        summary.append(f"Chance of reaching target: {success_rate:.1f}%.")

    return {
        'interpretation': ' '.join(summary),
        'statistics_explanation': (
            '- Median final value: midpoint of all simulated outcomes.\n'
            '- Mean final value: average across all simulations.\n'
            '- 10th percentile: conservative scenario where 90% of outcomes are better.\n'
            '- 90th percentile: optimistic scenario represented by the top 10% outcomes.\n'
            '- Probability of reaching target: share of simulations that meet your goal.'
        ),
        'initial_recommendations': (
            '- Increase monthly contributions if the gap to target is negative.\n'
            '- Review asset allocation to align with your risk tolerance and time horizon.\n'
            '- Revisit the plan annually to adjust for market changes and life events.'
        ),
    }


def generate_simulation_interpretation(user_profile: Dict[str, Any], simulation_results: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """Use OpenAI to produce a narrative summary of the simulation results."""

    client = _get_openai_client()
    stats: Dict[str, Any] = simulation_results.get('stats', {})
    target_amount = user_profile.get('target_retirement_amount')

    if client is None:
        st.info('Set OPENAI_API_KEY to unlock automated interpretations.')
        return _default_interpretation(stats, target_amount)

    age = user_profile.get('current_age')
    retirement_age = user_profile.get('retirement_age')
    monthly_contribution = user_profile.get('monthly_contribution')
    current_savings = user_profile.get('current_savings', 0)
    risk_tolerance = user_profile.get('risk_tolerance', 'N/A')

    years_to_retirement = retirement_age - age if age and retirement_age else None
    gap = stats.get('median_final_value', 0) - (target_amount or 0)

    prompt = f"""
You are a retirement planning specialist. Interpret the Monte Carlo simulation for this investor and return JSON.

Investor details:
- Current age: {age}
- Planned retirement age: {retirement_age} ({years_to_retirement} years from now)
- Current retirement savings: INR {current_savings:,}
- Monthly contribution: INR {monthly_contribution:,}
- Target retirement amount: INR {target_amount:,}
- Risk tolerance: {risk_tolerance}

Simulation highlights:
- Median projected corpus: INR {stats.get('median_final_value', 0):,.0f}
- Mean projected corpus: INR {stats.get('mean_final_value', 0):,.0f}
- 10th percentile: INR {stats.get('percentile_10', 0):,.0f}
- 90th percentile: INR {stats.get('percentile_90', 0):,.0f}
- Probability of reaching target: {stats.get('success_rate', 'N/A')}%
- Gap to target: INR {abs(gap):,.0f} {'surplus' if gap >= 0 else 'shortfall'}

Respond as JSON with these keys: interpretation, statistics_explanation, initial_recommendations.
- interpretation: 2 sentences that frame the outlook.
- statistics_explanation: bullet style sentences joined with newlines that explain each metric in plain language.
- initial_recommendations: bullet style sentences joined with newlines outlining next steps (contribution changes, asset allocation, expert consultations).
"""

    try:
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {'role': 'system', 'content': 'You are a financial advisor specialising in retirement readiness.'},
                {'role': 'user', 'content': prompt},
            ],
            response_format={'type': 'json_object'},
            temperature=0.4,
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as exc:  # pragma: no cover - depends on remote API
        st.error(f'Could not generate interpretation: {exc}')
        return _default_interpretation(stats, target_amount)
