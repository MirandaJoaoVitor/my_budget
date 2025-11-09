import streamlit as st
import pandas as pd
from db import *
import calendar
from datetime import date


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

# Alvos padrão (fallback)
default_values = {
    "Custos Fixos": 40,
    "Custos Variáveis": 15,
    "Metas": 10,
    "Lazer": 10,
    "Educação": 5,
    "Investimento": 20
}

# Categorias padrão (fallback)
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


col1, col2 = st.columns([1, 6])

with col1:
    with st.container(border=True):
        st.markdown("<p style='text-align: center'><b>Menu</b></p>", unsafe_allow_html=True)
        st.page_link("app.py", label="Resumo", icon="🧮")
        st.page_link("pages/1_lancamentos.py", label="Lançamentos", icon="📥")
        st.page_link("pages/2_settings.py", label="Configuração", icon="⚙️")
        st.page_link("pages/3_teste.py", label="Teste", icon="🧪")

with col2:
    with st.container(border=True):
        # Filtrar anos disponíveis ----------
        df_all = load_transacoes()
        if not df_all.empty:
            df_all["data"] = pd.to_datetime(df_all["data"])
            anos_disponiveis = sorted(df_all["data"].dt.year.unique().tolist())
        else:
            anos_disponiveis = [date.today().year]

        col21, col22, col23, col24 = st.columns([1, 25, 1, 5])
        
        with col22:
            month_names = list(calendar.month_name)[1:]  # janeiro..dezembro
            # select_slider com nomes de meses (retorna tupla)
            periodo_meses = st.select_slider("🗓️ Período", options=month_names,
                                            value=(month_names[0], month_names[date.today().month - 1]))
            mes_inicio = month_names.index(periodo_meses[0]) + 1
            mes_fim = month_names.index(periodo_meses[1]) + 1
        
        with col24:
            ano_selecionado = st.selectbox(" Ano", anos_disponiveis, index=(anos_disponiveis.index(date.today().year) if date.today().year in anos_disponiveis else 0))

    ## --------- Carregar dados --------
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

    # Valores resumo ----------
    col31, col32, col33, col34 = st.columns(4)

    with col31:
        with st.container(border=True):
            # receitas
            total_receita = df.loc[df["tipo"] == "Receita", "valor"].sum() if not df.empty else 0.0

            st.markdown("💰 Receitas")
            st.markdown(f"<p style='text-align: right; font-size: 34px; line-height: 0.5;'>R$ {total_receita:.2f}</p>", unsafe_allow_html=True) #color: #00B050

    with col32:
        with st.container(border=True):
            # despesas
            total_despesas = - df.loc[df["tipo"].isin(["Despesa", "Investimento"]), "valor"].sum() if not df.empty else 0.0

            st.markdown("💸 Despesas")
            st.markdown(f"<p style='text-align: right; font-size: 34px; line-height: 0.5;'>R$ {total_despesas:.2f}</p>", unsafe_allow_html=True) #color: #FF0000
    
    with col33:
        with st.container(border=True):
            # percentual despesas / receitas
            percentual = (total_despesas / total_receita) * 100 if total_receita != 0 else 0

            st.markdown("🎯 Percentual")
            st.markdown(f"<p style='text-align: right; font-size: 34px; line-height: 0.5;'>{percentual:.2f} %</p>", unsafe_allow_html=True)
    
    with col34:
        with st.container(border=True):
            # saldo
            saldo_periodo = df["valor"].sum() if not df.empty else 0.0

            st.markdown("📊 Saldo")
            st.markdown(f"<p style='text-align: right; font-size: 34px; line-height: 0.5;'>R$ {saldo_periodo:.2f}</p>", unsafe_allow_html=True)

    col41, col42, col43 = st.columns([1, 2, 1])

    with col41:
        receitas = df[df["tipo"] == "Receita"]
        if not receitas.empty:
            rec_by_cat = receitas.groupby("categoria")["valor"].sum().reset_index().sort_values("valor", ascending=False)
            rec_by_cat["valor_fmt"] = rec_by_cat["valor"].map(lambda x: f"R$ {x:,.2f}")
            st.dataframe(
                rec_by_cat[["categoria", "valor_fmt"]]
                    .rename(columns={"categoria": "Categoria", "valor_fmt": "Valor"}),
                use_container_width=True,
                hide_index=True
            )

        else:
            st.info("Nenhuma receita encontrada no período selecionado.")

    with col42:
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
                "Valor Gasto (R$)": round(gasto_valor, 2),
                "Valor Alvo (R$)": round(alvo_valor, 2),
                "Percentual Alvo (%)": perc,
                "% Usado": None if pct_usado is None else round(pct_usado, 2)
            })
        
        budget_df = pd.DataFrame(rows)
        if not budget_df.empty:
            # formatar para exibição
            display_df = budget_df.copy()
            display_df["Valor Alvo (R$)"] = display_df["Valor Alvo (R$)"].map(lambda x: f"R$ {x:,.2f}")
            display_df["Valor Gasto (R$)"] = display_df["Valor Gasto (R$)"].map(lambda x: f"R$ {x:,.2f}")
            display_df["% Usado"] = display_df["% Usado"].map(lambda x: f"{x:.2f}%" if pd.notna(x) else "—")
            
            st.dataframe(
                display_df.rename(columns={"Categoria":"Categoria","Percentual Alvo (%)":"% Alvo","Valor Alvo (R$)":"Alvo","Valor Gasto (R$)":"Gasto"}),
                use_container_width=True,
                hide_index=True
            )

    with col43:
        df_bancos = load_transacoes(filters={"end": end_date})
        if not df_bancos.empty:
            df_bancos["data"] = pd.to_datetime(df_bancos["data"])
            bal = df_bancos.groupby("banco")["valor"].sum().reset_index().dropna(subset=["banco"])
            if not bal.empty:
                bal["Saldo"] = bal["valor"].map(lambda x: f"R$ {x:,.2f}")
                st.dataframe(bal[["banco","Saldo"]].rename(columns={"banco":"Banco"}), use_container_width=True, hide_index=True)
            else:
                st.info("Nenhum lançamento com banco registrado.")
        else:
            st.info("Nenhuma transação encontrada para calcular saldo por banco até a data selecionada.")


df