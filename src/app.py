import streamlit as st
import pandas as pd


# Configuração do app
st.set_page_config(
    page_title="My Budget",
    page_icon="💰",
    layout="wide"
)

# Custom CSS para ajustar o padding
st.markdown("""
    <style>
        .block-container {
            padding-left: 2rem;
            padding-right: 2rem;
        }
    </style>
    """, unsafe_allow_html=True)

col1, col2 = st.columns([1, 6])

with col1:
    st.page_link("app.py", label="Resumo", icon="🏠")
    st.page_link("pages/1_settings.py", label="Configuração", icon="⚙️")
    st.page_link("pages/2_teste.py", label="Teste", icon="🧪")

with col2:
    st.expander("Sobre o app", expanded=True).markdown(
        """
        ## My Budget
        Este é um app para controle de orçamento pessoal. 
        """
    )