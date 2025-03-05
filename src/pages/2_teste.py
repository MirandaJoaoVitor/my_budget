import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os

# Nome do arquivo para salvar os dados do usuário
SAVE_FILE = "data/user_data.json"

# Configuração do app
st.set_page_config(
    page_title="My Budget",
    page_icon="💰",
    layout="wide"
)

# Valores padrão dos sliders
default_values = {
    "Custos Fixos": 40,
    "Custos Variáveis": 20,
    "Metas": 5,
    "Lazer": 5,
    "Educação": 5,
    "Investimento": 25
}

# Função para carregar os valores salvos do usuário
def load_user_data():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as file:
            return json.load(file)
    return default_values.copy()

# Função para salvar os valores atuais
def save_user_data(data):
    with open(SAVE_FILE, "w") as file:
        json.dump(data, file)

# Função para restaurar os valores padrão
def reset_to_default():
    save_user_data(default_values)
    st.session_state.user_data = default_values.copy()
    st.rerun()

# Carregar os valores do usuário ou padrão
if "user_data" not in st.session_state:
    st.session_state.user_data = load_user_data()

# Criar layout da sidebar
col1, col2 = st.columns([1, 5])

with col1:
    st.page_link("app.py", label="Resumo", icon="🏠")
    st.page_link("pages/1_settings.py", label="Configuração", icon="⚙️")
    st.page_link("pages/2_teste.py", label="Teste", icon="🧪")

with col2:
    col11, col12 = st.columns([2, 1])

    with col11:
        st.markdown(
            """
            <div style="text-align: left; margin-bottom: 2rem">
            <h1 style='text-align: left; font-size: 1.5rem; color: #FFFFFF'>Alvo</h1>
            <p style='text-align: left; line-height: 0.2; font-size: 1rem; color: #f8f69f'>Edite os itens abaixo para ajustar seu alvo conforme a sua realidade.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col12:
        salvar = st.button("Salvar", use_container_width=True)

    coll21, coll22 = st.columns([2, 1])

    with coll21:
        with st.container(border=True):
            values = {}
            for categoria, valor in st.session_state.user_data.items():
                values[categoria] = st.slider(categoria, 0, 100, valor, 1, format="%d%%")
            
            # Criar dataframe com os valores atuais
            df = pd.DataFrame(list(st.session_state.user_data.items()), columns=["Categoria", "Valor"])

            if salvar:
                # Atualizar os valores e salvar automaticamente
                st.session_state.user_data = values
                save_user_data(values)


    with coll22:
        with st.container(border=True):
            
            total = df["Valor"].sum()

            st.markdown(
            f"""
            <p style='text-align: center; font-size: 1.5rem; color: #FFFFFF'>Total: {total} %</p>
            """,
            unsafe_allow_html=True
        )
            
            # Criar gráfico de rosca
            fig = px.pie(df, names="Categoria", values="Valor", hole=0.5, color_discrete_sequence=px.colors.qualitative.Set3)
            fig.update_layout(
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.3,
                    xanchor="center",
                    x=0.5
                )
            )
            st.plotly_chart(fig)

        if st.button("Restaurar Padrão", use_container_width=True):
            reset_to_default()

