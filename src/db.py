import sqlite3
import os
import pandas as pd

DB_FILE = "data/budget.db"

def get_connection():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # Orçamento alvo
    cur.execute("""
    CREATE TABLE IF NOT EXISTS alvo_orcamento (
        categoria TEXT PRIMARY KEY,
        percentual INTEGER NOT NULL
    )
    """)

    # Categorias
    cur.execute("""
    CREATE TABLE IF NOT EXISTS categorias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT NOT NULL,
        categoria TEXT NOT NULL
    )
    """)

    # Transações
    cur.execute("""
    CREATE TABLE IF NOT EXISTS transacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT NOT NULL,
        data DATE DEFAULT CURRENT_DATE,
        valor REAL NOT NULL,
        categoria TEXT NOT NULL,
        subcategoria TEXT,
        banco TEXT,
        id_transferencia TEXT,
        descricao TEXT
    )
    """)

    conn.commit()
    conn.close()


# -------- FUNÇÕES AUXILIARES -------- #

# Orçamento alvo
def load_alvo(defaults):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT categoria, percentual FROM alvo_orcamento")
    rows = cur.fetchall()
    conn.close()
    if rows:
        return {cat: perc for cat, perc in rows}
    return defaults.copy()

def save_alvo(values):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM alvo_orcamento")  # reset
    for cat, perc in values.items():
        cur.execute("INSERT INTO alvo_orcamento (categoria, percentual) VALUES (?, ?)", (cat, perc))
    conn.commit()
    conn.close()

# Categorias
def load_categorias(defaults):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT tipo, categoria FROM categorias")
    rows = cur.fetchall()
    conn.close()
    if rows:
        categorias = {k: [] for k in defaults.keys()}
        for tipo, categoria in rows:
            if tipo in categorias:
                categorias[tipo].append(categoria)
        return categorias
    return defaults.copy()

def save_categorias(categorias):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM categorias")
    for tipo, lista in categorias.items():
        for cat in lista:
            cur.execute("INSERT INTO categorias (tipo, categoria) VALUES (?, ?)", (tipo, cat))
    conn.commit()
    conn.close()

# Transações
def insert_transacao(tx):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO transacoes (tipo, data, valor, categoria, subcategoria, banco, id_transferencia, descricao)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        tx["tipo"], tx["data"], tx["valor"], tx["categoria"],
        tx.get("subcategoria"), tx.get("banco"),
        tx.get("id_transferencia"), tx.get("descricao")
    ))
    conn.commit()
    conn.close()


def load_transacoes(filters=None):
    conn = get_connection()
    q = "SELECT * FROM transacoes"
    params, clauses = [], []
    if filters:
        if filters.get("start"):
            clauses.append("date(data) >= date(?)")
            params.append(filters["start"])
        if filters.get("end"):
            clauses.append("date(data) <= date(?)")
            params.append(filters["end"])
        if filters.get("tipo") and filters["tipo"] != "Todos":
            clauses.append("tipo = ?")
            params.append(filters["tipo"])
        if filters.get("banco") and filters["banco"] != "Todos":
            clauses.append("banco = ?")
            params.append(filters["banco"])
    if clauses:
        q += " WHERE " + " AND ".join(clauses)
    q += " ORDER BY data DESC, id DESC"
    df = pd.read_sql_query(q, conn, params=params)
    conn.close()
    return df


def delete_transacoes(ids):
    conn = get_connection()
    cur = conn.cursor()
    cur.executemany("DELETE FROM transacoes WHERE id = ?", [(i,) for i in ids])
    conn.commit()
    conn.close()
