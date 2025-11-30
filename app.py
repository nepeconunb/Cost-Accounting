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
        Este módulo replica a sua **planilha de inventário por mês e por produto**.

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

    # Quantidade de meses e produtos
    n_meses = st.number_input(
        "Quantidade de meses para simular:",
        min_value=1,
        max_value=12,
        value=12,   # agora default 12
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
                }
            )

        df_res = pd.DataFrame(linhas_resultado)
        resultados_meses.append((mes, df_res))

        st.markdown(f"#### ✅ Resultado – Mês {mes}")

        # dicionário de formatação (sem CTu utilizado quando não for média)
        format_dict = {
            "Estoque inicial (CTu)": "R$ {:,.2f}",
            "Produção (CTu)": "R$ {:,.2f}",
            "Preço de venda (R$)": "R$ {:,.2f}",
            "CMV (R$)": "R$ {:,.2f}",
            "Estoque final (R$)": "R$ {:,.2f}",
        }
        if metodo.lower().startswith("média"):
            format_dict["CTu utilizado (método)"] = "R$ {:,.2f}"

        st.dataframe(
            df_res.style.format(format_dict),
            use_container_width=True,
        )

        total_cmv = df_res["CMV (R$)"].sum()
        total_estoque = df_res["Estoque final (R$)"].sum()

        col1, col2 = st.columns(2)
        with col1:
            st.metric(f"CMV total – Mês {mes}", f"R$ {total_cmv:,.2f}")
        with col2:
            st.metric(f"Estoque final total – Mês {mes}", f"R$ {total_estoque:,.2f}")

        st.markdown("---")

    # ----------------------------------------------------
    # Visão consolidada dos meses (resumo da planilha)
    # ----------------------------------------------------
    if len(resultados_meses) > 1:
        st.markdown("### 📊 Visão consolidada – Totais por mês")
        consol = []
        for mes, df_res in resultados_meses:
            consol.append(
                {
                    "Mês": mes,
                    "CMV total (R$)": df_res["CMV (R$)"].sum(),
                    "Estoque final total (R$)": df_res["Estoque final (R$)"].sum(),
                }
            )
        df_consol = pd.DataFrame(consol)
        st.dataframe(
            df_consol.style.format(
                {
                    "CMV total (R$)": "R$ {:,.2f}",
                    "Estoque final total (R$)": "R$ {:,.2f}",
                }
            ),
            use_container_width=True,
        )

    # ----------------------------------------------------
    # Gráfico de evolução de vendas por produto
    # ----------------------------------------------------
    vendas_rows = []
    for mes, df_res in resultados_meses:
        for _, row in df_res.iterrows():
            vendas_rows.append(
                {
                    "Mês": mes,
                    "Produto": row["Produto"],
                    "Quantidade vendida": row["Quantidade vendida (unid.)"],
                    "Receita (R$)": row["Quantidade vendida (unid.)"]
                    * row["Preço de venda (R$)"],
                }
            )

    if vendas_rows:
        df_vendas = pd.DataFrame(vendas_rows)

        st.markdown("### 📈 Evolução das vendas (quantidade por produto)")

        chart_vendas = (
            alt.Chart(df_vendas)
            .mark_line(point=True)
            .encode(
                x=alt.X("Mês:O", title="Mês"),
                y=alt.Y("Quantidade vendida:Q", title="Quantidade vendida (unid.)"),
                color=alt.Color("Produto:N", title="Produto"),
                tooltip=[
                    alt.Tooltip("Mês:O", title="Mês"),
                    "Produto",
                    alt.Tooltip("Quantidade vendida:Q", title="Qtd. vendida"),
                    alt.Tooltip("Receita (R$):Q", title="Receita (R$)", format=",.2f"),
                ],
            )
            .properties(height=400)
        )

        st.altair_chart(chart_vendas, use_container_width=True)

        # ------------------------------------------------
        # DRE – Custeio por Absorção x Custeio Variável
        # ------------------------------------------------
        st.markdown("### 🧾 DRE – Custeio por Absorção x Custeio Variável")

        total_receita = df_vendas["Receita (R$)"].sum()
        total_cmv_global = sum(df["CMV (R$)"].sum() for _, df in resultados_meses)

        st.markdown(
            f"""
            **Receita total das vendas (todos os meses e produtos):**  
            **R$ {total_receita:,.2f}**  

            **CMV total calculado com o método de estoque selecionado** (**{metodo}**):  
            **R$ {total_cmv_global:,.2f}**
            """
        )

        colc1, colc2 = st.columns(2)
        with colc1:
            custos_fixos_fab = st.number_input(
                "Custos fixos de fabricação do período (R$)",
                min_value=0.0,
                value=0.0,
                step=1000.0,
                key="dre_cfix_fab",
            )
            desp_var_venda = st.number_input(
                "Despesas variáveis de venda (R$)",
                min_value=0.0,
                value=0.0,
                step=500.0,
                key="dre_dv",
            )
        with colc2:
            desp_fixas_op = st.number_input(
                "Despesas fixas operacionais (vendas + adm) (R$)",
                min_value=0.0,
                value=0.0,
                step=1000.0,
                key="dre_df",
            )

        # ---- Custeio por Absorção ----
        cmv_abs = total_cmv_global + custos_fixos_fab
        lucro_bruto_abs = total_receita - cmv_abs
        resultado_op_abs = lucro_bruto_abs - (desp_var_venda + desp_fixas_op)

        # ---- Custeio Variável ----
        # Aqui consideramos o CMV calculado como custo variável dos produtos vendidos.
        margem_contrib = total_receita - (total_cmv_global + desp_var_venda)
        resultado_op_var = margem_contrib - (custos_fixos_fab + desp_fixas_op)

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("#### Custeio por Absorção")
            st.markdown(
                f"""
                **Receita líquida de vendas:** R$ {total_receita:,.2f}  
                **(-) CMV (inclui custos fixos de fabricação):** R$ {cmv_abs:,.2f}  
                **= Lucro bruto:** R$ {lucro_bruto_abs:,.2f}  

                **(-) Despesas variáveis de venda:** R$ {desp_var_venda:,.2f}  
                **(-) Despesas fixas operacionais:** R$ {desp_fixas_op:,.2f}  

                **= Resultado operacional (Absorção):**  
                **R$ {resultado_op_abs:,.2f}**
                """
            )

        with col_b:
            st.markdown("#### Custeio Variável")
            st.markdown(
                f"""
                **Receita líquida de vendas:** R$ {total_receita:,.2f}  
                **(-) Custos variáveis dos produtos vendidos (CV):** R$ {total_cmv_global:,.2f}  
                **(-) Despesas variáveis de venda:** R$ {desp_var_venda:,.2f}  
                **= Margem de contribuição:** R$ {margem_contrib:,.2f}  

                **(-) Custos fixos de fabricação:** R$ {custos_fixos_fab:,.2f}  
                **(-) Despesas fixas operacionais:** R$ {desp_fixas_op:,.2f}  

                **= Resultado operacional (Variável):**  
                **R$ {resultado_op_var:,.2f}**
                """
            )

# ========================================================
# TABS PRINCIPAIS
# ========================================================
tab_home, tab_classificacao, tab_inventario, tab_simulador, tab_markup = st.tabs(
    [
        "🏠 Página inicial",                 # 1ª aba
        "📚 Classificação de Gastos",        # 2ª aba
        "📦 Livro de Inventário",            # 3ª aba
        "💻 Simulador de Gastos e Custos",   # 4ª aba (Produto único + Mix)
        "🧾 Mark-up de Preço",               # 5ª aba
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
        - Proponha **cenários diferentes** (ex.: aumento de preço, redução de gastos fixos, 
          mudanças no mix de produtos, escolha do método de custeio de estoques) e peça para os alunos analisarem o impacto no **ponto de equilíbrio**, **lucro** e **CMV**.  
        - Use o LABCOST em **aulas práticas de laboratório** ou em **atividades remotas**.  
        - Combine com leituras sobre **margem de contribuição**, **decisão de mix de produtos**, **GAO** e **métodos de avaliação de estoques**.  
        """
    )

    st.info(
        "O LABCOST é uma ferramenta educacional desenvolvida no âmbito do NEPECON/UnB "
        "para apoiar o ensino de Contabilidade de Custos e Gestão."
    )

# ========================================================
# TAB 1 – SIMULADOR DE GASTOS E CUSTOS
# (igual ao que você já tinha – não alterei nada aqui)
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
    # (o restante do código da aba Simulador é igual ao que você já tinha)
    # -----------------------------------------------------
    # >>> COLE AQUI O MESMO BLOCO “Produto único / Mix de produtos”
    #     QUE JÁ ESTAVA FUNCIONANDO NO SEU ARQUIVO <<<

    st.caption("LABCOST – Uso educacional. Modo: Produto único ou Mix de produtos.")

# ========================================================
# TAB 2 – CLASSIFICAÇÃO DE GASTOS
# (igual ao anterior – não alterei nada)
# ========================================================
# ...  (mantenha o bloco de Classificação de Gastos que você já tinha) ...

# ========================================================
# TAB 3 – PLANILHA DE MARK-UP
# (igual ao anterior – não alterei nada)
# ========================================================
# ...  (mantenha o bloco da planilha de Mark-up que você já tinha) ...

# ========================================================
# TAB 4 – LIVRO DE INVENTÁRIO
# ========================================================
with tab_inventario:
    inventario_produtos()
