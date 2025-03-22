import streamlit as st
import pandas as pd
from pulp import LpMaximize, LpProblem, LpVariable, lpSum
import os
from processos_em_publ import processar_arquivos  # Importe a função processar_arquivos
import random

# Defina os caminhos dos arquivos Excel que serão utilizados no `processos_em_publ.py`
caminho_arquivo_principal = r"C:\Users\c1r6\PycharmProjects\STREAMLIT\Controle Processos Publicação SCOMP2.xlsx"
caminho_arquivo_lista_nomes = r"C:\Users\c1r6\PycharmProjects\STREAMLIT\ListaNomes.xlsx"
output_csv = "resultado_processos_em_publ.csv"  # Nome do arquivo CSV a ser gerado

def gerar_bolinhas():
    cores = ['#F80813', '#F2FE02', '#3ED12F']  # Cores hexadecimais
    bolinhas_html = "".join([f"<span style='color:{cor}; font-size:20px;'>●</span> " for cor in random.choices(cores, k=4)])
    return bolinhas_html

# Verifica se o CSV já existe, se não, gera-o automaticamente
if not os.path.exists(output_csv):
    print(f"O arquivo '{output_csv}' não foi encontrado. Gerando o arquivo automaticamente...")
    processar_arquivos(caminho_arquivo_principal, caminho_arquivo_lista_nomes, output_csv=output_csv)
    print(f"Arquivo '{output_csv}' gerado com sucesso!")
else:
    print(f"Arquivo '{output_csv}' já existente. Pulando a geração do CSV.")

# Adiciona o botão de upload de arquivo para o usuário carregar a planilha de nomes
uploaded_file = st.file_uploader("Selecione o arquivo 'Matriz Pica Pau' aqui", type=['xlsx'])

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

    # Lê o resultado do script `processos_em_publ`
    try:
        # Lê o arquivo CSV com separador e encoding corretos para evitar problemas de leitura
        resultado_processos_df = pd.read_csv(output_csv, sep=';', encoding='ISO-8859-1')
        resultado_processos_df.columns = resultado_processos_df.columns.str.upper()  # Padroniza colunas para maiúsculas

        # Garante que a coluna 'QP' esteja presente no DataFrame, usando 'TOTAL QUANTIDADE DE LINHAS'
        if 'TOTAL QUANTIDADE DE LINHAS' in resultado_processos_df.columns:
            resultado_processos_df.rename(columns={'TOTAL QUANTIDADE DE LINHAS': 'QP'}, inplace=True)
        else:
            resultado_processos_df['QP'] = 0  # Se a coluna não existir, cria 'QP' com valor 0

        # Integra o resultado com o `nomes_df`, adicionando a coluna "QP"
        nomes_df = pd.merge(nomes_df, resultado_processos_df[['NOME', 'QP']], left_on='NOME', right_on='NOME', how='left')

        # Verificar se a coluna 'QP' foi adicionada corretamente
        if 'QP' not in nomes_df.columns:
            st.error("Erro: A coluna 'QP' não foi encontrada após o merge. Verifique se o CSV possui a coluna 'QUANTIDADE EM PUBLICAÇÃO' ou 'QP'.")
            st.stop()
        else:
            # Preenche valores nulos de QP com 0
            nomes_df['QP'].fillna(0, inplace=True)

    except Exception as e:
        st.error(f"Erro ao ler ou processar o arquivo CSV '{output_csv}': {e}")
        st.stop()

    # Adiciona o botão de upload para a planilha de agrupamento
    agrupamento_file = st.file_uploader("Selecione o arquivo de agrupamento 'XRA'", type=['xlsx'])

    if agrupamento_file is not None:
        agrupamento_df = pd.read_excel(agrupamento_file)  # Carrega o agrupamento do arquivo de upload

        # Adiciona a quantidade associada a cada agrupamento no DataFrame
        agrupamento_df['QUANTIDADE'] = agrupamento_df.groupby('nr acompanhamento')['nr acompanhamento'].transform('count')
        quantidade_agrupamento = agrupamento_df.set_index('nr acompanhamento')['QUANTIDADE'].to_dict()

        # Extrai números de acompanhamento únicos
        nr_acompanhamento = agrupamento_df['nr acompanhamento'].dropna().unique().tolist()

        # Definindo os sete grupos

        # 1. Somente PREG
        nomes_somente_preg = nomes_filtrados[(nomes_filtrados['PREGAO'] == 'S') & (nomes_filtrados['BSER'] != 'S')]['NOME'].tolist()

        # 2. Somente BSER
        nomes_somente_bser = nomes_filtrados[(nomes_filtrados['BSER'] == 'S') & (nomes_filtrados['PREGAO'] != 'S')]['NOME'].tolist()

        # 3. PREG e BSER
        nomes_preg_bser = nomes_filtrados[(nomes_filtrados['PREGAO'] == 'S') & (nomes_filtrados['BSER'] == 'S')]['NOME'].tolist()

        # 4. Outros (nem PREG nem BSER)
        nomes_outros = nomes_filtrados[(nomes_filtrados['PREGAO'] != 'S') & (nomes_filtrados['BSER'] != 'S')]['NOME'].tolist()

        # Inicializa o problema de otimização
        problema = LpProblem("Distribuicao_Agrupamentos", LpMaximize)

        # Criação das variáveis para cada grupo
        vars_preg = LpVariable.dicts("PREG", [(nome, nr) for nome in nomes_somente_preg for nr in nr_acompanhamento if "PREG" in nr], lowBound=0, cat='Integer')
        vars_bser = LpVariable.dicts("BSER", [(nome, nr) for nome in nomes_somente_bser for nr in nr_acompanhamento if "BSER" in nr], lowBound=0, cat='Integer')
        vars_preg_bser = LpVariable.dicts("PREG_BSER", [(nome, nr) for nome in nomes_preg_bser for nr in nr_acompanhamento if "PREG" in nr or "BSER" in nr], lowBound=0, cat='Integer')
        vars_outros = LpVariable.dicts("OUTROS", [(nome, nr) for nome in nomes_outros for nr in nr_acompanhamento if "PREG" not in nr], lowBound=0, cat='Integer')

        # Limitar o número máximo de itens por pessoa para manter o balanceamento
        max_itens_por_pessoa = len(nr_acompanhamento) // len(nomes_somente_preg + nomes_somente_bser + nomes_preg_bser + nomes_outros) + 10  # Ajuste conforme necessário

        # Restrição 1: Atribuir números PREG apenas a nomes que são do grupo Somente PREG
        for nome in nomes_somente_preg:
            problema += lpSum([vars_preg[(nome, nr)] for nr in nr_acompanhamento if "PREG" in nr]) >= 1, f"Restricao_PREG_{nome}"

        # Restrição 2: Atribuir números BSER apenas a nomes que são do grupo Somente BSER
        for nome in nomes_somente_bser:
            problema += lpSum([vars_bser[(nome, nr)] for nr in nr_acompanhamento if "BSER" in nr]) >= 1, f"Restricao_BSER_{nome}"

        # Restrição 3: Atribuir números PREG e BSER aos nomes que pertencem a ambos os grupos
        for nome in nomes_preg_bser:
            problema += lpSum([vars_preg_bser[(nome, nr)] for nr in nr_acompanhamento if "PREG" in nr or "BSER" in nr]) >= 1, f"Restricao_PREG_BSER_{nome}"

        # Restrição 4: Distribuir os agrupamentos restantes para os outros nomes, incluindo "OUTROS"
        for nome in nomes_outros:
            problema += lpSum([vars_outros[(nome, nr)] for nr in nr_acompanhamento if "PREG" not in nr and "BSER" not in nr]) >= 1, f"Restricao_Outros_{nome}"

        # Garantir que todos os agrupamentos sejam distribuídos e balanceados
        for nr in nr_acompanhamento:
            problema += lpSum([vars_preg.get((nome, nr), 0) for nome in nomes_somente_preg] +
                              [vars_bser.get((nome, nr), 0) for nome in nomes_somente_bser] +
                              [vars_preg_bser.get((nome, nr), 0) for nome in nomes_preg_bser] +
                              [vars_outros.get((nome, nr), 0) for nome in nomes_outros]) == 1, f"Distribuicao_agrupamento_{nr}"

        # Balanceamento adicional para limitar o número de agrupamentos por pessoa
        for nome in nomes_somente_preg + nomes_somente_bser + nomes_preg_bser + nomes_outros:
            problema += lpSum([vars_preg.get((nome, nr), 0) for nr in nr_acompanhamento] +
                              [vars_bser.get((nome, nr), 0) for nr in nr_acompanhamento] +
                              [vars_preg_bser.get((nome, nr), 0) for nr in nr_acompanhamento] +
                              [vars_outros.get((nome, nr), 0) for nr in nr_acompanhamento]) <= max_itens_por_pessoa, f"Restricao_Max_Itens_{nome}"

        # Resolver o problema
        problema.solve()

        # Armazenar os resultados
        distribuicao_resultado = {nome: [] for nome in nomes_somente_preg + nomes_somente_bser + nomes_preg_bser + nomes_outros}

        # Resultados para PREG, BSER e Outros
        for (nome, nr), var in vars_preg.items():
            if var.varValue > 0:
                distribuicao_resultado[nome].append(nr)
        for (nome, nr), var in vars_bser.items():
            if var.varValue > 0:
                distribuicao_resultado[nome].append(nr)
        for (nome, nr), var in vars_preg_bser.items():
            if var.varValue > 0:
                distribuicao_resultado[nome].append(nr)
        for (nome, nr), var in vars_outros.items():
            if var.varValue > 0:
                distribuicao_resultado[nome].append(nr)

       
        # Cálculo final das colunas e exibição do DataFrame
        total_itens_alocados = {
            nome: sum([quantidade_agrupamento.get(nr, 0) for nr in distribuicao_resultado.get(nome, [])])
            for nome in nomes_somente_preg + nomes_somente_bser + nomes_preg_bser + nomes_outros
        }

        # Criação do DataFrame
        resultado_df = pd.DataFrame({
            'Nome': nomes_somente_preg + nomes_somente_bser + nomes_preg_bser + nomes_outros,
            'Agrupamento': [", ".join(distribuicao_resultado.get(nome, [])) for nome in nomes_somente_preg + nomes_somente_bser + nomes_preg_bser + nomes_outros],
            'TIA': [total_itens_alocados.get(nome, 0) for nome in nomes_somente_preg + nomes_somente_bser + nomes_preg_bser + nomes_outros],  # Total de Itens Alocados
            'PDT': [produtividade_dict.get(nome, 0) for nome in nomes_somente_preg + nomes_somente_bser + nomes_preg_bser + nomes_outros],  # Produtividade
            'QIC': [qtde_itens_dict.get(nome, 0) for nome in nomes_somente_preg + nomes_somente_bser + nomes_preg_bser + nomes_outros],  # Quantidade de Itens em Carteira
            'QP': [nomes_df[nomes_df['NOME'] == nome]['QP'].values[0] for nome in nomes_somente_preg + nomes_somente_bser + nomes_preg_bser + nomes_outros],  # Quantidade em Publicação
            'Total Prev': [
                total_itens_alocados.get(nome, 0) + produtividade_dict.get(nome, 0) + qtde_itens_dict.get(nome, 0) + nomes_df[nomes_df['NOME'] == nome]['QP'].values[0]
                for nome in nomes_somente_preg + nomes_somente_bser + nomes_preg_bser + nomes_outros],  # Total Geral
            'Bolinhas': [gerar_bolinhas() for nome in nomes_somente_preg + nomes_somente_bser + nomes_preg_bser + nomes_outros]  # Gera as bolinhas coloridas aleatórias
        })

        # Adiciona uma coluna de índice começando em 1
        resultado_df.index = range(1, len(resultado_df) + 1)
        resultado_df.reset_index(inplace=True)
        resultado_df.rename(columns={'index': 'Nº'}, inplace=True)

        # Adiciona a coluna de bolinhas
        resultado_df['Bolinhas'] = [gerar_bolinhas() for _ in range(len(resultado_df))]

        # Função para exibir a tabela com as bolinhas ao lado, números sem casas decimais e cabeçalho verde
        def exibir_tabela_com_bolinhas(df):
            tabela_html = """
            <style>
                table {
                    width: 100%;
                    border-collapse: collapse;
                }
                th {
                    background-color: #008000; /* Cor verde para o cabeçalho */
                    color: white;
                    padding: 8px;
                    text-align: left;
                    font-weight: normal; /* Fonte menos destacada */
                }
                td {
                    padding: 8px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }
                td.bolinhas {
                    text-align: right; /* Alinha as bolinhas à direita */
                }
            </style>
            <table>
            """
            # Adiciona cabeçalho
            tabela_html += "<tr>"
            for coluna in df.columns[:-1]:  # Todas as colunas, exceto 'Bolinhas'
                tabela_html += f"<th>{coluna}</th>"
            tabela_html += "<th>HistoCarga</th></tr>"

            # Adiciona dados e bolinhas
            for i, linha in df.iterrows():
                tabela_html += "<tr>"
                for valor in linha[:-1]:  # Todas as colunas, exceto 'Bolinhas'
                    if isinstance(valor, (int, float)):  # Formata valores numéricos sem casa decimal
                        valor = f"{int(valor)}"
                    tabela_html += f"<td>{valor}</td>"
                # Adiciona bolinhas ao final de cada linha
                tabela_html += f"<td class='bolinhas'>{linha['Bolinhas']}</td>"
                tabela_html += "</tr>"

            tabela_html += "</table>"
            return tabela_html

        # Exibição no Streamlit com as bolinhas à direita
        st.title("Distribuição Aleatória com Programação Linear")
        st.write("Distribuição considerando a soma de PRODUTIVIDADE, QTDE ITENS EM CARTEIRA e QP.")

        # Renderizar tabela com bolinhas ao lado
        tabela_html = exibir_tabela_com_bolinhas(resultado_df)
        st.markdown(tabela_html, unsafe_allow_html=True)

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








