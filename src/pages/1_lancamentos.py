import streamlit as st
from datetime import date, datetime
import uuid
from db import *

# Inicialização
init_db()
conn = get_connection()

# Configuração do app
st.set_page_config(
    page_title="My Budget",
    page_icon="💰",
    layout="wide"
)

st.markdown("""
    <style>
        .block-container { padding-left: 2rem; padding-right: 2rem; }
    </style>
    """, unsafe_allow_html=True)

# ========= Inicialização segura do session_state ========= #

# categorias
if "categorias" not in st.session_state:
    st.session_state.categorias = load_categorias({
        "Receita": [],
        "Custos Fixos": [],
        "Custos Variáveis": [],
        "Metas": [],
        "Lazer": [],
        "Educação": [],
        "Investimento": [],
        "Banco": []
    })

# alvo do orçamento (opcional, mas recomendado)
if "user_data" not in st.session_state:
    st.session_state.user_data = load_alvo({})


# -------- Layout --------
col1, col2 = st.columns([1, 6])
with col1:
    with st.container(border=True):
        st.markdown("<p style='text-align: center'><b>Menu</b></p>", unsafe_allow_html=True)
        st.page_link("app.py", label="Resumo", icon="🧮")
        st.page_link("pages/1_lancamentos.py", label="Lançamentos", icon="📥")
        st.page_link("pages/2_settings.py", label="Configuração", icon="⚙️")

with col2:
    # ----- Formulário -----
    with st.container(border=True):
        # cabeçalho
        cab_a, cab_b = st.columns([3,1])

        cab_a.markdown("#### 📥 Adicionar Lançamentos")

        salvar = cab_b.button("🚀 Adicionar lançamento", use_container_width=True)

        # Linha 1
        c1, c2, c3, c4 = st.columns([1,1,1,1])
        data = c1.date_input("Data", date.today())
        tipo = c2.selectbox("Tipo", ["Receita","Despesa","Investimento","Transferência"])

        if tipo == "Despesa":
            categoria = c3.selectbox("Categoria", ["Custos Fixos","Custos Variáveis","Metas","Lazer","Educação"])
            subcategoria = c4.selectbox("Subcategoria", st.session_state.categorias.get(categoria, []))

        elif tipo == "Investimento":
            categoria = c3.selectbox("Categoria", "Investimento", disabled=True)
            subcategoria = c4.selectbox("Tipo de Investimento", st.session_state.categorias.get("Investimento", []))

        else:
            categoria = c3.selectbox("Categoria", st.session_state.categorias.get(tipo, []))
            subcategoria = c4.selectbox("Subcategoria", st.session_state.categorias.get(categoria, []), disabled=True)


        # Linha 2
        c5, c6, c7, c8 = st.columns([1,1,1,1])
        
        bancos = st.session_state.categorias.get("Banco", [])

        valor = c5.number_input("Valor", min_value=0.0, step=50.0)

        if tipo in "Transferência":
            de_banco = c6.selectbox("De", bancos)
            para_banco = c7.selectbox("Para", bancos)
        else:
            banco = c6.selectbox("Banco", bancos)
            para_banco = c7.selectbox("Para", bancos, disabled=True)


        descricao = c8.text_input("Descrição")


        if salvar:
            # ---------------- Transferência ----------------
            if valor <= 0:
                st.error("Informe um valor maior que zero.")
            else:
                if tipo == "Transferência":
                    if de_banco == para_banco:
                        st.error("Banco de origem e destino não podem ser iguais.")
                    else:
                        transfer_id = str(uuid.uuid4())
                        categoria = "Transferência"
                        subcategoria = ""

                        tx_out = {
                            "tipo": tipo,
                            "data": data.isoformat(),
                            "valor": -valor,
                            "categoria": categoria,
                            "subcategoria": subcategoria,
                            "banco": de_banco,
                            "id_transferencia": transfer_id,
                            "descricao": descricao
                        }
                        tx_in = tx_out.copy()
                        tx_in["valor"] = valor
                        tx_in["banco"] = para_banco

                        insert_transacao(tx_out)
                        insert_transacao(tx_in)
                        st.success(f"Transferência registrada: {de_banco} → {para_banco}")

                # ---------------- Investimento ----------------
                elif tipo == "Investimento":

                    # investimento sempre: 1 lançamento (saída)
                    tx = {
                        "tipo": tipo,
                        "data": data.isoformat(),
                        "valor": -valor,
                        "categoria": categoria,   
                        "subcategoria": subcategoria,  
                        "banco": banco,     
                        "id_transferencia": None,
                        "descricao": descricao
                    }

                    insert_transacao(tx)
                    st.success(f"Investimento registrado em {subcategoria} (banco {banco})")

                # ---------------- Receita ----------------
                elif tipo == "Receita":
                    tx = {
                        "tipo": tipo,
                        "data": data.isoformat(),
                        "valor": valor,  # positivo
                        "categoria": categoria,
                        "subcategoria": subcategoria,
                        "banco": banco,
                        "id_transferencia": None,
                        "descricao": descricao
                    }
                    insert_transacao(tx)
                    st.success(f"Receita de R$ {valor:,.2f} registrada em {banco}")


                # ---------------- Despesa ----------------
                elif tipo == "Despesa":
                    tx = {
                        "tipo": tipo,
                        "data": data.isoformat(),
                        "valor": -valor,  # negativo
                        "categoria": categoria,
                        "subcategoria": subcategoria,
                        "banco": banco,
                        "id_transferencia": None,
                        "descricao": descricao
                    }
                    insert_transacao(tx)
                    st.success(f"Despesa de R$ {valor:,.2f} registrada em {banco}")


    # ----- Transações -----
    with st.container(border=True):
        col1, col2, col3 = st.columns([4, 1, 1])

        with col1:
            st.markdown("#### 💲 Transações")

        df = load_transacoes()
        
        if not df.empty:
            df_disp = df.copy()
            df_disp["valor"] = df_disp["valor"].map(lambda x: f"R$ {x:,.2f}")
            df_disp["Excluir?"] = False
            
            with col2:
                # Checkbox para selecionar tudo
                select_all = st.checkbox("Selecionar todos", value=False, key="select_all")

                if select_all:
                    df_disp["Excluir?"] = True
            
            with col3:
                excluir_selec = st.button("Excluir selecionados", use_container_width=True)

            # Exibir tabela sem a coluna id
            edited = st.data_editor(
                df_disp.drop(columns=["id"]),
                num_rows="fixed",
                hide_index=True,
                use_container_width=True
            )

            # Mapear IDs dos registros marcados para exclusão
            # Usar posições (iloc) para garantir alinhamento correto
            excluir_positions = [i for i, v in enumerate(edited["Excluir?"].tolist()) if v]
            excluir_ids = df.iloc[excluir_positions]["id"].tolist()

            if excluir_ids and excluir_selec:
                delete_transacoes(excluir_ids)
                st.success(f"{len(excluir_ids)} lançamentos excluídos.")
                st.rerun()
        else:
            st.info("Nenhum lançamento encontrado.")
