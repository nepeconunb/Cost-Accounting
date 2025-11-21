import streamlit as st
import pandas as pd

# ----- CONFIGURAÇÃO DA PÁGINA -----
st.set_page_config(
    page_title="LABCOST – Simulador de Custos",
    layout="centered"
)

# ----- TÍTULO -----
st.title("LABCOST – Simulador de Custos")

st.write("""
O **LABCOST** é uma ferramenta educacional que auxilia estudantes e gestores a compreenderem  
**comportamento dos custos, margem de contribuição, ponto de equilíbrio e alavancagem operacional**.  
Use os controles da barra lateral para simular diferentes cenários.
""")

# ----- BARRA LATERAL -----
st.sidebar.header("Configurações da Simulação")

preco = st.sidebar.number_input("Preço de venda por unidade (R$)", 0.0, 10000.0, 100.0)
custo_var = st.sidebar.number_input("Custo variável por unidade (R$)", 0.0, 10000.0, 30.0)
custos_fixos = st.sidebar.number_input("Custos fixos totais (R$)", 0.0, 1000000.0, 25000.0)
quantidade = st.sidebar.number_input("Volume de vendas esperado (unidades)", 0, 1000000, 1000)

st.sidebar.markdown("---")

q_min = st.sidebar.number_input("Volume mínimo (gráfico)", 0, 1000000, 0)
q_max = st.sidebar.number_input("Volume máximo (gráfico)", 0, 1000000, 2000)
q_step = st.sidebar.number_input("Incremento (gráfico)", 1, 1000000, 100)

# ----- CÁLCULOS -----
mc_unit = preco - custo_var
mc_total = mc_unit * quantidade
receita_total = preco * quantidade
custo_var_total = custo_var * quantidade
lucro = mc_total - custos_fixos

if mc_unit != 0:
    pe_unidades = custos_fixos / mc_unit
    pe_receita = pe_unidades * preco
else:
    pe_unidades = 0
    pe_receita = 0

if mc_total - custos_fixos != 0:
    gao = mc_total / (mc_total - custos_fixos)
else:
    gao = 0

# ----- RESULTADOS -----
st.header("Resultados da Simulação")

col1, col2 = st.columns(2)

# MARGEM DE CONTRIBUIÇÃO
with col1:
    st.subheader("Margem de Contribuição")
    st.write(f"Margem unitária: **R$ {mc_unit:,.2f}**")
    st.write(f"Margem total: **R$ {mc_total:,.2f}**")

# PONTO DE EQUILÍBRIO
with col2:
    st.subheader("Ponto de Equilíbrio")
    st.write(f"Unidades: **{pe_unidades:,.0f}**")
    st.write(f"Receita necessária: **R$ {pe_receita:,.2f}**")

# LUCRATIVIDADE
st.subheader("Lucratividade")
st.write(f"Receita total: **R$ {receita_total:,.2f}**")
st.write(f"Custo variável total: **R$ {custo_var_total:,.2f}**")
st.write(f"Lucro operacional: **R$ {lucro:,.2f}**")

# GAO
st.subheader("Grau de Alavancagem Operacional (GAO)")
st.write(f"GAO: **{gao:,.2f}**")

if gao > 0 and gao < 2:
    st.info("GAO baixo: o lucro é pouco sensível às variações no volume de vendas.")
elif 2 <= gao < 5:
    st.warning("GAO moderado: há risco moderado e bom potencial de retorno.")
elif gao >= 5:
    st.error("GAO alto: o lucro é muito sensível às variações no volume de vendas.")
else:
    st.write("GAO não definido para este cenário.")

# ----- GRÁFICO -----
if q_max > q_min:
    volumes = list(range(q_min, q_max + 1, q_step))
    df = pd.DataFrame({
        "Volume": volumes,
        "Receita": [preco * q for q in volumes],
        "Custo Variável": [custo_var * q for q in volumes],
        "Lucro": [(preco - custo_var) * q - custos_fixos for q in volumes]
    }).set_index("Volume")

    st.subheader("Comportamento do Lucro por Volume de Vendas")
    st.line_chart(df)

st.caption("LABCOST – Uso educacional.")
