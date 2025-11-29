import streamlit as st
import pandas as pd
from pathlib import Path

# ---------------- CONFIGURAÇÃO DA PÁGINA ----------------
st.set_page_config(
    page_title="LABCOST – Simulador de Gastos e Custos",
    page_icon="📊",
    layout="wide",
)

# ---------------- TABS PRINCIPAIS ----------------
tab_home, tab_simulador, tab_classificacao = st.tabs(
    ["🏠 Página inicial", "💻 Simulador de Gastos e Custos", "📚 Classificação de Gastos"]
)

# =========================================================
# TAB 0 – PÁGINA INICIAL
# =========================================================
with tab_home:
    col_logo, col_texto = st.columns([1, 2])

    # ---- LOGO (opcional, sem aviso chato) ----
    with col_logo:
        logo_path = Path("labcost_logo.svg")
        if logo_path.exists():
            st.image(str(logo_path), width=220)
        else:
            st.empty()
        st.caption("LABCOST – Laboratório de Simulação de Gastos e Custos")

    # ---- TEXTO PRINCIPAL COM DISCIPLINA / NEPECON ----
    with col_texto:
        st.title("Bem-vindo ao LABCOST")
        st.markdown(
            """
            **LABCOST – Laboratório de Simulação de Gastos e Custos**  

            Este simulador é utilizado na disciplina de **Contabilidade de Custos e Gestão**,
            ministrada pela Profª **Fátima de Souza Freire** na **Universidade de Brasília (UnB)**,
            como parte das iniciativas do **NEPECON – Núcleo de Estudos e Pesquisas em Sustentabilidade
            Econômica e Socioambiental**.

            O **LABCOST** é um laboratório virtual para apoiar o ensino de **Contabilidade de Custos e Gestão**, com foco em:

            - Comportamento dos **gastos fixos e variáveis**  
            - **Margem de contribuição** unitária e total  
            - **Ponto de equilíbrio** em unidades e em receita  
            - **Margem de segurança**  
            - **Grau de Alavancagem Operacional (GAO)**  
            - Análise de **mix de produtos**  

            A ferramenta foi pensada para uso em disciplinas de graduação e pós-graduação, 
            atividades de laboratório, estudos dirigidos e educação a distância.
            """
        )

    st.markdown("---")

    st.subheader("Como usar o LABCOST")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            """
            ### 🧮 Simulador de Gastos e Custos  
            Na aba **“💻 Simulador de Gastos e Custos”**, você poderá:

            - Simular **produto único** com:
              - Receita total  
              - Gastos variáveis e fixos  
              - **DRE simplificada**  
              - Margem de contribuição  
              - Margem de segurança  
              - GAO  
              - Gráficos de valores **totais e unitários**  

            - Simular **mix de produtos** com:
              - Margem de contribuição por produto  
              - Mix de vendas  
              - Ponto de equilíbrio do mix  
              - Lucro operacional consolidado  
            """
        )

    with col2:
        st.markdown(
            """
            ### 📚 Classificação de Gastos  
            Na aba **“📚 Classificação de Gastos”**, os alunos podem:

            - Classificar itens em **Custo** ou **Despesa**  
            - Detalhar:
              - Custo Direto / Indireto  
              - Custo Fixo / Variável  
              - Despesa Fixa / Variável  
              - Despesa Administrativa / com Vendas / Financeira  

            Ao final, o sistema mostra:
            - Quantos itens acertou no **tipo**  
            - Quantos acertou na **classificação detalhada**  
            """
        )

    st.markdown("---")

    st.subheader("Sugestão de uso didático")
    st.markdown(
        """
        - Proponha **cenários diferentes** (ex.: aumento de preço, redução de gastos fixos, 
          mudanças no mix de produtos) e peça para os alunos analisarem o impacto no **ponto de equilíbrio** e no **lucro**.  
        - Use o LABCOST em **aulas práticas de laboratório** ou em **atividades remotas**.  
        - Combine com leituras sobre **margem de contribuição**, **decisão de mix de produtos** e **GAO**.  
        """
    )

    st.info(
        "O LABCOST é uma ferramenta educacional desenvolvida no âmbito do NEPECON/UnB "
        "para apoiar o ensino de Contabilidade de Custos e Gestão."
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

        # GAO
        if mc_total - gastos_fixos != 0:
            gao = mc_total / (mc_total - gastos_fixos)
        else:
            gao = 0

        # Margem de Segurança
        margem_seg_unid = quantidade - pe_unidades
        margem_seg_receita = receita_total - pe_receita
        if quantidade > 0:
            margem_seg_perc = (margem_seg_unid / quantidade) * 100
        else:
            margem_seg_perc = 0

        # Gastos Unitários
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

        # DRE
        st.subheader("Demonstração do Resultado do Exercício (DRE)")
        st.markdown(
            f"""
        **Receita Total:** R$ {receita_total:,.2f}  
        **(-) Gastos Variáveis Totais:** R$ {gasto_var_total:,.2f}  
        **= Margem de Contribuição Total:** R$ {mc_total:,.2f}  

        **(-) Gastos Fixos Totais:** R$ {gastos_fixos:,.2f}  

        **= Lucro/Prejuízo Operacional:**  
        <span style='font-size:22px; font-weight:bold; color:{'green' if lucro>=0 else 'red'}'>
        R$ {lucro:,.2f}
        </span>
        """,
            unsafe_allow_html=True,
        )

        st.subheader("Gastos Unitários")
        st.write(f"Gasto variável unitário: **R$ {gasto_variavel_unitario:,.2f}**")
        st.write(f"Gasto fixo unitário: **R$ {gasto_fixo_unitario:,.2f}**")
        st.write(f"Gasto unitário total: **R$ {gasto_unitario_total:,.2f}**")

        st.subheader("Margem de Segurança")
        st.write(f"Em unidades: **{margem_seg_unid:,.0f}**")
        st.write(f"Em receita: **R$ {margem_seg_receita:,.2f}**")
        st.write(
            f"Em percentual sobre o volume esperado: **{margem_seg_perc:,.1f}%**"
        )

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

        # ---------------- GRÁFICO ----------------
        if q_max > q_min and q_step > 0:
            volumes = list(range(q_min, q_max + 1, q_step))

            df = pd.DataFrame(
                {
                    "Volume": volumes,
                    "Receita Total": [preco * q for q in volumes],
                    "Gasto Variável Total": [gasto_var * q for q in volumes],
                    "Gasto Fixo Total": [gastos_fixos for _ in volumes],
                    "Lucro": [
                        (preco - gasto_var) * q - gastos_fixos for q in volumes
                    ],
                    "GV Unitário": [gasto_variavel_unitario for _ in volumes],
                    "GF Unitário": [
                        (gastos_fixos / q) if q > 0 else None for q in volumes
                    ],
                    "Gasto Unitário Total": [
                        gasto_variavel_unitario + ((gastos_fixos / q) if q > 0 else 0)
                        for q in volumes
                    ],
                }
            ).set_index("Volume")

            st.subheader("Comportamento dos Resultados – Totais e Unitários")
            st.line_chart(df)

        st.caption("LABCOST – Uso educacional. Modo: Produto único.")

    # -----------------------------------------------------
    # MODO 2 – MIX DE PRODUTOS
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

        # ATÉ 10 PRODUTOS NO MIX
        num_produtos = st.sidebar.slider(
            "Número de produtos no mix", min_value=2, max_value=10, value=3
        )

        st.write(
            """
            Preencha as informações de cada produto abaixo.  
            O sistema irá calcular:
            - Margem de contribuição unitária de cada produto;  
            - Mix de vendas (% em unidades);  
            - Margem de contribuição ponderada do mix;  
            - **Ponto de equilíbrio do mix** (unidades totais e por produto);  
            - Resultado total (receita, gasto variável total, margem de contribuição e lucro).
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
                    f"Preço venda {i+1} (R$)",
                    0.0,
                    100000.0,
                    100.0 + 10 * i,
                    key=f"preco_{i}",
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

            produtos.append(
                {
                    "Nome": nome,
                    "Preco": preco_i,
                    "GV": gv_i,
                    "Q": q_i,
                }
            )

        # Somatório de volumes para cálculo do mix
        soma_q = sum(p["Q"] for p in produtos)

        if soma_q == 0:
            st.warning("Informe volumes de vendas maiores que zero para calcular o mix.")
        else:
            linhas = []
            mc_mix_ponderada = 0

            receita_total = 0
            gv_total = 0
            mc_total = 0

            for p in produtos:
                mc_unit_i = p["Preco"] - p["GV"]
                receita_i = p["Preco"] * p["Q"]
                gv_i_total = p["GV"] * p["Q"]
                mc_i_total = mc_unit_i * p["Q"]
                mix_i = p["Q"] / soma_q  # proporção em unidades

                receita_total += receita_i
                gv_total += gv_i_total
                mc_total += mc_i_total

                # MC unitária ponderada pelo mix (em unidades)
                mc_mix_ponderada += mc_unit_i * mix_i

                linhas.append(
                    {
                        "Produto": p["Nome"],
                        "Preço (R$)": p["Preco"],
                        "Gasto Var. unit. (R$)": p["GV"],
                        "MC unit. (R$)": mc_unit_i,
                        "Volume esperado": p["Q"],
                        "Mix (%)": mix_i * 100,
                        "Receita (R$)": receita_i,
                        "Gasto Var. Total (R$)": gv_i_total,
                        "MC Total (R$)": mc_i_total,
                    }
                )

            # ----------------- PONTO DE EQUILÍBRIO DO MIX -----------------
            if mc_mix_ponderada > 0:
                # PE em unidades totais do mix
                pe_mix_unidades = gastos_fixos_mix / mc_mix_ponderada
            else:
                pe_mix_unidades = 0

            # PE de cada produto (em unidades), mantendo o mix
            for linha in linhas:
                mix_frac = linha["Mix (%)"] / 100
                linha["PE (unid.) no mix"] = pe_mix_unidades * mix_frac

            # PE em receita total do mix
            pe_mix_receita = sum(
                linha["PE (unid.) no mix"] * linha["Preço (R$)"] for linha in linhas
            )

            lucro_total = mc_total - gastos_fixos_mix

            df_mix = pd.DataFrame(linhas)

            st.subheader("Resumo por produto")
            st.dataframe(
                df_mix.style.format(
                    {
                        "Preço (R$)": "R$ {:,.2f}",
                        "Gasto Var. unit. (R$)": "R$ {:,.2f}",

