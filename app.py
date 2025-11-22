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

        # ---------------- PE ----------------
        pe_unidades = gastos_fixos / mc_unit if mc_unit != 0 else 0
        pe_receita = pe_unidades * preco if mc_unit != 0 else 0

        # ---------------- GAO ----------------
        gao = mc_total / (mc_total - gastos_fixos) if (mc_total - gastos_fixos) != 0 else 0

        # ---------------- MARGEM DE SEGURANÇA ----------------
        margem_seg_unid = quantidade - pe_unidades
        margem_seg_receita = receita_total - pe_receita
        margem_seg_perc = (margem_seg_unid / quantidade) * 100 if quantidade > 0 else 0

        # ---------------- GASTOS UNITÁRIOS ----------------
        gasto_variavel_unitario = gasto_var
        gasto_fixo_unitario = gastos_fixos / quantidade if quantidade > 0 else 0
        gasto_unitario_total = gasto_variavel_unitario + gasto_fixo_unitario

        # ---------------- RESULTADOS ----------------
        st.header("Resultados da Simulação – Produto único")

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Margem de Contribuição")
            st.write(f"Margem unitária: **R$ {mc_unit:,.2f}**")
            st.write(f"Margem total: **R$ {mc_total:,.2f}**")
        with col2:
            st.subheader("Ponto de Equilíbrio")
            st.write(f"Unidades: **{pe_unidades:,.0f}**")
            st.write(f"Receita necessária: **R$ {pe_receita:,.2f}**")

        # ---------------- DRE ----------------
        st.subheader("Demonstração do Resultado do Exercício (DRE)")
        st.markdown(
            f"""
        **Receita Total:** R$ {receita_total:,.2f}  
        **(-) Gastos Variáveis Totais:** R$ {gasto_var_total:,.2f}  
        **= Margem de Contribuição:** R$ {mc_total:,.2f}  

        **(-) Gastos Fixos Totais:** R$ {gastos_fixos:,.2f}  

        **= Lucro/Prejuízo:**  
        <span style='font-size:22px; font-weight:bold; color:{'green' if lucro>=0 else 'red'}'>
        R$ {lucro:,.2f}
        </span>
        """,
            unsafe_allow_html=True,
        )

        # ---------------- GASTOS UNITÁRIOS ----------------
        st.subheader("Gastos Unitários")
        st.write(f"Gasto variável unitário: **R$ {gasto_variavel_unitario:,.2f}**")
        st.write(f"Gasto fixo unitário: **R$ {gasto_fixo_unitario:,.2f}**")
        st.write(f"Gasto unitário total: **R$ {gasto_unitario_total:,.2f}**")

        # ---------------- MARGEM SEGURANÇA ----------------
        st.subheader("Margem de Segurança")
        st.write(f"Unidades: **{margem_seg_unid:,.0f}**")
        st.write(f"Receita: **R$ {margem_seg_receita:,.2f}**")
        st.write(f"Percentual: **{margem_seg_perc:,.1f}%**")

        # ---------------- GAO ----------------
        st.subheader("Grau de Alavancagem Operacional (GAO)")
        st.write(f"GAO: **{gao:,.2f}**")

        # ---------------- GRÁFICO ----------------
        if q_max > q_min and q_step > 0:
            volumes = list(range(q_min, q_max + 1, q_step))

            df = pd.DataFrame(
                {
                    "Volume": volumes,
                    "Receita Total": [preco * q for q in volumes],
                    "Gasto Variável Total": [gasto_var * q for q in volumes],
                    "Gasto Fixo Total": [gastos_fixos for _ in volumes],
                    "Lucro": [(preco - gasto_var) * q - gastos_fixos for q in volumes],
                    "GV Unitário": [gasto_variavel_unitario for _ in volumes],
                    "GF Unitário": [gastos_fixos / q if q > 0 else None for q in volumes],
                    "Gasto Unitário Total": [
                        gasto_variavel_unitario + (gastos_fixos / q if q > 0 else 0)
                        for q in volumes
                    ],
                }
            ).set_index("Volume")

            st.subheader("Gráfico – Totais e Unitários")
            st.line_chart(df)

        st.caption("LABCOST – Produto único")

    # -----------------------------------------------------
    # MODO 2 – MIX DE PRODUTOS (SEM ALTERAÇÕES)
    # -----------------------------------------------------
    else:
        st.subheader("Modo: Mix de produtos")

        st.sidebar.header("Configurações da Simulação – Mix de produtos")

        gastos_fixos_mix = st.sidebar.number_input(
            "Gastos fixos totais (R$) – comuns a todos os produtos",
            0.0,
            1000000.0,
            50000.0,
        )

        num_produtos = st.sidebar.slider(
            "Número de produtos no mix", min_value=2, max_value=5, value=3
        )

        st.write(
            """
            Preencha as informações de cada produto abaixo e o sistema calculará:
            - Margem de contribuição unitária
            - Mix de vendas
            - Margem de contribuição ponderada
            - Ponto de equilíbrio do mix
            - Lucro operacional
            """
        )

        produtos = []
        for i in range(num_produtos):
            st.markdown(f"### Produto {i+1}")
            col1, col2, col3, col4 = st.columns([2, 1.2, 1.2, 1.2])

            with col1:
                nome = st.text_input(
                    f"Nome do Produto {i+1}",
                    value=f"Produto {i+1}",
                    key=f"nome_{i}",
                )
            with col2:
                preco_i = st.number_input(
                    f"Preço venda {i+1} (R$)", 0.0, 100000.0, 100.0 + 10 * i, key=f"preco_{i}"
                )
            with col3:
                gv_i = st.number_input(
                    f"Gasto variável {i+1} (R$)",
                    0.0,
                    100000.0,
                    40.0 + 5 * i,
                    key=f"gv_{i}",
                )
            with col4:
                q_i = st.number_input(
                    f"Volume esperado {i+1} (unid.)",
                    0,
                    1000000,
                    1000,
                    key=f"q_{i}",
                )

            produtos.append({"Nome": nome, "Preco": preco_i, "GV": gv_i, "Q": q_i})

        soma_q = sum(p["Q"] for p in produtos)

        if soma_q == 0:
            st.warning("Informe volumes maiores que zero.")
        else:
            linhas = []
            mc_mix_ponderada = 0
            receita_total = gv_total = mc_total = 0

            for p in produtos:
                mc_unit = p["Preco"] - p["GV"]
                receita = p["Preco"] * p["Q"]
                gv_total_i = p["GV"] * p["Q"]
                mc_total_i = mc_unit * p["Q"]
                mix_i = p["Q"] / soma_q

                receita_total += receita
                gv_total += gv_total_i
                mc_total += mc_total_i

                mc_mix_ponderada += mc_unit * mix_i

                linhas.append(
                    {
                        "Produto": p["Nome"],
                        "Preço (R$)": p["Preco"],
                        "Gasto Var. Unit. (R$)": p["GV"],
                        "MC Unit. (R$)": mc_unit,
                        "Volume": p["Q"],
                        "Mix (%)": mix_i * 100,
                        "Receita (R$)": receita,
                        "GV Total (R$)": gv_total_i,
                        "MC Total (R$)": mc_total_i,
                    }
                )

            pe_mix = gastos_fixos_mix / mc_mix_ponderada if mc_mix_ponderada > 0 else 0

            for linha in linhas:
                linha["PE (unid.) no mix"] = pe_mix * (linha["Mix (%)"] / 100)

            lucro_total = mc_total - gastos_fixos_mix

            df_mix = pd.DataFrame(linhas)

            st.subheader("Resumo por Produto")
            st.dataframe(df_mix, use_container_width=True)

            st.subheader("Indicadores")
            st.write(f"Receita Total: **R$ {receita_total:,.2f}**")
            st.write(f"Gasto Variável Total: **R$ {gv_total:,.2f}**")
            st.write(f"Margem de Contribuição Total: **R$ {mc_total:,.2f}**")
            st.write(f"Gastos Fixos: **R$ {gastos_fixos_mix:,.2f}**")
            st.write(f"Lucro Operacional: **R$ {lucro_total:,.2f}**")

            st.caption("LABCOST – Mix de produtos")

# =========================================================
# TAB 2 – CLASSIFICAÇÃO DE GASTOS
# =========================================================
with tab_classificacao:
    st.title("Classificação de Gastos: Custos x Despesas")

    st.write(
        """
        Nesta atividade, o aluno deve classificar os itens em:
        **Custo**, **Despesa** e a classificação detalhada
        (fixo, variável, direto, indireto, etc.).
        """
    )

    itens = [
        {"descricao": "Salário da mão de obra direta.", "tipo_correto": "Custo", "classificacao_correta": "Custo Direto"},
        {"descricao": "Matéria-prima utilizada.", "tipo_correto": "Custo", "classificacao_correta": "Custo Direto"},
        {"descricao": "Aluguel da fábrica.", "tipo_correto": "Custo", "classificacao_correta": "Custo Fixo"},
        {"descricao": "Energia das máquinas (variável).", "tipo_correto": "Custo", "classificacao_correta": "Custo Variável"},
        {"descricao": "Depreciação das máquinas.", "tipo_correto": "Custo", "classificacao_correta": "Custo Indireto"},
        {"descricao": "Comissão dos vendedores.", "tipo_correto": "Despesa", "classificacao_correta": "Despesa Variável"},
        {"descricao": "Salário fixo da equipe de vendas.", "tipo_correto": "Despesa", "classificacao_correta": "Despesa com Vendas"},
        {"descricao": "Salário administrativo.", "tipo_correto": "Despesa", "classificacao_correta": "Despesa Administrativa"},
        {"descricao": "Propaganda e publicidade.", "tipo_correto": "Despesa", "classificacao_correta": "Despesa com Vendas"},
        {"descricao": "Juros bancários.", "tipo_correto": "Despesa", "classificacao_correta": "Despesa Financeira"},
        {"descricao": "Seguro da fábrica.", "tipo_correto": "Custo", "classificacao_correta": "Custo Fixo"},
        {"descricao": "Telefone do escritório.", "tipo_correto": "Despesa", "classificacao_correta": "Despesa Administrativa"},
    ]

    opcoes_tipo = ["Custo", "Despesa"]
    opcoes_classificacao = [
        "Custo Direto", "Custo Indireto", "Custo Fixo", "Custo Variável",
        "Despesa Fixa", "Despesa Variável", "Despesa Administrativa",
        "Despesa com Vendas", "Despesa Financeira",
    ]

    respostas_tipo = []
    respostas_class = []

    for i, item in enumerate(itens):
        st.markdown(f"**Item {i+1}:** {item['descricao']}")
        col1, col2 = st.columns(2)
        with col1:
            respostas_tipo.append(
                st.selectbox("Custo ou Despesa?", opcoes_tipo, key=f"tipo_{i}")
            )
        with col2:
            respostas_class.append(
                st.selectbox("Classificação detalhada", opcoes_classificacao, key=f"class_{i}")
            )
        st.markdown("---")

    if st.button("Corrigir"):
        resultados = []
        ac_tipo = ac_class = ac_total = 0

        for i, item in enumerate(itens):
            tipo_ok = respostas_tipo[i] == item["tipo_correto"]
            class_ok = respostas_class[i] == item["classificacao_correta"]
            total_ok = tipo_ok and class_ok

            if tipo_ok: ac_tipo += 1
            if class_ok: ac_class += 1
            if total_ok: ac_total += 1

            resultados.append(
                {
                    "Item": i+1,
                    "Descrição": item["descricao"],
                    "Tipo marcado": respostas_tipo[i],
                    "Tipo correto": item["tipo_correto"],
                    "Classificação marcada": respostas_class[i],
                    "Classificação correta": item["classificacao_correta"],
                    "Acertou tudo?": "Sim" if total_ok else "Não",
                }
            )

        st.subheader("Resultado")
        st.write(f"Acertos de tipo: **{ac_tipo} / {len(itens)}**")
        st.write(f"Acertos de classificação: **{ac_class} / {len(itens)}**")
        st.write(f"Acertos completos: **{ac_total} / {len(itens)}**")

        st.dataframe(pd.DataFrame(resultados), use_container_width=True)
