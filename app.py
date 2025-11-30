import streamlit as st
import pandas as pd
from pathlib import Path
import altair as alt

# --------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# --------------------------------------------------------
st.set_page_config(
    page_title="LABCOST – Simulador de Gastos e Custos",
    page_icon="📊",
    layout="wide",
)

# Contador simples de acessos na sessão
if "visit_count" not in st.session_state:
    st.session_state["visit_count"] = 0
st.session_state["visit_count"] += 1

# ========================================================
# FUNÇÕES AUXILIARES – INVENTÁRIO
# ========================================================
def calcula_inventario_linha(ei_qtd, ei_ctu, prod_qtd, prod_ctu, vend_qtd, metodo):
    """
    Calcula CMV e Estoque Final de UMA linha (um produto em um mês),
    para os métodos:
    - PEPS (FIFO)
    - UEPS (LIFO)
    - Média ponderada
    """

    # Camadas de estoque: estoque inicial + produção do período
    layers = []
    if ei_qtd > 0:
        layers.append({"q": float(ei_qtd), "ctu": float(ei_ctu)})
    if prod_qtd > 0:
        layers.append({"q": float(prod_qtd), "ctu": float(prod_ctu)})

    total_disp_q = sum(l["q"] for l in layers)

    # Se não há estoque nem produção, tudo zero
    if total_disp_q <= 0:
        return 0.0, 0.0, 0.0, 0.0

    vend_qtd = float(vend_qtd)
    vend_qtd_eff = min(vend_qtd, total_disp_q)  # evita vender mais do que existe

    metodo = metodo.lower()

    # ---------------- MÉDIA PONDERADA ----------------
    if metodo.startswith("média"):
        total_cost = sum(l["q"] * l["ctu"] for l in layers)
        ctu_medio = total_cost / total_disp_q if total_disp_q > 0 else 0.0
        cmv = vend_qtd_eff * ctu_medio
        estoque_final_q = total_disp_q - vend_qtd_eff
        estoque_final_v = estoque_final_q * ctu_medio
        return ctu_medio, cmv, estoque_final_q, estoque_final_v

    # ---------------- PEPS / UEPS ----------------
    if metodo.startswith("peps"):
        iter_layers = layers                  # mais antigo primeiro
    elif metodo.startswith("ueps"):
        iter_layers = list(reversed(layers))  # mais recente primeiro
    else:
        raise ValueError("Método desconhecido")

    cmv = 0.0
    remaining = vend_qtd_eff

    for layer in iter_layers:
        if remaining <= 0:
            break
        use_q = min(layer["q"], remaining)
        cmv += use_q * layer["ctu"]
        layer["q"] -= use_q
        remaining -= use_q

    # Após a venda, recompor as camadas na ordem original (EI + Produção)
    if metodo.startswith("peps"):
        final_layers = iter_layers
    else:  # UEPS -> iter_layers está invertida, então reverte de volta
        final_layers = list(reversed(iter_layers))

    estoque_final_q = sum(l["q"] for l in final_layers)
    estoque_final_v = sum(l["q"] * l["ctu"] for l in final_layers)

    # Custo unitário médio do estoque final (apenas para exibir)
    ctu_medio_estoque = (
        estoque_final_v / estoque_final_q if estoque_final_q > 0 else 0.0
    )

    return ctu_medio_estoque, cmv, estoque_final_q, estoque_final_v


def inventario_produtos():
    st.header("📚 Livro de Inventário – PEPS, UEPS e Média Ponderada")

    st.markdown(
        """
        Este módulo replica um **Livro de Inventário por mês e por produto**.

        Você pode escolher o método de custeio:

        - **PEPS (FIFO)**  
        - **UEPS (LIFO)**  
        - **Média ponderada**

        Para cada **mês** e **produto**, informe:
        - Estoque inicial (Quantidade e CTu)  
        - Produção do período (Quantidade e CTu)  
        - Quantidade vendida no mês  
        - Preço de venda (apenas informativo)  
        """
    )

    metodo = st.radio(
        "Escolha o método para cálculo do CMV e do estoque final:",
        ["PEPS (FIFO)", "UEPS (LIFO)", "Média ponderada"],
        horizontal=True,
    )

    st.markdown("#### Parâmetros para Demonstração de Resultado (iguais para todos os meses)")
    colp1, colp2, colp3 = st.columns(3)
    with colp1:
        perc_desp_var = st.number_input(
            "Despesas variáveis (% da receita)",
            min_value=0.0,
            max_value=100.0,
            value=10.0,
            step=0.5,
            format="%.2f",
        )
    with colp2:
        gastos_fixos_op = st.number_input(
            "Gastos fixos operacionais (R$/mês)",
            min_value=0.0,
            value=5000.0,
            step=500.0,
            format="%.2f",
        )
    with colp3:
        custo_fixo_fab = st.number_input(
            "Custos fixos de fabricação (R$/mês)",
            min_value=0.0,
            value=0.0,
            step=500.0,
            format="%.2f",
        )

    # Quantidade de meses e produtos
    n_meses = st.number_input(
        "Quantidade de meses para simular:",
        min_value=1,
        max_value=12,
        value=3,
        step=1,
    )

    n_produtos = st.number_input(
        "Quantidade de produtos (até 10):",
        min_value=1,
        max_value=10,
        value=3,
        step=1,
    )

    # Nomes padrão: Produto 1, Produto 2, ...
    default_products = [f"Produto {i+1}" for i in range(int(n_produtos))]
    st.markdown("Você pode editar os nomes dos produtos na tabela de cada mês.")

    resultados_meses = []
    series_vendas = []  # para o gráfico de evolução de vendas

    for mes in range(1, int(n_meses) + 1):
        st.markdown(f"### 📆 Mês {mes}")
        st.markdown("Preencha os dados do mês:")

        dados = {
            "Produto": default_products,
            "Estoque inicial (Qtd)": [0.0] * int(n_produtos),
            "Estoque inicial (CTu)": [0.0] * int(n_produtos),
            "Produção do período (Qtd)": [0.0] * int(n_produtos),
            "Produção do período (CTu)": [0.0] * int(n_produtos),
            "Quantidade vendida (unid.)": [0.0] * int(n_produtos),
            "Preço de venda (R$)": [0.0] * int(n_produtos),
        }

        df_mes = pd.DataFrame(dados)

        df_editado = st.data_editor(
            df_mes,
            num_rows="fixed",
            use_container_width=True,
            key=f"mes_{mes}",
        )

        # ---- Cálculo por produto naquele mês ----
        linhas_resultado = []
        for _, row in df_editado.iterrows():
            disp_q = row["Estoque inicial (Qtd)"] + row["Produção do período (Qtd)"]

            ctu_base, cmv, estoque_q, estoque_v = calcula_inventario_linha(
                row["Estoque inicial (Qtd)"],
                row["Estoque inicial (CTu)"],
                row["Produção do período (Qtd)"],
                row["Produção do período (CTu)"],
                row["Quantidade vendida (unid.)"],
                metodo,
            )

            receita = row["Quantidade vendida (unid.)"] * row["Preço de venda (R$)"]

            linhas_resultado.append(
                {
                    "Produto": row["Produto"],
                    "Estoque inicial (Qtd)": row["Estoque inicial (Qtd)"],
                    "Estoque inicial (CTu)": row["Estoque inicial (CTu)"],
                    "Produção (Qtd)": row["Produção do período (Qtd)"],
                    "Produção (CTu)": row["Produção do período (CTu)"],
                    "Produção acumulada (unid.)": disp_q,
                    "Quantidade vendida (unid.)": row["Quantidade vendida (unid.)"],
                    "Estoque final (Qtd)": estoque_q,
                    "Preço de venda (R$)": row["Preço de venda (R$)"],
                    "CTu utilizado (método)": ctu_base if metodo.lower().startswith("média") else None,
                    "CMV (R$)": cmv,
                    "Estoque final (R$)": estoque_v,
                    "Receita (R$)": receita,
                }
            )

            # Guarda série de vendas para o gráfico
            series_vendas.append(
                {
                    "Mês": mes,
                    "Produto": row["Produto"],
                    "Quantidade vendida": row["Quantidade vendida (unid.)"],
                }
            )

        df_res = pd.DataFrame(linhas_resultado)
        resultados_meses.append((mes, df_res))

        # Garante que colunas monetárias sejam numéricas (evita erro no Styler)
        cols_monetarias = [
            "Estoque inicial (CTu)",
            "Produção (CTu)",
            "Preço de venda (R$)",
            "CTu utilizado (método)",
            "CMV (R$)",
            "Estoque final (R$)",
            "Receita (R$)",
        ]
        for c in cols_monetarias:
            if c in df_res.columns:
                df_res[c] = pd.to_numeric(df_res[c], errors="coerce")

        st.markdown(f"#### ✅ Resultado – Mês {mes}")
        st.dataframe(
            df_res.style.format(
                {
                    "Estoque inicial (CTu)": "R$ {:,.2f}",
                    "Produção (CTu)": "R$ {:,.2f}",
                    "Preço de venda (R$)": "R$ {:,.2f}",
                    "CTu utilizado (método)": "R$ {:,.2f}",
                    "CMV (R$)": "R$ {:,.2f}",
                    "Estoque final (R$)": "R$ {:,.2f}",
                    "Receita (R$)": "R$ {:,.2f}",
                }
            ),
            use_container_width=True,
        )

        total_cmv = float(df_res["CMV (R$)"].sum())
        total_estoque = float(df_res["Estoque final (R$)"].sum())
        total_receita = float(df_res["Receita (R$)"].sum())
        desp_var = total_receita * perc_desp_var / 100.0

        # --------- DRE POR ABSORÇÃO ---------
        lucro_bruto_abs = total_receita - total_cmv
        lucro_oper_abs = lucro_bruto_abs - desp_var - gastos_fixos_op

        # --------- DRE POR CUSTEIO VARIÁVEL ---------
        cmv_var = max(total_cmv - custo_fixo_fab, 0.0)
        custo_fixo_total = gastos_fixos_op + custo_fixo_fab
        margem_contrib = total_receita - cmv_var - desp_var
        lucro_oper_var = margem_contrib - custo_fixo_total

        st.markdown("#### 📑 Demonstração de Resultado – Comparativo de Métodos")
        col_dre1, col_dre2 = st.columns(2)

        with col_dre1:
            st.markdown("##### Custeio por Absorção")
            st.markdown(
                f"""
                **Receita líquida:** R$ {total_receita:,.2f}  
                **(-) CMV (inclui custos fixos de fabricação):** R$ {total_cmv:,.2f}  
                **= Lucro bruto:** R$ {lucro_bruto_abs:,.2f}  

                **(-) Despesas variáveis:** R$ {desp_var:,.2f}  
                **(-) Gastos fixos operacionais:** R$ {gastos_fixos_op:,.2f}  

                **= Lucro operacional:**  
                **R$ {lucro_oper_abs:,.2f}**
                """
            )

        with col_dre2:
            st.markdown("##### Custeio Variável")
            st.markdown(
                f"""
                **Receita líquida:** R$ {total_receita:,.2f}  
                **(-) Custos variáveis das vendas (CMV - CF fab):** R$ {cmv_var:,.2f}  
                **= Margem de contribuição:** R$ {total_receita - cmv_var:,.2f}  

                **(-) Despesas variáveis:** R$ {desp_var:,.2f}  
                **= Margem de contribuição após despesas variáveis:**  
                R$ {margem_contrib:,.2f}  

                **(-) Custos fixos (fab + operac.):** R$ {custo_fixo_total:,.2f}  

                **= Lucro operacional:**  
                **R$ {lucro_oper_var:,.2f}**
                """
            )

        st.markdown("#### 📌 Totais do período (estoques e CMV)")
        col1, col2 = st.columns(2)
        with col1:
            st.metric(f"CMV total – Mês {mes}", f"R$ {total_cmv:,.2f}")
        with col2:
            st.metric(f"Estoque final total – Mês {mes}", f"R$ {total_estoque:,.2f}")

        st.markdown("---")

    # Visão consolidada dos meses (igual um resumo da planilha)
    if len(resultados_meses) > 1:
        st.markdown("### 📊 Visão consolidada – Totais por mês")
        consol = []
        for mes, df_res in resultados_meses:
            consol.append(
                {
                    "Mês": mes,
                    "CMV total (R$)": float(df_res["CMV (R$)"].sum()),
                    "Estoque final total (R$)": float(df_res["Estoque final (R$)"].sum()),
                    "Receita total (R$)": float(df_res["Receita (R$)"].sum()),
                }
            )
        df_consol = pd.DataFrame(consol)
        for c in ["CMV total (R$)", "Estoque final total (R$)", "Receita total (R$)"]:
            df_consol[c] = pd.to_numeric(df_consol[c], errors="coerce")

        st.dataframe(
            df_consol.style.format(
                {
                    "CMV total (R$)": "R$ {:,.2f}",
                    "Estoque final total (R$)": "R$ {:,.2f}",
                    "Receita total (R$)": "R$ {:,.2f}",
                }
            ),
            use_container_width=True,
        )

    # Gráfico de evolução das vendas por produto
    if series_vendas:
        st.markdown("### 📈 Evolução das vendas por produto")
        df_vendas = pd.DataFrame(series_vendas)
        df_vendas["Mês"] = pd.to_numeric(df_vendas["Mês"], errors="coerce")

        chart = (
            alt.Chart(df_vendas)
            .mark_line(point=True)
            .encode(
                x=alt.X("Mês:Q", title="Mês"),
                y=alt.Y("Quantidade vendida:Q", title="Quantidade vendida"),
                color="Produto:N",
                tooltip=["Mês", "Produto", "Quantidade vendida"],
            )
            .properties(height=400)
        )
        st.altair_chart(chart, use_container_width=True)


# ========================================================
# TABS PRINCIPAIS
# ========================================================
tab_home, tab_classificacao, tab_inventario, tab_simulador, tab_markup, tab_avaliacao = st.tabs(
    [
        "🏠 Página inicial",
        "📚 Classificação de Gastos",
        "📦 Livro de Inventário",
        "💻 Simulador de Gastos e Custos",
        "🧾 Mark-up de Preço",
        "⭐ Avaliação do LABCOST",
    ]
)

# ========================================================
# TAB 0 – PÁGINA INICIAL
# ========================================================
with tab_home:
    col_logo, col_texto = st.columns([1, 2])

    # Logo (opcional)
    with col_logo:
        logo_path = Path("labcost_logo.svg")
        if logo_path.exists():
            st.image(str(logo_path), width=220)
        st.caption("LABCOST – Laboratório de Simulação de Gastos e Custos")

    with col_texto:
        st.title("Bem-vindo ao LABCOST")
        st.markdown(
            """
            **LABCOST – Laboratório de Simulação de Gastos e Custos**  

            Este simulador é utilizado na disciplina de **Contabilidade de Custos**,
            ministrada pela Profª **Fátima de Souza Freire** na **Universidade de Brasília (UnB)**,
            como parte das iniciativas do **NEPECON – Núcleo de Estudos e Pesquisas em Sustentabilidade
            Econômica e Socioambiental**.
            Contato: nepeconunb@gmail.com  
            Youtube: https://www.youtube.com/channel/UCu55I4Qpp2nBYWu5-qftkZw/videos

            O **LABCOST** é um laboratório virtual para apoiar o ensino de **Contabilidade de Custos e Gestão**, com foco em:

            - Comportamento dos **gastos fixos e variáveis**  
            - **Margem de contribuição** unitária e total  
            - **Ponto de equilíbrio** em unidades e em receita  
            - **Margem de segurança**  
            - **Grau de Alavancagem Operacional (GAO)**  
            - Análise de **mix de produtos**  
            - Controle de **estoques e CMV** (PEPS, UEPS, Média Ponderada)
            """
        )

    # contador simples na página inicial
    st.metric("Acessos nesta sessão", st.session_state["visit_count"])

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
            ### 📚 Classificação de Gastos e Inventário  
            - Na aba **“📚 Classificação de Gastos”**, os alunos podem:
              - Classificar itens em **Custo** ou **Despesa**  
              - Detalhar: Custo Direto/Indireto/Fixo/Variável, Despesa Fixa/Variável,
                Administrativa, com Vendas, Financeira  

            - Na aba **“📦 Livro de Inventário”**:
              - Simular **PEPS, UEPS e Média Ponderada**  
              - Comparar CMV e Estoque Final por método  
              - Utilizar vários meses e até 10 produtos  
            """
        )

    st.markdown("---")

    st.subheader("Sugestão de uso didático")
    st.markdown(
        """
        - Propor **cenários diferentes** (ex.: aumento de preço, redução de gastos fixos, 
          mudanças no mix de produtos, escolha do método de avaliação de estoques) e pedir aos alunos
          que analisem o impacto no **ponto de equilíbrio**, **lucro** e **CMV**.  
        - Usar o LABCOST em **aulas práticas de laboratório** ou em **atividades remotas**.  
        - Combinar com leituras sobre **margem de contribuição**, **decisão de mix de produtos**, 
          **GAO** e **métodos de avaliação de estoques**.  
        """
    )

    st.info(
        "O LABCOST é uma ferramenta educacional desenvolvida no âmbito do NEPECON/UnB "
        "para apoiar o ensino de Contabilidade de Custos e Gestão."
    )

# ========================================================
# TAB – SIMULADOR DE GASTOS E CUSTOS
# ========================================================
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
            "Preço de venda por unidade (R$)", min_value=0.0, max_value=10000.0, value=100.0
        )
        gasto_var = st.sidebar.number_input(
            "Gasto variável por unidade (R$)", min_value=0.0, max_value=10000.0, value=30.0
        )
        gastos_fixos = st.sidebar.number_input(
            "Gastos fixos totais (R$)", min_value=0.0, max_value=1000000.0, value=25000.0
        )
        quantidade = st.sidebar.number_input(
            "Volume de vendas esperado (unidades)", min_value=0, max_value=1000000, value=1000
        )

        st.sidebar.markdown("---")
        st.sidebar.write("Parâmetros para o gráfico:")
        q_min = st.sidebar.number_input("Volume mínimo (gráfico)", min_value=0, max_value=1000000, value=0)
        q_max = st.sidebar.number_input("Volume máximo (gráfico)", min_value=0, max_value=1000000, value=2000)
        q_step = st.sidebar.number_input("Incremento (gráfico)", min_value=1, max_value=1000000, value=100)

        # Cálculos principais
        mc_unit = preco - gasto_var
        mc_total = mc_unit * quantidade
        receita_total = preco * quantidade
        gasto_var_total = gasto_var * quantidade
        lucro = mc_total - gastos_fixos

        if mc_unit != 0:
            pe_unidades = gastos_fixos / mc_unit
            pe_receita = pe_unidades * preco
        else:
            pe_unidades = 0
            pe_receita = 0

        if mc_total - gastos_fixos != 0:
            gao = mc_total / (mc_total - gastos_fixos)
        else:
            gao = 0

        margem_seg_unid = quantidade - pe_unidades
        margem_seg_receita = receita_total - pe_receita
        if quantidade > 0:
            margem_seg_perc = (margem_seg_unid / quantidade) * 100
        else:
            margem_seg_perc = 0

        gasto_variavel_unitario = gasto_var
        gasto_fixo_unitario = gastos_fixos / quantidade if quantidade > 0 else 0
        gasto_unitario_total = gasto_variavel_unitario + gasto_fixo_unitario

        # Resultados
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
        st.write(f"Em percentual sobre o volume esperado: **{margem_seg_perc:,.1f}%**")

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
                    "GF Unitário": [(gastos_fixos / q) if q > 0 else None for q in volumes],
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
            min_value=0.0,
            max_value=1000000.0,
            value=50000.0,
        )

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
            - Ponto de equilíbrio do mix (unidades totais e por produto);  
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
                    min_value=0.0,
                    max_value=100000.0,
                    value=100.0 + 10 * i,
                    key=f"preco_{i}",
                )
            with col3:
                gv_i = st.number_input(
                    f"Gasto variável {i+1} (R$)",
                    min_value=0.0,
                    max_value=100000.0,
                    value=40.0 + 5 * i,
                    key=f"gv_{i}",
                )
            with col4:
                q_i = st.number_input(
                    f"Volume esperado {i+1} (unid.)",
                    min_value=0,
                    max_value=1000000,
                    value=1000,
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

        soma_q = sum(p["Q"] for p in produtos)

        if soma_q == 0:
            st.warning("Informe volumes de vendas maiores que zero para calcular o mix.")
        else:
            linhas = []
            mc_mix_ponderada = 0.0

            receita_total = 0.0
            gv_total = 0.0
            mc_total = 0.0

            for p in produtos:
                mc_unit_i = p["Preco"] - p["GV"]
                receita_i = p["Preco"] * p["Q"]
                gv_i_total = p["GV"] * p["Q"]
                mc_i_total = mc_unit_i * p["Q"]
                mix_i = p["Q"] / soma_q

                receita_total += receita_i
                gv_total += gv_i_total
                mc_total += mc_i_total

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

            if mc_mix_ponderada > 0:
                pe_mix_unidades = gastos_fixos_mix / mc_mix_ponderada
            else:
                pe_mix_unidades = 0

            for linha in linhas:
                mix_frac = linha["Mix (%)"] / 100
                linha["PE (unid.) no mix"] = pe_mix_unidades * mix_frac

            lucro_total = mc_total - gastos_fixos_mix

            df_mix = pd.DataFrame(linhas)

            st.subheader("Resumo por produto")
            st.dataframe(
                df_mix.style.format(
                    {
                        "Preço (R$)": "R$ {:,.2f}",
                        "Gasto Var. unit. (R$)": "R$ {:,.2f}",
                        "MC unit. (R$)": "R$ {:,.2f}",
                        "Receita (R$)": "R$ {:,.2f}",
                        "Gasto Var. Total (R$)": "R$ {:,.2f}",
                        "MC Total (R$)": "R$ {:,.2f}",
                        "Mix (%)": "{:,.1f}%",
                        "PE (unid.) no mix": "{:,.0f}",
                    }
                ),
                use_container_width=True,
            )

            st.subheader("Indicadores do Mix")

            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Receita total", f"R$ {receita_total:,.2f}")
                st.metric("Gasto variável total", f"R$ {gv_total:,.2f}")
            with col_b:
                st.metric("Margem de contribuição total", f"R$ {mc_total:,.2f}")
                st.metric("Gastos fixos totais", f"R$ {gastos_fixos_mix:,.2f}")
            with col_c:
                st.metric("Lucro operacional", f"R$ {lucro_total:,.2f}")
                st.metric(
                    "MC unitária média ponderada do mix",
                    f"R$ {mc_mix_ponderada:,.2f}",
                )

            st.markdown(
                f"""
                **Ponto de equilíbrio do mix (unidades totais):**  
                {pe_mix_unidades:,.0f} unidades *combinadas*, distribuídas conforme o mix de vendas.

                A tabela acima mostra, na coluna **"PE (unid.) no mix"**, quantas unidades de cada produto
                precisam ser vendidas **no ponto de equilíbrio**, mantendo o mix informado.
                """
            )

            # --------- GRÁFICO DO PE POR PRODUTO (ALTAIR) ----------
            df_pe = df_mix[["Produto", "PE (unid.) no mix"]].copy()
            df_pe.rename(columns={"PE (unid.) no mix": "PE_unid"}, inplace=True)

            df_pe["PE_unid"] = pd.to_numeric(df_pe["PE_unid"], errors="coerce").fillna(0)

            if (df_pe["PE_unid"] > 0).any():
                st.subheader("Gráfico do Ponto de Equilíbrio por produto (unidades)")

                chart = (
                    alt.Chart(df_pe)
                    .mark_bar()
                    .encode(
                        x=alt.X("Produto:N", title="Produto"),
                        y=alt.Y("PE_unid:Q", title="PE (unidades)"),
                        tooltip=["Produto", alt.Tooltip("PE_unid:Q", title="PE (unid.)")],
                    )
                    .properties(height=400)
                )

                st.altair_chart(chart, use_container_width=True)
            else:
                st.info(
                    "Os valores de PE por produto são zero. Ajuste os parâmetros do mix "
                    "ou dos gastos fixos para visualizar o gráfico."
                )

        st.caption("LABCOST – Uso educacional. Modo: Mix de produtos.")

# ========================================================
# TAB – CLASSIFICAÇÃO DE GASTOS
# ========================================================
with tab_classificacao:
    st.title("Classificação de Gastos: Custos x Despesas e Detalhamento")

    st.write(
        """
        Nesta atividade, o aluno deve **classificar os gastos** em:
        - **Custo** ou **Despesa**;  
        - E também indicar a **classificação detalhada**, escolhendo uma das opções:

        - Custo Direto  
        - Custo Indireto  
        - Custo Fixo  
        - Custo Variável  
        - Despesa Fixa  
        - Despesa Variável  
        - Despesa Administrativa  
        - Despesa com Vendas  
        - Despesa Financeira  
        """
    )

    itens = [
        {
            "descricao": "Salário da mão de obra diretamente envolvida na produção.",
            "tipo_correto": "Custo",
            "classificacao_correta": "Custo Direto",
        },
        {
            "descricao": "Matéria-prima utilizada na fabricação do produto.",
            "tipo_correto": "Custo",
            "classificacao_correta": "Custo Direto",
        },
        {
            "descricao": "Aluguel do prédio da fábrica.",
            "tipo_correto": "Custo",
            "classificacao_correta": "Custo Fixo",
        },
        {
            "descricao": "Energia elétrica das máquinas na fábrica (varia com a produção).",
            "tipo_correto": "Custo",
            "classificacao_correta": "Custo Variável",
        },
        {
            "descricao": "Depreciação das máquinas utilizadas na produção.",
            "tipo_correto": "Custo",
            "classificacao_correta": "Custo Indireto",
        },
        {
            "descricao": "Comissão dos vendedores sobre as vendas realizadas.",
            "tipo_correto": "Despesa",
            "classificacao_correta": "Despesa Variável",
        },
        {
            "descricao": "Salário fixo da equipe de vendas.",
            "tipo_correto": "Despesa",
            "classificacao_correta": "Despesa com Vendas",
        },
        {
            "descricao": "Salário da equipe administrativa do escritório central.",
            "tipo_correto": "Despesa",
            "classificacao_correta": "Despesa Administrativa",
        },
        {
            "descricao": "Gastos com propaganda e publicidade.",
            "tipo_correto": "Despesa",
            "classificacao_correta": "Despesa com Vendas",
        },
        {
            "descricao": "Juros pagos sobre empréstimos bancários.",
            "tipo_correto": "Despesa",
            "classificacao_correta": "Despesa Financeira",
        },
        {
            "descricao": "Seguro das instalações da fábrica (valor fixo anual).",
            "tipo_correto": "Custo",
            "classificacao_correta": "Custo Fixo",
        },
        {
            "descricao": "Telefone e internet do escritório administrativo.",
            "tipo_correto": "Despesa",
            "classificacao_correta": "Despesa Administrativa",
        },
    ]

    opcoes_tipo = ["Custo", "Despesa"]
    opcoes_classificacao = [
        "Custo Direto",
        "Custo Indireto",
        "Custo Fixo",
        "Custo Variável",
        "Despesa Fixa",
        "Despesa Variável",
        "Despesa Administrativa",
        "Despesa com Vendas",
        "Despesa Financeira",
    ]

    st.subheader("Atividade")
    st.write(
        "Para cada item abaixo, selecione **se é Custo ou Despesa** e a **classificação detalhada**."
    )

    respostas_tipo = []
    respostas_classificacao = []

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
            classificacao_escolhida = st.selectbox(
                "Classificação detalhada",
                opcoes_classificacao,
                key=f"class_{i}",
            )

        respostas_tipo.append(tipo_escolhido)
        respostas_classificacao.append(classificacao_escolhida)
        st.markdown("---")

    if st.button("Corrigir respostas"):
        resultados = []
        acertos_tipo = 0
        acertos_class = 0
        acertos_totais = 0

        for i, item in enumerate(itens):
            tipo_ok = respostas_tipo[i] == item["tipo_correto"]
            class_ok = respostas_classificacao[i] == item["classificacao_correta"]
            acertou_tudo = tipo_ok and class_ok

            if tipo_ok:
                acertos_tipo += 1
            if class_ok:
                acertos_class += 1
            if acertou_tudo:
                acertos_totais += 1

            resultados.append(
                {
                    "Item": i + 1,
                    "Descrição": item["descricao"],
                    "Tipo marcado": respostas_tipo[i],
                    "Tipo correto": item["tipo_correto"],
                    "Classificação marcada": respostas_classificacao[i],
                    "Classificação correta": item["classificacao_correta"],
                    "Acertou tipo e class.?": "Sim" if acertou_tudo else "Não",
                }
            )

        df_result = pd.DataFrame(resultados)
        st.subheader("Resultado da Atividade")
        st.write(f"Acertos no **tipo (Custo/Despesa)**: **{acertos_tipo} de {len(itens)}**")
        st.write(
            f"Acertos na **classificação detalhada**: **{acertos_class} de {len(itens)}**"
        )
        st.write(
            f"Itens com **tipo e classificação corretos ao mesmo tempo**: **{acertos_totais} de {len(itens)}**"
        )
        st.dataframe(df_result, use_container_width=True)

        st.info(
            "Sugestão didática: discuta com os alunos os itens em que houve erro, "
            "reforçando a diferença entre **custos diretos/indiretos/fixos/variáveis** "
            "e **despesas fixas, variáveis, administrativas, de vendas e financeiras**."
        )

# ========================================================
# TAB – PLANILHA DE MARK-UP
# ========================================================
with tab_markup:
    st.title("Planilha de Mark-up de Preço de Venda")

    st.write(
        """
        Esta planilha permite calcular o **preço de venda** a partir de um **custo unitário**
        e dos **percentuais incidentes sobre o preço de venda (PV)**, como impostos,
        comissões, despesas e margem de lucro desejada.

        Você pode escolher entre dois **métodos de custeio** para definir o custo-base:
        - **Custeio Variável**: considera apenas os **custos variáveis de fabricação**;
        - **Custeio por Absorção**: considera **custos variáveis + custos fixos de fabricação
          rateados por unidade**.
        """
    )

    st.markdown("---")

    col_esq, col_dir = st.columns([1, 1.1])

    # ---------------- ENTRADAS ----------------
    with col_esq:
        st.subheader("Entradas – Custo de Produção")

        metodo_custeio = st.radio(
            "Método de custeio:",
            ["Custeio Variável", "Custeio por Absorção"],
            horizontal=True,
        )

        # Custo variável unitário
        custo_var_unit = st.number_input(
            "Custo variável unitário de fabricação (R$)",
            min_value=0.0,
            value=80.0,
            step=1.0,
            format="%.2f",
        )

        # Dados adicionais para custeio por absorção
        custo_fixo_unit = 0.0
        custo_fixo_total = 0.0
        volume_producao = 0

        if metodo_custeio == "Custeio por Absorção":
            st.markdown("#### Dados para rateio dos custos fixos de fabricação")
            custo_fixo_total = st.number_input(
                "Custos fixos de fabricação no período (R$)",
                min_value=0.0,
                value=20000.0,
                step=500.0,
                format="%.2f",
            )
            volume_producao = st.number_input(
                "Volume produzido no período (unidades)",
                min_value=1,
                value=1000,
                step=100,
            )
            custo_fixo_unit = custo_fixo_total / volume_producao

        # Custo-base conforme método de custeio
        if metodo_custeio == "Custeio Variável":
            custo_unitario_base = custo_var_unit
        else:
            custo_unitario_base = custo_var_unit + custo_fixo_unit

        st.markdown("---")
        st.subheader("Percentuais sobre o **Preço de Venda (PV)**")

        impostos_perc = st.number_input(
            "Impostos sobre vendas (% do PV)",
            min_value=0.0,
            max_value=100.0,
            value=18.0,
            step=0.5,
            format="%.2f",
        )
        comissao_perc = st.number_input(
            "Comissão / taxas de venda (% do PV)",
            min_value=0.0,
            max_value=100.0,
            value=5.0,
            step=0.5,
            format="%.2f",
        )
        despesas_perc = st.number_input(
            "Despesas fixas / administrativas rateadas (% do PV)",
            min_value=0.0,
            max_value=100.0,
            value=10.0,
            step=0.5,
            format="%.2f",
        )
        outros_perc = st.number_input(
            "Outros encargos sobre o PV (%)",
            min_value=0.0,
            max_value=100.0,
            value=0.0,
            step=0.5,
            format="%.2f",
        )
        lucro_perc = st.number_input(
            "Lucro desejado (% do PV)",
            min_value=0.0,
            max_value=100.0,
            value=15.0,
            step=0.5,
            format="%.2f",
        )

    # ---------------- CÁLCULO DO MARK-UP ----------------
    with col_dir:
        st.subheader("Cálculo do Mark-up")

        st.markdown(
            f"""
            **Método de custeio selecionado:** `{metodo_custeio}`  

            - Custo variável unitário de fabricação: **R$ {custo_var_unit:,.2f}**  
            - Custo fixo unitário de fabricação (rateado): **R$ {custo_fixo_unit:,.2f}**  
            - **Custo-base unitário para o Mark-up:** **R$ {custo_unitario_base:,.2f}**
            """
        )

        soma_perc_sobre_pv = (
            impostos_perc
            + comissao_perc
            + despesas_perc
            + outros_perc
            + lucro_perc
        ) / 100.0

        if soma_perc_sobre_pv >= 1:
            st.error(
                "A soma dos percentuais sobre o preço de venda é maior ou igual a **100%**. "
                "Não é possível calcular o Mark-up. Reduza algum percentual."
            )
            preco_venda = 0.0
            fator_markup = 0.0
        else:
            # Fórmula clássica do Mark-up:
            # Mark-up = 1 / (1 - % sobre PV)
            fator_markup = (
                1 / (1 - soma_perc_sobre_pv) if custo_unitario_base > 0 else 0
            )
            preco_venda = custo_unitario_base * fator_markup

            st.metric("Fator de Mark-up", f"{fator_markup:,.4f}")
            st.metric("Preço de venda sugerido (PV)", f"R$ {preco_venda:,.2f}")

        st.markdown("---")

        # ---------------- PLANILHA RESUMO ----------------
        st.subheader("Planilha-resumo em formato de tabela")

        if preco_venda > 0:
            valor_impostos = preco_venda * impostos_perc / 100
            valor_comissao = preco_venda * comissao_perc / 100
            valor_despesas = preco_venda * despesas_perc / 100
            valor_outros = preco_venda * outros_perc / 100
            valor_lucro = preco_venda * lucro_perc / 100

            dados_tabela = [
                {
                    "Componente": "Custo variável unitário de fabricação",
                    "% sobre PV": "",
                    "Valor (R$)": custo_var_unit,
                },
                {
                    "Componente": "Custo fixo unitário de fabricação (absorção)",
                    "% sobre PV": "",
                    "Valor (R$)": custo_fixo_unit,
                },
                {
                    "Componente": f"Custo unitário base ({metodo_custeio})",
                    "% sobre PV": "",
                    "Valor (R$)": custo_unitario_base,
                },
                {
                    "Componente": "Impostos sobre vendas",
                    "% sobre PV": f"{impostos_perc:.2f} %",
                    "Valor (R$)": valor_impostos,
                },
                {
                    "Componente": "Comissões / taxas de venda",
                    "% sobre PV": f"{comissao_perc:.2f} %",
                    "Valor (R$)": valor_comissao,
                },
                {
                    "Componente": "Despesas fixas / administrativas",
                    "% sobre PV": f"{despesas_perc:.2f} %",
                    "Valor (R$)": valor_despesas,
                },
                {
                    "Componente": "Outros encargos",
                    "% sobre PV": f"{outros_perc:.2f} %",
                    "Valor (R$)": valor_outros,
                },
                {
                    "Componente": "Lucro desejado",
                    "% sobre PV": f"{lucro_perc:.2f} %",
                    "Valor (R$)": valor_lucro,
                },
                {
                    "Componente": "Preço de venda (PV)",
                    "% sobre PV": "100,00 %",
                    "Valor (R$)": preco_venda,
                },
            ]

            df_markup = pd.DataFrame(dados_tabela)

            st.dataframe(
                df_markup.style.format({"Valor (R$)": "R$ {:,.2f}"}),
                use_container_width=True,
            )
        else:
            st.info(
                "Informe o custo e os percentuais para calcular o Mark-up "
                "e gerar a planilha-resumo."
            )

    st.markdown("---")
    st.caption(
        "Planilha de Mark-up integrada ao LABCOST – uso educacional na disciplina de "
        "Contabilidade de Custos e Gestão (UnB / NEPECON), com métodos de "
        "custeio variável e custeio por absorção."
    )

# ========================================================
# TAB – LIVRO DE INVENTÁRIO
# ========================================================
with tab_inventario:
    inventario_produtos()

# ========================================================
# TAB 5 – AVALIAÇÃO DO SISTEMA (DASHBOARD SIMPLES E ESTÁVEL)
# ========================================================
with tab_avaliacao:
    st.title("⭐ Avaliação do LABCOST")

    st.write(
        """
        Ajude a melhorar o **LABCOST**!  
        Preencha rapidamente a avaliação abaixo e veja o painel com os resultados.
        """
    )

    # Arquivo CSV onde as avaliações serão guardadas
    csv_path = Path("avaliacoes_labcost.csv")

    # Lista de estados (UF)
    lista_estados = [
        "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS",
        "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC",
        "SP", "SE", "TO", "Outro/Exterior",
    ]

    # ---------------- FORMULÁRIO DE AVALIAÇÃO ----------------
    with st.form("form_avaliacao"):

        col_loc, col_tipo = st.columns(2)
        with col_loc:
            estado = st.selectbox(
                "Em qual estado (UF) você está?",
                options=lista_estados,
                index=lista_estados.index("DF") if "DF" in lista_estados else 0,
            )

        with col_tipo:
            tipo_usuario = st.selectbox(
                "Você é:",
                [
                    "Estudante",
                    "Professor",
                    "Profissional da área contábil",
                    "Outro",
                ],
            )

        col_notas = st.columns(3)
        with col_notas[0]:
            nota_geral = st.slider("Nota geral para o LABCOST", 1, 10, 9)
        with col_notas[1]:
            facilidade = st.slider("Facilidade de uso da interface", 1, 10, 9)
        with col_notas[2]:
            utilidade = st.slider("Utilidade para aprendizagem de custos", 1, 10, 10)

        palavra_labcost = st.selectbox(
            "Em **uma palavra**, como você define o LABCOST?",
            [
                "Excelente",
                "Ótimo",
                "Bom",
                "Regular",
                "Confuso",
                "Difícil",
            ],
        )

        enviar = st.form_submit_button("Enviar avaliação")

    # ---------------- TRATAMENTO DO ENVIO ----------------
    if enviar:
        # Registro da resposta (sem nome, e-mail, cidade)
        resposta = {
            "Data_hora": datetime.now().isoformat(timespec="seconds"),
            "Estado": estado,
            "Tipo de usuário": tipo_usuario,
            "Nota geral": nota_geral,
            "Facilidade": facilidade,
            "Utilidade": utilidade,
            "Palavra_LABCOST": palavra_labcost,
        }

        # Se já existir, carrega e acrescenta; senão, cria novo
        if csv_path.exists():
            df_existente = pd.read_csv(csv_path)
            df_novo = pd.concat(
                [df_existente, pd.DataFrame([resposta])],
                ignore_index=True,
            )
        else:
            df_novo = pd.DataFrame([resposta])

        # Salva (sobrescreve com o conjunto atualizado)
        df_novo.to_csv(csv_path, index=False, encoding="utf-8-sig")

        st.success("Obrigado pela sua avaliação! 🙌")
        st.write("### Resumo da sua resposta:")
        st.write(resposta)

    st.markdown("---")

    # ---------------- DASHBOARD DE AVALIAÇÕES ----------------
    st.subheader("📊 Painel de avaliações do LABCOST")

    if csv_path.exists():
        df_av = pd.read_csv(csv_path)

        if df_av.empty:
            st.info("Ainda não há dados suficientes para montar o painel.")
        else:
            # Garante que as notas sejam numéricas
            for col in ["Nota geral", "Facilidade", "Utilidade"]:
                if col in df_av.columns:
                    df_av[col] = pd.to_numeric(df_av[col], errors="coerce")

            # --------- KPI CARDS (topo do dashboard) ----------
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Respostas totais", f"{len(df_av)}")
            if "Nota geral" in df_av.columns:
                with col2:
                    st.metric("Média – Nota geral", f"{df_av['Nota geral'].mean():.1f}")
            if "Facilidade" in df_av.columns:
                with col3:
                    st.metric("Média – Facilidade", f"{df_av['Facilidade'].mean():.1f}")
            if "Utilidade" in df_av.columns:
                with col4:
                    st.metric("Média – Utilidade", f"{df_av['Utilidade'].mean():.1f}")

            # --------- PERFIL DOS USUÁRIOS ----------
            st.markdown("### 👥 Perfil dos usuários")

            col_a, col_b = st.columns(2)

            # Distribuição por tipo de usuário
            if "Tipo de usuário" in df_av.columns:
                dist_tipo = (
                    df_av["Tipo de usuário"]
                    .value_counts()
                    .rename_axis("Tipo de usuário")
                    .reset_index(name="Quantidade")
                    .set_index("Tipo de usuário")
                )

                with col_a:
                    st.markdown("#### Por tipo de usuário")
                    st.bar_chart(dist_tipo)

            # Distribuição por Estado (UF)
            if "Estado" in df_av.columns:
                df_av["Estado"] = df_av["Estado"].astype(str).str.upper().str.strip()
                dist_estado = (
                    df_av["Estado"]
                    .value_counts()
                    .rename_axis("Estado")
                    .reset_index(name="Quantidade")
                    .set_index("Estado")
                )

                with col_b:
                    st.markdown("#### Por estado (UF)")
                    st.bar_chart(dist_estado)

            # --------- OPINIÃO EM UMA PALAVRA ----------
            if "Palavra_LABCOST" in df_av.columns:
                st.markdown("### ☁️ Opinião geral sobre o LABCOST")

                palavras = (
                    df_av["Palavra_LABCOST"]
                    .astype(str)
                    .str.strip()
                )
                palavras = palavras[palavras != ""]
                palavras = palavras[palavras.str.lower() != "none"]

                if not palavras.empty:
                    freq_palavras = (
                        palavras.value_counts()
                        .rename_axis("Palavra")
                        .reset_index(name="Frequência")
                        .set_index("Palavra")
                    )
                    st.bar_chart(freq_palavras)

            # --------- BASE COMPLETA + DOWNLOAD ----------
            st.markdown("### 📄 Tabela completa de avaliações")
            st.dataframe(df_av, use_container_width=True)

            with open(csv_path, "rb") as f:
                st.download_button(
                    label="📥 Baixar avaliações em CSV",
                    data=f,
                    file_name="avaliacoes_labcost.csv",
                    mime="text/csv",
                )
    else:
        st.info(
            "Ainda não há avaliações salvas. Assim que a primeira for enviada, "
            "o painel será exibido aqui."
        )


