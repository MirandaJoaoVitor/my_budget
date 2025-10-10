# app.py
import streamlit as st
import pandas as pd
import calendar
from datetime import date
import plotly.express as px
from db import init_db, load_transacoes, load_categorias, load_alvo

# Inicialização do banco de dados
init_db()

# Configuração do app
st.set_page_config(
    page_title="My Budget",
    page_icon="💰",
    layout="wide"
)

# Custom CSS para ajustar o padding (mesmo estilo das outras páginas)
st.markdown(
    """
    <style>
        .block-container {
            padding-left: 2rem;
            padding-right: 2rem;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Navegação lateral (mesma que você vinha usando)
col1, col2 = st.columns([1, 6])

with col1:
    st.page_link("app.py", label="Resumo", icon="🧮")
    st.page_link("pages/1_lancamentos.py", label="Lançamentos", icon="📥")
    st.page_link("pages/2_settings.py", label="Configuração", icon="⚙️")
    st.page_link("pages/3_teste.py", label="Teste", icon="🧪")

# Defaults (copiei os defaults usados nas outras telas como fallback)
default_values = {
    "Custos Fixos": 40,
    "Custos Variáveis": 20,
    "Metas": 5,
    "Lazer": 5,
    "Educação": 5,
    "Investimento": 25
}

default_categorias = {
    "Receita": ["Salário", "Renda Extra", "Projetos"],
    "Custos Fixos": ["Academia", "Combustível", "IPVA", "Celular", "Barbeiro"],
    "Custos Variáveis": ["Compras", "Cuidados", "Imprevistos", "Veículo", "Alimentação", "Saúde"],
    "Metas": ["Reserva de Emergência", "Viagem", "Compras"],
    "Lazer": ["Festa", "Saída", "Rolê"],
    "Educação": ["Livro", "Curso", "Material", "Fundo"],
    "Investimento": ["Ações", "Renda Fixa", "Fundos Imobiliários", "Exterior", "Criptomoedas"],
    "Banco": ["Nubank", "Banco do Brasil", "Caixa", "Dinheiro Vivo"]
}

with col2:
    st.expander("Sobre o app", expanded=True).markdown(
        """
        ## My Budget
        Painel resumo: filtro por período, receitas, despesas, comparação com orçamento alvo e saldo por banco.
        """
    )

# -------------------------
# FILTROS (topo)
# -------------------------
# Para preencher lista de anos, carregamos todas as transações (pequeno custo em DB local)
df_all = load_transacoes()
if not df_all.empty:
    df_all["data"] = pd.to_datetime(df_all["data"])
    anos_disponiveis = sorted(df_all["data"].dt.year.unique().tolist())
else:
    anos_disponiveis = [date.today().year]

col_f1, col_f2, col_f3 = st.columns([2, 4, 1])
with col_f1:
    ano_selecionado = st.selectbox("Ano", anos_disponiveis, index=(anos_disponiveis.index(date.today().year) if date.today().year in anos_disponiveis else 0))
with col_f2:
    month_names = list(calendar.month_name)[1:]  # janeiro..dezembro
    # select_slider com nomes de meses (retorna tupla)
    periodo_meses = st.select_slider("Período (mês início → mês fim)", options=month_names,
                                    value=(month_names[0], month_names[date.today().month - 1]))
    mes_inicio = month_names.index(periodo_meses[0]) + 1
    mes_fim = month_names.index(periodo_meses[1]) + 1
with col_f3:
    st.write("")  # espaço

# construir start / end date
start_date = f"{ano_selecionado}-{mes_inicio:02d}-01"
last_day = calendar.monthrange(ano_selecionado, mes_fim)[1]
end_date = f"{ano_selecionado}-{mes_fim:02d}-{last_day:02d}"

# carregar transações do período
df = load_transacoes(filters={"start": start_date, "end": end_date})
if not df.empty:
    df["data"] = pd.to_datetime(df["data"])
else:
    # garantir df com colunas esperadas para evitar keyerrors depois
    df = pd.DataFrame(columns=["id","tipo","data","valor","categoria","subcategoria","banco","id_transferencia","descricao"])

# carregar categorias e alvo
alvo = load_alvo(default_values)
categorias = load_categorias(default_categorias)

# -------------------------
# KPI's principais
# -------------------------
# cálculo de totais
total_receita = df.loc[df["tipo"] == "Receita", "valor"].sum() if not df.empty else 0.0
# despesas e investimentos como saída (valores positivos para exibição)
total_despesas = - df.loc[df["tipo"].isin(["Despesa", "Investimento"]), "valor"].sum() if not df.empty else 0.0
saldo_periodo = df["valor"].sum() if not df.empty else 0.0

st.markdown("---")
k1, k2, k3 = st.columns(3)
k1.metric("Receita (período)", f"R$ {total_receita:,.2f}")
k2.metric("Despesas (período)", f"R$ {total_despesas:,.2f}")
k3.metric("Saldo (período)", f"R$ {saldo_periodo:,.2f}")

# -------------------------
# Layout principal: 2 colunas
# -------------------------
left_col, right_col = st.columns([2, 1.6])

# --------- LEFT: Receitas e Despesas -----------
with left_col:
    # Receitas por categoria
    with st.container():
        st.markdown("#### 💰 Receitas")
        receitas = df[df["tipo"] == "Receita"]
        if not receitas.empty:
            rec_by_cat = receitas.groupby("categoria")["valor"].sum().reset_index().sort_values("valor", ascending=False)
            rec_by_cat["valor_fmt"] = rec_by_cat["valor"].map(lambda x: f"R$ {x:,.2f}")
            st.dataframe(rec_by_cat[["categoria", "valor_fmt"]].rename(columns={"categoria":"Categoria", "valor_fmt":"Valor"}), use_container_width=True)
        else:
            st.info("Nenhuma receita encontrada no período selecionado.")

    st.markdown("")
    # Despesas: agrupadas por categoria de orçamento (Custos Fixos, Custos Variáveis, ...)
    with st.container():
        st.markdown("#### 💸 Despesas")
        despesas = df[df["tipo"] == "Despesa"]
        if not despesas.empty:
            # total por categoria (essas categorias correspondem aos grupos definidos nas configurações)
            exp_by_cat = despesas.groupby("categoria")["valor"].sum().abs().reset_index().sort_values("valor", ascending=False)
            exp_by_cat["valor_fmt"] = exp_by_cat["valor"].map(lambda x: f"R$ {x:,.2f}")
            st.dataframe(exp_by_cat[["categoria", "valor_fmt"]].rename(columns={"categoria":"Categoria", "valor_fmt":"Valor"}), use_container_width=True)

            st.markdown("**Detalhe por subcategoria (despesas)**")
            subcat = despesas.groupby(["categoria", "subcategoria"])["valor"].sum().abs().reset_index().sort_values("valor", ascending=False)
            subcat["valor_fmt"] = subcat["valor"].map(lambda x: f"R$ {x:,.2f}")
            st.dataframe(subcat[["categoria","subcategoria","valor_fmt"]].rename(columns={"categoria":"Categoria","subcategoria":"Subcategoria","valor_fmt":"Valor"}), use_container_width=True)
        else:
            st.info("Nenhuma despesa encontrada no período selecionado.")

# --------- RIGHT: Orçamento vs Gasto e Saldo por banco -----------
with right_col:
    # Orçamento vs gasto
    with st.container():
        st.markdown("#### 🎯 Orçamento: Alvo × Gasto")
        rows = []
        # percorre categorias do alvo (Custos Fixos, Custos Variáveis, Metas, Lazer, Educação, Investimento, ...)
        for cat, perc in alvo.items():
            # alvo em valor baseado na receita do período
            alvo_valor = total_receita * (perc / 100) if total_receita > 0 else 0.0
            # gasto real: somar transações do período com essa categoria (Despesa e Investimento quando aplicável)
            mask = (df["categoria"] == cat) & (df["tipo"].isin(["Despesa", "Investimento"]))
            gasto_valor = - df.loc[mask, "valor"].sum() if not df.loc[mask].empty else 0.0
            pct_usado = (gasto_valor / alvo_valor * 100) if (alvo_valor > 0) else None
            rows.append({
                "Categoria": cat,
                "Percentual Alvo (%)": perc,
                "Valor Alvo (R$)": round(alvo_valor, 2),
                "Gasto Real (R$)": round(gasto_valor, 2),
                "% Usado": None if pct_usado is None else round(pct_usado, 2)
            })

        budget_df = pd.DataFrame(rows)
        if not budget_df.empty:
            # formatar para exibição
            display_df = budget_df.copy()
            display_df["Valor Alvo (R$)"] = display_df["Valor Alvo (R$)"].map(lambda x: f"R$ {x:,.2f}")
            display_df["Gasto Real (R$)"] = display_df["Gasto Real (R$)"].map(lambda x: f"R$ {x:,.2f}")
            display_df["% Usado"] = display_df["% Usado"].map(lambda x: f"{x:.2f}%" if pd.notna(x) else "—")
            st.dataframe(display_df.rename(columns={"Categoria":"Categoria","Percentual Alvo (%)":"% Alvo","Valor Alvo (R$)":"Alvo","Gasto Real (R$)":"Gasto"}), use_container_width=True)

            # gráfico comparativo (Alvo vs Gasto)
            # montar df para gráfico
            melt = budget_df.melt(id_vars=["Categoria"], value_vars=["Valor Alvo (R$)", "Gasto Real (R$)"])
            # os valores estão em números mas podem conter round; garantir nomes certos
            melt = melt.rename(columns={"value":"Valor", "variable":"Tipo"})
            fig = px.bar(melt, x="Categoria", y="Valor", color="Tipo", barmode="group")
            fig.update_layout(height=350, margin=dict(t=30, b=30))
            st.plotly_chart(fig, use_container_width=True)

            # pequenos indicadores de alerta quando passou do alvo
            st.markdown("**Alertas**")
            over = budget_df[budget_df["% Usado"].notna() & (budget_df["% Usado"] > 100)]
            if not over.empty:
                for _, r in over.iterrows():
                    st.warning(f"{r['Categoria']}: {r['% Usado']:.1f}% do alvo (ultrapassou).")
            else:
                st.success("Nenhuma categoria ultrapassou o alvo no período selecionado.")
        else:
            st.info("Nenhum dado de orçamento disponível.")

    st.markdown("")
    # Saldo por banco (acumulado até end_date)
    with st.container():
        st.markdown(f"#### 🏦 Saldo por Banco (até {end_date})")
        df_bancos = load_transacoes(filters={"end": end_date})
        if not df_bancos.empty:
            df_bancos["data"] = pd.to_datetime(df_bancos["data"])
            bal = df_bancos.groupby("banco")["valor"].sum().reset_index().dropna(subset=["banco"])
            if not bal.empty:
                bal["Saldo"] = bal["valor"].map(lambda x: f"R$ {x:,.2f}")
                st.dataframe(bal[["banco","Saldo"]].rename(columns={"banco":"Banco"}), use_container_width=True)
                st.markdown(f"**Saldo total (todos bancos)**: R$ {bal['valor'].sum():,.2f}")
            else:
                st.info("Nenhum lançamento com banco registrado.")
        else:
            st.info("Nenhuma transação encontrada para calcular saldo por banco até a data selecionada.")
