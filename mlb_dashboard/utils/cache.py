from __future__ import annotations

import streamlit as st


def cache_data(ttl: int = 3600, show_spinner: bool = False):
    return st.cache_data(ttl=ttl, show_spinner=show_spinner)
