import streamlit as st
import pandas as pd

# ---------------- CONFIGURAÇÃO DA PÁGINA ----------------
st.set_page_config(
    page_title="LABCOST – Simulador de Gastos e Custos",
    layout="wide",
)

# ---------------- TABS PRINCIPAIS ----------------
tab_simulador, tab_classificacao = st.tabs(
    ["💻 Simulador de Gastos e Custos", "📚 Classificação de Gastos"]
)

# =========================================================
# TAB 1 – SIMULADOR DE GASTOS E CUSTOS
# =========================================================
with tab_simulador:
    st.title("LABCOST – Simulador de Gastos e Custos")

    st.write(
        """
        O **LABCOST** é uma ferramenta educacional que auxilia estudantes e gestores a compreenderem  
        **comportamento dos gastos, margem de contribuição, ponto de equilíbrio e alavancagem operacional**.  

        Abaixo você pode escolher entre dois modos de análise:
        - **Produto único**  
        - **Mix de produtos** (vários produtos com cálculo de mix e ponto de equilíbrio conjunto)
        """
    )

    modo = st.radio(
        "Escolha o modo de análise:",
        ["Produto único", "Mix de produtos"],
        horizontal=True,
    )

    # -----------------------------------------------------
    # MODO 1 – PRODUTO ÚNICO
    # -----------------------------------------------------
    if modo == "Produto único":
        st.subheader("Modo: Produto único")

        st.sidebar.header("Configurações da Simulação – Produto único")

        preco = st.sidebar.number_input(
            "Preço de venda por unidade (R$)", 0.0, 10000.0, 100.0
        )
        gasto_var = st.sidebar.number_input(
            "Gasto variável por unidade (R$)", 0.0, 10000.0, 30.0
        )
        gastos_fixos = st.sidebar.number_input(
            "Gastos fixos totais (R$)", 0.0, 1000000.0, 25000.0
        )
        quantidade = st.sidebar.number_input(
            "Volume de vendas esperado (unidades)", 0, 1000000, 1000
        )

        st.sidebar.markdown("---")
        st.sidebar.write("Parâmetros para o gráfico:")
        q_min = st.sidebar.number_input("Volume mínimo (gráfico)", 0, 1000000, 0)
        q_max = st.sidebar.number_input("Volume máximo (gráfico)", 0, 1000000, 2000)
        q_step = st.sidebar.number_input("Incremento (gráfico)", 1, 1000000, 100)

        # ---------------- CÁLCULOS PRINCIPAIS ----------------
        mc_unit = preco - gasto_var
        mc_total = mc_unit * quantidade
        receita_total = preco * quantidade
        gasto_var_total = gasto_var * quantidade
        lucro = mc_total - gastos_fixos

        # Ponto de equilíbrio
        if mc_unit != 0:
            pe_unidades = gastos_fixos / mc_unit
            pe_receita = pe_unidades * preco
        else:
            pe_unidades = 0
            pe_receita = 0

        # Grau de alavancagem operacional (GAO)
        if mc_total - gastos_fixos != 0:
            gao = mc_total / (mc_total - gastos_fixos)
        else:
            gao = 0

        # Margem de segurança
        margem_seg_unid = quantidade - pe_unidades
        margem_seg_receita = receita_total - pe_receita
        if quantidade > 0:
            margem_seg_perc = (margem_seg_unid / quantidade) * 100
        else:
            margem_seg_perc = 0

        # ---------------- RESULTADOS ----------------
        st.header("Resultados da Simulação – Produto único")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Margem de Contribuição")
            st.write(f"Margem unitária: **R$ {mc_unit:,.2f}**")
            st.write(f"Margem total: **R$ {mc_total:,.2f}**")

        with col2:
            st.subheader("Ponto de Equilíbrio")

