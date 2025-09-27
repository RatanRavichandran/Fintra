"""Shared UI helpers for the Streamlit experience."""
from __future__ import annotations

from pathlib import Path

import streamlit as st

from config import get_path

BASE_CSS = r"""$css"""


def apply_global_styles() -> None:
    """Inject consistent styling across pages."""
    st.markdown(BASE_CSS, unsafe_allow_html=True)


def load_logo(width: int = 200) -> None:
    logo_path = get_path('assets', 'logo.png')
    if logo_path.exists():
        st.image(str(logo_path), width=width)
