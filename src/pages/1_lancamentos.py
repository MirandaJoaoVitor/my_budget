import streamlit as st
import pandas as pd
from datetime import date, datetime
import uuid
from db import *

# Inicialização
init_db()
conn = get_connection()

st.set_page_config(page_title="My Budget", page_icon="💰", layout="wide")

st.markdown("""
    <style>
        .block-container { padding-left: 2rem; padding-right: 2rem; }
    </style>
    """, unsafe_allow_html=True)



# -------- Layout --------
col1, col2 = st.columns([1, 6])
with col1:
    st.page_link("app.py", label="Resumo", icon="🧮")
    st.page_link("pages/1_lancamentos.py", label="Lançamentos", icon="📥")
    st.page_link("pages/2_settings.py", label="Configuração", icon="⚙️")
    st.page_link("pages/3_teste.py", label="Teste", icon="🧪")

with col2:
    # ----- Formulário -----
    with st.container(border=True):
        st.markdown("#### 📥 Adicionar Lançamentos")

        # Linha 1
        c1, c2, c3, c4 = st.columns([1,1,1,1])
        data = c1.date_input("Data", date.today())
        tipo = c2.selectbox("Tipo", ["Receita","Despesa","Investimento","Transferência"])
        bancos = st.session_state.categorias.get("Banco", [])

        if tipo in ["Transferência", "Investimento"]:
            de_banco = c3.selectbox("De", bancos)
            para_banco = c4.selectbox("Para", bancos)
        else:
            banco = c3.selectbox("Banco", bancos)
            para_banco = None

        # Linha 2
        c5, c6, c7, c8 = st.columns([1,1,1,2])
        if tipo == "Despesa":
            grupo = c5.selectbox("Grupo", ["Custos Fixos","Custos Variáveis","Metas","Lazer","Educação"])
            categoria = grupo
            subcategoria = c6.selectbox("Subcategoria", st.session_state.categorias.get(grupo, []))
        else:
            categoria = c5.selectbox("Categoria", st.session_state.categorias.get(tipo, []))
            subcategoria = ""

        valor = c7.number_input("Valor", min_value=0.0, step=0.01)
        descricao = c8.text_input("Descrição")

        salvar = st.button("Salvar", use_container_width=True)

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
                    transfer_id = str(uuid.uuid4())
                    categoria = "Investimento"
                    subcategoria = ""

                    if de_banco == para_banco:
                        # Apenas 1 lançamento (saída)
                        tx = {
                            "tipo": tipo,
                            "data": data.isoformat(),
                            "valor": -valor,
                            "categoria": categoria,
                            "subcategoria": subcategoria,
                            "banco": de_banco,
                            "id_transferencia": None,
                            "descricao": descricao
                        }
                        insert_transacao(tx)
                        st.success(f"Investimento registrado no próprio banco {de_banco}")
                    else:
                        # Dois lançamentos (saída + entrada)
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
                        st.success(f"Investimento registrado: {de_banco} → {para_banco}")

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
                    st.success("Receita registrada com sucesso!")

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
                    st.success("Despesa registrada com sucesso!")


    # ----- Listagem -----
    with st.container(border=True):
        st.markdown("#### 💲 Transações")
        df = load_transacoes()

        if not df.empty:
            df_disp = df.copy()
            df_disp["valor"] = df_disp["valor"].map(lambda x: f"R$ {x:,.2f}")
            df_disp["Excluir?"] = False

            # Exibir tabela sem a coluna id
            edited = st.data_editor(
                df_disp.drop(columns=["id"]),
                num_rows="fixed",
                hide_index=True,
                use_container_width=True
            )

            # Mapear IDs dos registros marcados para exclusão
            excluir_ids = df.loc[edited["Excluir?"], "id"].tolist()

            if excluir_ids and st.button("Excluir selecionados"):
                delete_transacoes(excluir_ids)
                st.success(f"{len(excluir_ids)} lançamentos excluídos.")
                st.rerun()
        else:
            st.info("Nenhum lançamento encontrado.")


