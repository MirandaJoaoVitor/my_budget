import streamlit as st
import pandas as pd
import plotly.express as px
from db import *

# Inicialização do banco de dados
init_db()

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

# Valores padrão dos sliders
default_values = {
    "Custos Fixos": 40,
    "Custos Variáveis": 15,
    "Metas": 10,
    "Lazer": 10,
    "Educação": 5,
    "Investimento": 20
}

# Categorias padrão
default_categorias = {
    "Receita": ["Salário/Renda principal", "Freelancer/Serviços", "Bônus/Comissões", "Reembolsos", "Outros/Extras"],
    "Custos Fixos": ["Aluguel", "Condomínio", "Internet/Telefone", "Energia", "Água", "Transporte/Combustível", "Supermercado", "Mensalidades"],
    "Custos Variáveis": ["Compras pessoais", "Cuidados pessoais", "Imprevistos", "Transporte/Veículo", "Alimentação fora"],
    "Metas": ["Reserva de Emergência", "Viagem", "Compras"],
    "Lazer": ["Restaurantes e bares", "Viagens e passeios", "Cinema, shows e eventos", "Hobbies"],
    "Educação": ["Curso online", "Livros e materiais", "Workshops e Eventos", "Mentoria", "Fundo de estudo"],
    "Investimento": ["Ações", "Renda Fixa", "Fundos Imobiliários", "Exterior", "Criptomoedas"],
    "Banco": ["Caixa", "Bradesco", "NuBank", "Banco do Brasil", "Dinheiro Vivo"]
}

# Session state inicial
if "user_data" not in st.session_state:
    st.session_state.user_data = load_alvo(default_values)

if "categorias" not in st.session_state:
    st.session_state.categorias = load_categorias(default_categorias)


# Layout da sidebar
col1, col2 = st.columns([1, 6])

with col1:
    with st.container(border=True):
        st.markdown("<p style='text-align: center'><b>Menu</b></p>", unsafe_allow_html=True)
        st.page_link("app.py", label="Resumo", icon="🧮")
        st.page_link("pages/1_lancamentos.py", label="Lançamentos", icon="📥")
        st.page_link("pages/2_settings.py", label="Configuração", icon="⚙️")
        st.page_link("pages/3_teste.py", label="Teste", icon="🧪")

with col2:
    ## Orçamento Alvo ----------
    with st.container(border=True):
        col11, col12 = st.columns([2, 1])
        with col11:
            st.markdown("#### 🎯 Orçamento Alvo")
            st.markdown("""
                Ajuste os percentuais para cada categoria. 
                """)
        with col12:
            salvar = st.button("Salvar", use_container_width=True)
            if st.button("Restaurar Padrão", use_container_width=True):
                st.session_state.user_data = default_values.copy()
                save_alvo(default_values)
                st.rerun()

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
                save_alvo(values)
                st.success("Configuração salva com sucesso! 💾")
            else:
                st.error("Não é possível salvar: o total deve ser exatamente 100%.")
    
    ## Categorias ----------
    with st.container(border=True):
        # Cabeçalho
        header_left, btn1_col, btn2_col = st.columns([2, 1, 1])
        with header_left:
            st.markdown("#### 🗂️ Categorias")
        with btn1_col:
            salvar_cats = st.button("Salvar Categorias", use_container_width=True)
        with btn2_col:
            restaurar_cats = st.button("Restaurar Categorias Padrão", use_container_width=True)

        
        col1, col2, col3 = st.columns(3)

        #Receitas
        with col1:
            st.markdown("<p style='text-align: center'><b>💰 Receitas</b></p>", unsafe_allow_html=True)
            receitas_df = pd.DataFrame({"Receitas": st.session_state.categorias.get("Receita", [])})
            receitas_editadas = st.data_editor(
                receitas_df,
                num_rows="dynamic",
                key="receitas_editor",
                use_container_width=True
            )

        # Investimentos
        with col2:
            st.markdown("<p style='text-align: center'><b>📈 Investimentos</b></p>", unsafe_allow_html=True)
            investimento_df = pd.DataFrame({"Investimento": st.session_state.categorias.get("Investimento", [])})
            investimento_editadas = st.data_editor(
                investimento_df,
                num_rows="dynamic",
                key="investimento_editor",
                use_container_width=True
            )

        # Banco
        with col3:
            st.markdown("<p style='text-align: center'><b>🏦 Banco</b></p>", unsafe_allow_html=True)
            banco_df = pd.DataFrame({"Banco": st.session_state.categorias.get("Banco", [])})
            banco_editadas = st.data_editor(
                banco_df,
                num_rows="dynamic",
                key="banco_editor",
                use_container_width=True
            )

        # Despesas
        st.markdown("<p style='text-align: center'><b>💸 Despesas</b></p>", unsafe_allow_html=True)
        desp_titles = ["Custos Fixos", "Custos Variáveis", "Metas", "Lazer", "Educação"]
        cols = st.columns(len(desp_titles))
        despesas_editados = {}
        for i, title in enumerate(desp_titles):
            with cols[i]:
                #st.markdown(f"**{title}**")
                df = pd.DataFrame({title: st.session_state.categorias.get(title, [])})
                despesas_editados[title] = st.data_editor(
                    df,
                    num_rows="dynamic",
                    key=f"desp_{title}",
                    use_container_width=True
                )

        # Ações dos botões (agora alinhados com o título)
        if salvar_cats:
            # Receitas
            st.session_state.categorias["Receita"] = receitas_editadas["Receitas"].dropna().tolist()

            # Despesas (cada título)
            for title, df in despesas_editados.items():
                st.session_state.categorias[title] = df[title].dropna().tolist()

            # Investimento e Banco
            st.session_state.categorias["Investimento"] = investimento_editadas["Investimento"].dropna().tolist()
            st.session_state.categorias["Banco"] = banco_editadas["Banco"].dropna().tolist()

            save_categorias(st.session_state.categorias)
            st.success("Categorias salvas com sucesso! 💾")

        if restaurar_cats:
            st.session_state.categorias = default_categorias.copy()
            save_categorias(default_categorias)
            st.rerun()
