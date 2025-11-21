import streamlit as st
import pandas as pd

# ---------------- CONFIGURAÇÃO DA PÁGINA ----------------
st.set_page_config(
    page_title="LABCOST – Simulador de Custos",
    layout="wide",
)

# ---------------- TABS PRINCIPAIS ----------------
tab_simulador, tab_classificacao = st.tabs(
    ["💻 Simulador de Custos", "📚 Classificação de Gastos"]
)

# =========================================================
# TAB 1 – SIMULADOR DE CUSTOS
# =========================================================
with tab_simulador:
    st.title("LABCOST – Simulador de Custos")

    st.write(
        """
        O **LABCOST** é uma ferramenta educacional que auxilia estudantes e gestores a compreenderem  
        **comportamento dos custos, margem de contribuição, ponto de equilíbrio e alavancagem operacional**.  
        Use os controles da barra lateral para simular diferentes cenários.
        """
    )

    # ----- BARRA LATERAL -----
    st.sidebar.header("Configurações da Simulação")

    preco = st.sidebar.number_input(
        "Preço de venda por unidade (R$)", 0.0, 10000.0, 100.0
    )
    custo_var = st.sidebar.number_input(
        "Custo variável por unidade (R$)", 0.0, 10000.0, 30.0
    )
    custos_fixos = st.sidebar.number_input(
        "Custos fixos totais (R$)", 0.0, 1000000.0, 25000.0
    )
    quantidade = st.sidebar.number_input(
        "Volume de vendas esperado (unidades)", 0, 1000000, 1000
    )

    st.sidebar.markdown("---")
    st.sidebar.write("Parâmetros para o gráfico:")

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

    with col1:
        st.subheader("Margem de Contribuição")
        st.write(f"Margem unitária: **R$ {mc_unit:,.2f}**")
        st.write(f"Margem total: **R$ {mc_total:,.2f}**")

    with col2:
        st.subheader("Ponto de Equilíbrio")
        st.write(f"Unidades: **{pe_unidades:,.0f}**")
        st.write(f"Receita necessária: **R$ {pe_receita:,.2f}**")

    st.subheader("Lucratividade")
    st.write(f"Receita total: **R$ {receita_total:,.2f}**")
    st.write(f"Custo variável total: **R$ {custo_var_total:,.2f}**")
    st.write(f"Lucro operacional: **R$ {lucro:,.2f}**")

    st.subheader("Grau de Alavancagem Operacional (GAO)")
    st.write(f"GAO: **{gao:,.2f}**")

    if gao > 0 and gao < 2:
        st.info("GAO baixo: o lucro é pouco sensível às variações no volume de vendas.")
    elif 2 <= gao < 5:
        st.warning("GAO moderado: há risco moderado e bom potencial de retorno.")
    elif gao >= 5:
        st.error(
            "GAO alto: o lucro é muito sensível às variações no volume de vendas."
        )
    else:
        st.write("GAO não definido para este cenário.")

    # ----- GRÁFICO -----
    if q_max > q_min:
        volumes = list(range(q_min, q_max + 1, q_step))
        df = pd.DataFrame(
            {
                "Volume": volumes,
                "Receita": [preco * q for q in volumes],
                "Custo Variável": [custo_var * q for q in volumes],
                "Lucro": [
                    (preco - custo_var) * q - custos_fixos for q in volumes
                ],
            }
        ).set_index("Volume")

        st.subheader("Comportamento do Lucro por Volume de Vendas")
        st.line_chart(df)

    st.caption("LABCOST – Uso educacional.")

# =========================================================
# TAB 2 – CLASSIFICAÇÃO DE GASTOS
# =========================================================
with tab_classificacao:
    st.title("Classificação de Gastos: Custos x Despesas")

    st.write(
        """
        Nesta atividade, o aluno deve **classificar os gastos** em:
        - **Custos** (relacionados à produção de bens/serviços);  
        - **Despesas** (administrativas, comerciais, financeiras etc.);  

        E, além disso, escolher a **categoria** correta, como:
        - Materiais Diretos  
        - Mão de Obra Direta (MOD)  
        - Custos Indiretos de Fabricação (CIF)  
        - Despesa Administrativa  
        - Despesa de Vendas  
        - Despesa Financeira  
        """
    )

    # Lista de itens para classificação
    itens = [
        {
            "descricao": "Salário da mão de obra diretamente envolvida na produção.",
            "tipo_correto": "Custo",
            "categoria_correta": "Mão de Obra Direta (MOD)",
        },
        {
            "descricao": "Matéria-prima utilizada na fabricação do produto.",
            "tipo_correto": "Custo",
            "categoria_correta": "Materiais Diretos",
        },
        {
            "descricao": "Aluguel do prédio da fábrica.",
            "tipo_correto": "Custo",
            "categoria_correta": "Custo Indireto de Fabricação (CIF)",
        },
        {
            "descricao": "Comissão dos vendedores sobre as vendas realizadas.",
            "tipo_correto": "Despesa",
            "categoria_correta": "Despesa de Vendas",
        },
        {
            "descricao": "Salário da equipe administrativa do escritório central.",
            "tipo_correto": "Despesa",
            "categoria_correta": "Despesa Administrativa",
        },
        {
            "descricao": "Juros pagos sobre empréstimos bancários.",
            "tipo_correto": "Despesa",
            "categoria_correta": "Despesa Financeira",
        },
        {
            "descricao": "Energia elétrica da fábrica (consumo das máquinas).",
            "tipo_correto": "Custo",
            "categoria_correta": "Custo Indireto de Fabricação (CIF)",
        },
        {
            "descricao": "Material de escritório utilizado no setor administrativo.",
            "tipo_correto": "Despesa",
            "categoria_correta": "Despesa Administrativa",
        },
        {
            "descricao": "Depreciação das máquinas utilizadas na produção.",
            "tipo_correto": "Custo",
            "categoria_correta": "Custo Indireto de Fabricação (CIF)",
        },
        {
            "descricao": "Gastos com propaganda e publicidade.",
            "tipo_correto": "Despesa",
            "categoria_correta": "Despesa de Vendas",
        },
    ]

    opcoes_tipo = ["Custo", "Despesa"]
    opcoes_categoria = [
        "Materiais Diretos",
        "Mão de Obra Direta (MOD)",
        "Custo Indireto de Fabricação (CIF)",
        "Despesa Administrativa",
        "Despesa de Vendas",
        "Despesa Financeira",
    ]

    st.subheader("Atividade")
    st.write("Para cada item abaixo, selecione **se é Custo ou Despesa** e a **categoria** correspondente.")

    respostas_tipo = []
    respostas_categoria = []

    for i, item in enumerate(itens):
        st.markdown(f"**Item {i+1}:** {item['descricao']}")
        col1, col2 = st.columns(2)

        with col1:
            tipo_escolhido = st.selectbox(
                "Custo ou Despesa?",
                opcoes_tipo,
                key=f"tipo_{i}",
            )
        with col2:
            categoria_escolhida = st.selectbox(
                "Categoria",
                opcoes_categoria,
                key=f"cat_{i}",
            )

        respostas_tipo.append(tipo_escolhido)
        respostas_categoria.append(categoria_escolhida)
        st.markdown("---")

    if st.button("Corrigir respostas"):
        resultados = []
        acertos = 0

        for i, item in enumerate(itens):
            tipo_ok = respostas_tipo[i] == item["tipo_correto"]
            cat_ok = respostas_categoria[i] == item["categoria_correta"]
            acertou = tipo_ok and cat_ok

            if acertou:
                acertos += 1

            resultados.append(
                {
                    "Item": i + 1,
                    "Descrição": item["descricao"],
                    "Tipo marcado": respostas_tipo[i],
                    "Tipo correto": item["tipo_correto"],
                    "Categoria marcada": respostas_categoria[i],
                    "Categoria correta": item["categoria_correta"],
                    "Acertou tudo?": "Sim" if acertou else "Não",
                }
            )

        df_result = pd.DataFrame(resultados)
        st.subheader("Resultado da Atividade")
        st.write(f"Você acertou **{acertos} de {len(itens)}** itens (tipo **e** categoria).")
        st.dataframe(df_result, use_container_width=True)

        st.info(
            "Sugestão didática: discuta com os alunos os itens que erraram, "
            "reforçando a diferença entre **custos de produção** e **despesas operacionais**."
        )
