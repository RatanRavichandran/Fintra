"""Agent definitions used across Streamlit pages."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.serpapi import SerpApiTools

from .config import get_settings

settings = get_settings()
ALLOWED_SOURCES: List[str] = [
    'investopedia.com',
    'morningstar.com',
    'bloomberg.com',
    'reuters.com',
    'ft.com',
    'wsj.com',
    'marketwatch.com',
    'fred.stlouisfed.org',
    'sec.gov',
    'data.worldbank.org',
    'data.imf.org',
]


class DisabledAgent:
    """Fallback agent that returns a helpful message when configuration is missing."""

    def __init__(self, reason: str) -> None:
        self.reason = reason

    def run(self, *_args, **_kwargs):  # pragma: no cover - simple passthrough
        return type('Response', (), {'content': self.reason})


def _build_model() -> OpenAIChat | None:
    if not settings.are_llm_keys_configured:
        return None
    return OpenAIChat(id=settings.openai_model, api_key=settings.openai_api_key)


def _build_tools() -> Iterable[SerpApiTools]:
    if settings.is_search_configured:
        yield SerpApiTools(api_key=settings.serpapi_api_key)


def _agent_disabled_message(agent_name: str) -> str:
    missing = []
    if not settings.are_llm_keys_configured:
        missing.append('OPENAI_API_KEY')
    if agent_name == 'Researcher' and not settings.is_search_configured:
        missing.append('SERPAPI_API_KEY')
    formatted = ', '.join(missing)
    return f"{agent_name} is unavailable. Configure {formatted} to enable this feature."


def _create_agent(agent_name: str, role: str, description: str, instructions: List[str]) -> Agent | DisabledAgent:
    model = _build_model()
    if not model:
        return DisabledAgent(_agent_disabled_message(agent_name))

    tools = list(_build_tools()) if agent_name == 'Researcher' else []
    return Agent(
        name=agent_name,
        role=role,
        model=model,
        description=description,
        instructions=instructions,
        tools=tools,
        add_datetime_to_instructions=True,
    )


_research_guidelines = [
    'Generate three to five targeted search terms based on the Indian financial context.',
    'Use the search tool for each term and analyse the most relevant findings.',
    'Only cite reputable sources: ' + ', '.join(ALLOWED_SOURCES) + '.',
    'Present key takeaways with URLs and avoid giving definitive investment advice.',
]

researcher = _create_agent(
    agent_name='Researcher',
    role='Finds financial insights tailored for Indian investors.',
    description='Search specialist that curates timely market intelligence for the rest of the system.',
    instructions=_research_guidelines,
)

_financial_planner_guidelines = [
    'Build a personalised plan with budgets, savings, and investment actions for Indian households.',
    'Incorporate Indian investment vehicles such as PPF, NPS, and ELSS when relevant.',
    'Factor in Indian tax considerations including Section 80C and related deductions.',
    'Support every recommendation with references to the allowed sources list.',
]

financial_planner = _create_agent(
    agent_name='Financial Planner',
    role='Transforms research insights into an integrated financial plan.',
    description='Senior advisor that prepares detailed, goal aligned plans for Indian users.',
    instructions=_financial_planner_guidelines,
)

_investment_guidelines = [
    'Assess the user profile and recommend asset allocations with Indian investment options.',
    'Summarise mutual funds, ETFs, and other securities with clear risk notes.',
    'Return actionable next steps and cite all factual claims.',
]

investment_advisor = _create_agent(
    agent_name='Investment Advisor',
    role='Curates investment opportunities that fit the user risk profile.',
    description='Generates diversified investment suggestions specific to the Indian market.',
    instructions=_investment_guidelines,
)

_debt_guidelines = [
    'Review liabilities and prioritise repayments based on interest costs.',
    'Recommend Indian debt management strategies such as avalanche or consolidation.',
    'Suggest ways to improve repayment capacity and include timeline estimates.',
]

debt_manager = _create_agent(
    agent_name='Debt Manager',
    role='Creates a debt reduction roadmap for the household.',
    description='Highlights risk areas across loans and credit lines with practical next steps.',
    instructions=_debt_guidelines,
)

_subscription_guidelines = [
    'Analyse recurring subscriptions and identify redundant spend.',
    'Suggest local alternatives or negotiation tactics for Indian service providers.',
    'Share the projected monthly and annual savings for every recommendation.',
]

subscription_manager = _create_agent(
    agent_name='Subscription Manager',
    role='Optimises recurring household spending.',
    description='Looks for overlaps and savings opportunities within subscription portfolios.',
    instructions=_subscription_guidelines,
)
