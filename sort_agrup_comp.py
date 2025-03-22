import streamlit as st
import pandas as pd
import random
from pulp import LpMaximize, LpProblem, LpVariable, lpSum

# Adiciona o botão de upload de arquivo para o usuário carregar a planilha
uploaded_file = st.file_uploader("Selecione um arquivo de nomes", type=['xlsx'])

if uploaded_file is not None:
    # Processa o arquivo se algo for carregado
    nomes_df = pd.read_excel(uploaded_file)  # Assume que o arquivo é um Excel
    nomes_df.columns = nomes_df.columns.str.upper()  # Corrige os nomes das colunas para maiúsculas

    # Carrega a produtividade e quantidade de itens em carteira dos nomes carregados
    produtividade_dict = nomes_df.set_index('NOME')['PRODUTIVIDADE'].fillna(0).to_dict()
    qtde_itens_dict = nomes_df.set_index('NOME')['QTDE ITENS EM CARTEIRA'].fillna(0).to_dict()

    # Soma de PRODUTIVIDADE e QTDE ITENS EM CARTEIRA, substituindo None por 0
    soma_produtividade_itens = {nome: produtividade_dict.get(nome, 0) + qtde_itens_dict.get(nome, 0) for nome in produtividade_dict.keys()}
    meta = 96  # Meta de produtividade a ser atingida

    # Filtra as pessoas que marcaram "S" na coluna "CONTRATADOR"
    nomes_filtrados = nomes_df[nomes_df['CONTRATADOR'] == 'S']

    # Adiciona o botão de upload para a planilha de agrupamento
    agrupamento_file = st.file_uploader("Selecione um arquivo de agrupamento", type=['xlsx'])

    if agrupamento_file is not None:
        agrupamento_df = pd.read_excel(agrupamento_file)  # Carrega o agrupamento do arquivo de upload

        # Adiciona a quantidade associada a cada agrupamento no DataFrame
        agrupamento_df['QUANTIDADE'] = agrupamento_df.groupby('nr acompanhamento')['nr acompanhamento'].transform('count')
        quantidade_agrupamento = agrupamento_df.set_index('nr acompanhamento')['QUANTIDADE'].to_dict()
        
        # Extrai números de acompanhamento únicos
        nr_acompanhamento = agrupamento_df['nr acompanhamento'].dropna().unique().tolist()

        # Filtra apenas os números que possuem "PREG"
        nr_pregao = [nr for nr in nr_acompanhamento if isinstance(nr, str) and "PREG" in nr]
        nr_nao_pregao = [nr for nr in nr_acompanhamento if isinstance(nr, str) and "PREG" not in nr]

        # Separa os nomes que têm "PREGÃO" marcado como "S" e os demais
        nomes_pregao = nomes_filtrados[nomes_filtrados['PREGAO'] == 'S']['NOME'].tolist()
        nomes_nao_pregao = nomes_filtrados[nomes_filtrados['PREGAO'] != 'S']['NOME'].tolist()

        # Inicializa o problema de otimização
        problema = LpProblem("Distribuicao_Agrupamentos", LpMaximize)

        # Cria variáveis de decisão para cada nome e número de acompanhamento (quantidade alocada)
        vars_pregao = LpVariable.dicts("PREG", [(nome, nr) for nome in nomes_pregao for nr in nr_pregao], lowBound=0, cat='Integer')
        vars_nao_pregao = LpVariable.dicts("Outros", [(nome, nr) for nome in nomes_nao_pregao for nr in nr_nao_pregao], lowBound=0, cat='Integer')

        # Restrição 1: Atribuir números PREG apenas a nomes com Pregão = "S"
        for nome in nomes_pregao:
            problema += lpSum([vars_pregao[(nome, nr)] for nr in nr_pregao if (nome, nr) in vars_pregao]) <= len(nr_pregao), f"Restricao_PREG_{nome}"

        # Restrição 2: Atribuir números não PREG apenas a nomes sem Pregão = "S"
        for nome in nomes_nao_pregao:
            problema += lpSum([vars_nao_pregao[(nome, nr)] for nr in nr_nao_pregao if (nome, nr) in vars_nao_pregao]) <= len(nr_nao_pregao), f"Restricao_Outros_{nome}"

        # Restrição 3: Garantir que a soma da PRODUTIVIDADE e QTDE ITENS EM CARTEIRA atinja a meta de 96
        for nome in nomes_pregao + nomes_nao_pregao:
            valor_soma_produtividade = soma_produtividade_itens.get(nome, 0)
            problema += (
                lpSum([vars_pregao.get((nome, nr), 0) * quantidade_agrupamento.get(nr, 0) +
                       vars_nao_pregao.get((nome, nr), 0) * quantidade_agrupamento.get(nr, 0) for nr in nr_acompanhamento]) +
                valor_soma_produtividade
            ) >= meta, f"Meta_{nome}"

        # Restrição 4: Cada número de acompanhamento deve ser alocado no máximo uma vez
        for nr in nr_acompanhamento:
            problema += lpSum([vars_pregao.get((nome, nr), 0) for nome in nomes_pregao if (nome, nr) in vars_pregao] +
                              [vars_nao_pregao.get((nome, nr), 0) for nome in nomes_nao_pregao if (nome, nr) in vars_nao_pregao]) <= 1, f"Unicidade_Agrupamento_{nr}"

        # Definindo a função objetivo para balancear a distribuição
        problema += lpSum([lpSum([vars_pregao.get((nome, nr), 0) * quantidade_agrupamento.get(nr, 0) for nr in nr_pregao if (nome, nr) in vars_pregao]) + 
                           lpSum([vars_nao_pregao.get((nome, nr), 0) * quantidade_agrupamento.get(nr, 0) for nr in nr_nao_pregao if (nome, nr) in vars_nao_pregao]) for nome in nomes_pregao + nomes_nao_pregao])

        # Resolver o problema
        problema.solve()

        # Obtendo os resultados
        distribuicao_pregao_resultado = {nome: [] for nome in nomes_pregao}
        distribuicao_nao_pregao_resultado = {nome: [] for nome in nomes_nao_pregao}

        # Armazena as distribuições resultantes
        for (nome, nr), var in vars_pregao.items():
            if var.varValue > 0:
                distribuicao_pregao_resultado[nome].append(nr)

        for (nome, nr), var in vars_nao_pregao.items():
            if var.varValue > 0:
                distribuicao_nao_pregao_resultado[nome].append(nr)

        # Calcula o total de itens alocados para cada nome, considerando a quantidade de cada agrupamento
        total_itens_alocados = {nome: sum([quantidade_agrupamento.get(nr, 0) for nr in distribuicao_pregao_resultado.get(nome, [])]) +
                                        sum([quantidade_agrupamento.get(nr, 0) for nr in distribuicao_nao_pregao_resultado.get(nome, [])])
                                for nome in nomes_pregao + nomes_nao_pregao}

        # Criação do DataFrame para exibição
        resultado_df = pd.DataFrame({
            'Nome': nomes_pregao + nomes_nao_pregao,
            'Agrupamento': [", ".join(distribuicao_pregao_resultado.get(nome, [])) for nome in nomes_pregao] + 
                           [", ".join(distribuicao_nao_pregao_resultado.get(nome, [])) for nome in nomes_nao_pregao],
            'TIA': [total_itens_alocados.get(nome, 0) for nome in nomes_pregao + nomes_nao_pregao],  # Total de Itens Alocados
            'PDT': [produtividade_dict.get(nome, 0) for nome in nomes_pregao + nomes_nao_pregao],  # Produtividade
            'QIC': [qtde_itens_dict.get(nome, 0) for nome in nomes_pregao + nomes_nao_pregao],  # Quantidade de Itens em Carteira
            'Total Prev': [total_itens_alocados.get(nome, 0) + produtividade_dict.get(nome, 0) + qtde_itens_dict.get(nome, 0) for nome in nomes_pregao + nomes_nao_pregao]  # Total Geral
        })

        # Exibição no Streamlit
        st.title("Distribuição Aleatória com Programação Linear")
        st.write("Distribuição considerando a soma de PRODUTIVIDADE e QTDE ITENS EM CARTEIRA para atingir a meta de 96.")
        st.dataframe(resultado_df)

        # Mensagem de erro se algum nome não atingiu a meta
        nomes_abaixo_meta = resultado_df[resultado_df['Total Prev'] < meta]
        if not nomes_abaixo_meta.empty:
            st.markdown(f"<span style='color:yellow'>Nr de agrupamentos insuficiente para que todos atinjam a Meta 96</span>", unsafe_allow_html=True)
            quantidade_necessaria = sum(meta - nomes_abaixo_meta['Total Prev'])
            st.write(f"Quantidade necessária: {quantidade_necessaria}")

        # Botão de Reiniciar para apagar o resultado
        if st.button("🔄 Reiniciar"):
            # Limpa a distribuição atual e lista de nomes completa
            st.session_state.distribuicao = None
            st.session_state.nomes_completo = None
            st.session_state.resultado_df = None
            st.rerun()  # Reinicia a interface








