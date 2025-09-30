# pages/3_lancamento.py
import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime, date
import uuid

DB_FILE = "data/lancamentos.db"
CATEGORIAS_FILE = "data/categorias.json"

# ---------- utilitários ----------
def ensure_data_dir():
    os.makedirs("data", exist_ok=True)

def init_db():
    ensure_data_dir()
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    cur = conn.cursor()
    # Mantive a coluna tags no DB por compatibilidade; o app NÃO usa mais tags.
    cur.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        type TEXT,
        category TEXT,
        amount REAL,
        account TEXT,
        description TEXT,
        tags TEXT,
        reconciled INTEGER DEFAULT 0,
        related_id TEXT,
        created_at TEXT
    )
    """)
    conn.commit()
    return conn

def load_categorias():
    import json
    if "categorias" in st.session_state:
        return st.session_state.categorias
    if os.path.exists(CATEGORIAS_FILE):
        with open(CATEGORIAS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            st.session_state.categorias = data
            return data
    default = {
        "Receita": ["Salário", "Renda Extra", "Projetos"],
        "Custos Fixos": ["Academia", "Combustível", "IPVA", "Celular", "Barbeiro"],
        "Custos Variáveis": ["Compras", "Cuidados", "Imprevistos", "Veículo", "Alimentação", "Saúde"],
        "Metas": ["Reserva de Emergência", "Viagem", "Compras"],
        "Lazer": ["Festa", "Saída", "Rolê"],
        "Educação": ["Livro", "Curso", "Material", "Fundo"],
        "Investimento": ["Ações", "Renda Fixa", "Fundos Imobiliários", "Exterior", "Criptomoedas"],
        "Banco": ["Nubank", "Banco do Brasil", "Caixa", "Dinheiro Vivo"]
    }
    st.session_state.categorias = default
    return default

def insert_transaction(conn, tx):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO transactions (date, type, category, amount, account, description, tags, reconciled, related_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        tx["date"], tx["type"], tx.get("category"), tx["amount"], tx.get("account"),
        tx.get("description"), None,  # tags não usado
        1 if tx.get("reconciled") else 0,
        tx.get("related_id"), tx["created_at"]
    ))
    conn.commit()
    return cur.lastrowid

def load_transactions_df(conn, filters=None):
    q = "SELECT * FROM transactions"
    params = []
    if filters:
        clauses = []
        if filters.get("start"):
            clauses.append("date >= ?"); params.append(filters["start"])
        if filters.get("end"):
            clauses.append("date <= ?"); params.append(filters["end"])
        if filters.get("type") and filters["type"] != "Todos":
            clauses.append("type = ?"); params.append(filters["type"])
        if filters.get("account") and filters["account"] != "Todos":
            clauses.append("account = ?"); params.append(filters["account"])
        if clauses:
            q += " WHERE " + " AND ".join(clauses)
    q += " ORDER BY date DESC, id DESC"
    df = pd.read_sql_query(q, conn, params=params)
    return df

def delete_transaction(conn, tx_id):
    cur = conn.cursor()
    cur.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
    conn.commit()

# ---------- reatividade: on_change handlers ----------
def on_tipo_change():
    tipo = st.session_state.get("tipo", "Receita")
    # ajustar categorias disponíveis imediatamente
    if tipo == "Receita":
        st.session_state["categoria_mode"] = "Receita"
        # set default category
        lista = cats.get("Receita", [])
        st.session_state["categoria_val"] = lista[0] if lista else ""
    elif tipo == "Despesa":
        st.session_state["categoria_mode"] = "Despesa_grupo"
        st.session_state["categoria_val"] = "Custos Fixos"
        # subcategoria default será definida na UI
    elif tipo == "Investimento":
        st.session_state["categoria_mode"] = "Investimento"
        st.session_state["categoria_val"] = cats.get("Investimento", [None])[0]
    else:  # Transferência
        st.session_state["categoria_mode"] = "Transferência"
        st.session_state["categoria_val"] = "Transferência"

# ---------- inicialização ----------


st.set_page_config(page_title="Lançamentos", layout="wide")
conn = init_db()
cats = load_categorias()

# garantir chaves iniciais de session_state
if "tipo" not in st.session_state:
    st.session_state["tipo"] = "Receita"
    st.session_state["categoria_mode"] = "Receita"
    st.session_state["categoria_val"] = cats.get("Receita", [""])[0] if cats.get("Receita") else ""
if "subcategory_val" not in st.session_state:
    st.session_state["subcategory_val"] = ""

st.title("📥 Lançamentos")

# --- Tipo fora do form (reativo sem callback) ---
tipo = st.selectbox("Tipo", ["Receita", "Despesa", "Investimento", "Transferência"], index=0, key="tipo")

# --- Formulário principal (sem callbacks nos widgets) ---
with st.form("novo_lancamento", clear_on_submit=False):
    col1, col2, col3 = st.columns([2,2,1])

    with col1:
        d = st.date_input("Data", date.today())
        # ler o tipo atual a partir do session_state
        tipo_atual = st.session_state.get("tipo", "Receita")

        if tipo_atual == "Receita":
            category = st.selectbox("Categoria", [""] + cats.get("Receita", []))
        elif tipo_atual == "Despesa":
            grupos = ["Custos Fixos", "Custos Variáveis", "Metas", "Lazer", "Educação"]
            grupo = st.selectbox("Categoria (grupo)", grupos)
            itens = cats.get(grupo, [])
            subcat = st.selectbox("Subcategoria", [""] + itens) if itens else st.text_input("Subcategoria")
            category = f"{grupo} :: {subcat}" if subcat else grupo
        elif tipo_atual == "Investimento":
            inv_mode = st.radio("Operação de investimento", ["Registrar (mesma conta)", "Transferir para conta de investimento"])
            category = st.selectbox("Categoria (investimento)", [""] + cats.get("Investimento", []))
        else:  # Transferência
            category = "Transferência"
            # campos from/to aparecerão no bloco de col2

        description = st.text_input("Descrição")

    with col2:
        amount = st.number_input("Valor (R$)", min_value=0.0, format="%.2f", step=1.0)
        accounts = cats.get("Banco", [])[:]
        if "Dinheiro Vivo" not in accounts:
            accounts.append("Dinheiro Vivo")

        if tipo_atual == "Transferência":
            from_acc = st.selectbox("De (conta)", accounts, key="from_acc")
            to_acc = st.selectbox("Para (conta)", accounts, key="to_acc")
        elif tipo_atual == "Investimento" and inv_mode == "Transferir para conta de investimento":
            from_acc = st.selectbox("De (conta)", accounts, key="inv_from_acc")
            to_acc = st.selectbox("Para (conta investimento)", accounts + ["Outra..."], key="inv_to_acc")
            if st.session_state.get("inv_to_acc") == "Outra...":
                to_acc = st.text_input("Nome da conta de investimento", key="inv_to_custom")
        else:
            account = st.selectbox("Conta/Banco", accounts + ["Outra..."], key="account")
            if account == "Outra...":
                account = st.text_input("Nome da conta", key="account_custom")

    with col3:
        reconciled = st.checkbox("Conciliar (marcar como reconciliado)", value=False)
        submitted = st.form_submit_button("Salvar Lançamento")  # <-- submit obrigatório dentro do form


# ---------- lógica de submissão ----------
if submitted:
    now_iso = datetime.utcnow().isoformat()
    # Recarregar tipo atual da sessão
    tipo = st.session_state["tipo"]

    if tipo == "Transferência":
        # pegar from/to do form; usar as chaves que existem
        fa = st.session_state.get("from_acc")
        ta = st.session_state.get("to_acc")
        if fa == ta:
            st.error("Conta de origem e destino não podem ser iguais para transferência.")
        else:
            group_id = str(uuid.uuid4())
            tx_out = {
                "date": d.isoformat(),
                "type": "Transferência",
                "category": "Transferência",
                "amount": -abs(amount),
                "account": fa,
                "description": description,
                "reconciled": reconciled,
                "related_id": group_id,
                "created_at": now_iso
            }
            tx_in = tx_out.copy()
            tx_in["amount"] = abs(amount)
            tx_in["account"] = ta
            insert_transaction(conn, tx_out)
            insert_transaction(conn, tx_in)
            st.success(f"Transferência R$ {amount:.2f} registrada: {fa} → {ta}")

    elif tipo == "Investimento":
        invest_mode = st.session_state.get("invest_mode", "Registrar (mesma conta)")
        if invest_mode == "Transferir para conta de investimento":
            fa = st.session_state.get("inv_from_acc")
            # inv_to_acc pode ser custom
            ta = st.session_state.get("inv_to_acc")
            if ta == "Conta Investimento (outra)...":
                ta = st.session_state.get("inv_to_custom")
            if not ta:
                st.error("Informe a conta de destino da aplicação.")
            elif fa == ta:
                st.error("Conta de origem e destino iguais: se deseja apenas registrar um investimento na mesma conta, escolha 'Registrar (mesma conta)'.")
            else:
                group_id = str(uuid.uuid4())
                tx_out = {
                    "date": d.isoformat(),
                    "type": "Investimento",
                    "category": category if category else "Investimento",
                    "amount": -abs(amount),
                    "account": fa,
                    "description": description,
                    "reconciled": reconciled,
                    "related_id": group_id,
                    "created_at": now_iso
                }
                tx_in = tx_out.copy()
                tx_in["amount"] = abs(amount)
                tx_in["account"] = ta
                insert_transaction(conn, tx_out)
                insert_transaction(conn, tx_in)
                st.success(f"Aplicação R$ {amount:.2f} registrada: {fa} → {ta}")
        else:
            # registrar na mesma conta como um gasto/investimento sem mover dinheiro de conta
            acct = st.session_state.get("inv_account")
            if acct == "Outra...":
                acct = st.session_state.get("inv_account_custom")
            if not acct:
                st.error("Informe a conta onde registrar o investimento.")
            else:
                tx = {
                    "date": d.isoformat(),
                    "type": "Investimento",
                    "category": category if category else "Investimento",
                    "amount": -abs(amount),  # considerar saída (investir)
                    "account": acct,
                    "description": description,
                    "reconciled": reconciled,
                    "related_id": None,
                    "created_at": now_iso
                }
                insert_transaction(conn, tx)
                st.success("Investimento registrado!")

    else:  # Receita ou Despesa
        if tipo == "Receita":
            sign = 1
        else:
            sign = -1
        # determinar account (pode ser account custom)
        if tipo == "Despesa":
            acct = st.session_state.get("account")
            if acct == "Outra...":
                acct = st.session_state.get("account_custom")
        else:
            acct = st.session_state.get("account")
            if acct == "Outra...":
                acct = st.session_state.get("account_custom")
        if not acct:
            st.error("Informe a conta.")
        else:
            tx = {
                "date": d.isoformat(),
                "type": tipo,
                "category": category,
                "amount": sign * abs(amount),
                "account": acct,
                "description": description,
                "reconciled": reconciled,
                "related_id": None,
                "created_at": now_iso
            }
            insert_transaction(conn, tx)
            st.success("Lançamento salvo!")

st.markdown("---")

# ---------- filtros e listagem (com opção de exclusão) ----------
left, right = st.columns([3,1])
with left:
    st.subheader("Lançamentos")
    colf1, colf2, colf3 = st.columns([1,1,1])
    with colf1:
        start = st.date_input("Data inicial", value=date.today().replace(day=1))
    with colf2:
        end = st.date_input("Data final", value=date.today())
    with colf3:
        tipo_filter = st.selectbox("Tipo (filtro)", ["Todos", "Receita","Despesa","Investimento","Transferência"])
    account_filter = st.selectbox("Conta (filtro)", ["Todos"] + cats.get("Banco", []) + ["Dinheiro Vivo"])
    df = load_transactions_df(conn, filters={
        "start": start.isoformat(),
        "end": end.isoformat(),
        "type": tipo_filter,
        "account": account_filter
    })
    st.write(f"Total registros: {len(df)}")
    if not df.empty:
        # mostrar tabela resumida
        df_display = df.copy()
        df_display["amount"] = df_display["amount"].map(lambda x: f"R$ {x:,.2f}")
        df_display = df_display[["id","date","type","category","amount","account","description","reconciled","related_id"]]
        st.dataframe(df_display, use_container_width=True)

        st.markdown("#### Excluir lançamento")
        # Select id to delete (mais seguro que many buttons)
        ids = df["id"].tolist()
        sel = st.selectbox("Escolha o ID para excluir", [""] + [str(i) for i in ids])
        if sel:
            if st.button("Excluir lançamento selecionado"):
                delete_transaction(conn, int(sel))
                st.success(f"Lançamento {sel} excluído.")
                st.experimental_rerun()

        csv = df.to_csv(index=False)
        st.download_button("Exportar CSV", csv, file_name="lancamentos_export.csv", mime="text/csv")
    else:
        st.info("Nenhum lançamento encontrado no período selecionado.")

with right:
    st.subheader("Saldos por conta")
    q = "SELECT account, SUM(amount) as balance FROM transactions GROUP BY account"
    balances = pd.read_sql_query(q, conn)
    if not balances.empty:
        balances["balance_fmt"] = balances["balance"].map(lambda x: f"R$ {x:,.2f}")
        st.table(balances[["account","balance_fmt"]].rename(columns={"account":"Conta","balance_fmt":"Saldo"}))
    else:
        st.write("Sem movimentos ainda.")
