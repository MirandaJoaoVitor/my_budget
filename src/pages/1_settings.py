import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os


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

# Nome do arquivo para salvar os dados do usuário
ALVO_FILE = "data/oracamento_alvo.json"

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
    if os.path.exists(ALVO_FILE):
        with open(ALVO_FILE, "r") as file:
            return json.load(file)
    return default_values.copy()

# Função para salvar os valores atuais
def save_user_data(data):
    with open(ALVO_FILE, "w") as file:
        json.dump(data, file)

# Função para restaurar os valores padrão
def reset_to_default():
    save_user_data(default_values)
    st.session_state.user_data = default_values.copy()
    st.rerun()

# Carregar os valores do usuário ou padrão
if "user_data" not in st.session_state:
    st.session_state.user_data = load_user_data()

# Nome do arquivo para salvar as categorias
CATEGORIAS_FILE = "data/categorias.json"

default_categorias = {
    "Receita": ["Salário", "Renda Extra", "Projetos"],
    "Despesa": ["Custos Fixos", "Custos Variáveis", "Metas", "Lazer", "Educação", "Investimento"]
}

# Funções utilitárias
def load_categorias():
    if os.path.exists(CATEGORIAS_FILE):
        with open(CATEGORIAS_FILE, "r") as f:
            return json.load(f)
    return default_categorias.copy()

def save_categorias(data):
    with open(CATEGORIAS_FILE, "w") as f:
        json.dump(data, f)

# Carregar no session_state ao iniciar
if "categorias" not in st.session_state:
    st.session_state.categorias = load_categorias()


# Criar layout da sidebar
col1, col2 = st.columns([1, 6])

with col1:
    st.page_link("app.py", label="Resumo", icon="🏠")
    st.page_link("pages/1_settings.py", label="Configuração", icon="⚙️")
    st.page_link("pages/2_teste.py", label="Teste", icon="🧪")

with col2:
    with st.container(border=True):
        col11, col12 = st.columns([2, 1])

        with col11:
            st.markdown("#### 🎯 Orçamento Alvo")
            st.markdown("""
                Ajuste os percentuais para cada categoria de despesa. 
                """)

        with col12:
            salvar = st.button("Salvar", use_container_width=True)
            if st.button("Restaurar Padrão", use_container_width=True):
                reset_to_default()

        coll21, coll22 = st.columns([2, 1])

        with coll21:
            with st.container(border=True):
                values = {}
                for categoria, valor in st.session_state.user_data.items():
                    values[categoria] = st.slider(categoria, 0, 100, valor, 1, format="%d%%")

                # DataFrame atualizado em tempo real
                df = pd.DataFrame(list(values.items()), columns=["Categoria", "Valor"])

        with coll22:
            with st.container(border=True):
                total = df["Valor"].sum()

                # Total sempre atualizado
                st.markdown(
                    f"""
                    <p style='text-align: center; font-size: 1.5rem; color: #FFFFFF'>
                    Total: {total} %
                    </p>
                    """,
                    unsafe_allow_html=True
                )

                # Mensagem de validação
                if total > 100:
                    st.error("❌ O total não pode ultrapassar 100%!")
                elif total < 100:
                    st.warning(f"⚠️ Ainda faltam {100 - total}% para completar 100%.")
                else:
                    st.success("✅ Percentual correto!")

                # Gráfico atualizado em tempo real
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


        # Lógica do botão salvar
        if salvar:
            if total == 100:
                st.session_state.user_data = values
                save_user_data(values)
                st.success("Configuração salva com sucesso! 💾")
            else:
                st.error("Não é possível salvar: o total deve ser exatamente 100%.")
    

    with st.container(border=True):
        st.markdown("### 🗂️ Categorias")

        # Editor de Receitas
        st.subheader("💰 Receitas")
        receitas_df = pd.DataFrame({"Categoria": st.session_state.categorias["Receita"]})
        receitas_editadas = st.data_editor(receitas_df, num_rows="dynamic", use_container_width=True)

        # Editor de Despesas
        st.subheader("💸 Despesas")
        despesas_df = pd.DataFrame({"Categoria": st.session_state.categorias["Despesa"]})
        despesas_editadas = st.data_editor(despesas_df, num_rows="dynamic", use_container_width=True)

        # Botões
        colA, colB = st.columns(2)
        with colA:
            if st.button("Salvar Categorias", use_container_width=True):
                st.session_state.categorias["Receita"] = receitas_editadas["Categoria"].dropna().tolist()
                st.session_state.categorias["Despesa"] = despesas_editadas["Categoria"].dropna().tolist()
                save_categorias(st.session_state.categorias)
                st.success("Categorias salvas em arquivo! ✅")

        with colB:
            if st.button("Restaurar Categorias Padrão", use_container_width=True):
                st.session_state.categorias = default_categorias.copy()
                save_categorias(default_categorias)
                st.rerun()