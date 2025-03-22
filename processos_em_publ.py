import pandas as pd

def extrair_ultimas_posicoes(valor):
    if isinstance(valor, str) and len(valor) >= 4:
        return valor[-4:]
    else:
        return None

def processar_arquivos(arquivo_principal, arquivo_lista_nomes, output_csv='resultado_processos_em_publ.csv'):
    df_principal = pd.read_excel(arquivo_principal, header=1)
    df_principal.columns = df_principal.columns.str.strip().str.upper()

    colunas_necessarias_principal = ["CONTRATADOR (PRESIDENTE/AGENTE DE CONTRATAÇÃO)", "QUANTIDADE DE LINHAS"]
    if not all(col in df_principal.columns for col in colunas_necessarias_principal):
        print(f"As colunas necessárias não foram encontradas no arquivo 'Controle Processos Publicação SCOMP2'.")
        return None

    df_principal['QUANTIDADE DE LINHAS'] = pd.to_numeric(df_principal['QUANTIDADE DE LINHAS'], errors='coerce').fillna(0).astype(int)
    df_lista_nomes = pd.read_excel(arquivo_lista_nomes)
    df_lista_nomes.columns = df_lista_nomes.columns.str.strip().str.upper()
    
    colunas_necessarias_lista_nomes = ["CHAVE", "NOME", "QUANTIDADE EM PUBLICAÇÃO"]
    if not all(col in df_lista_nomes.columns for col in colunas_necessarias_lista_nomes):
        print(f"As colunas necessárias não foram encontradas no arquivo 'ListaNomes'.")
        return None

    df_lista_nomes['CHAVE'] = df_lista_nomes['CHAVE'].astype(str).str.strip()
    df_principal['ULTIMAS 4 POSICOES'] = df_principal['CONTRATADOR (PRESIDENTE/AGENTE DE CONTRATAÇÃO)'].apply(extrair_ultimas_posicoes).astype(str).str.strip()
    total_quantidade_linhas = df_principal.groupby('ULTIMAS 4 POSICOES')['QUANTIDADE DE LINHAS'].sum().reset_index()
    total_quantidade_linhas.columns = ['ULTIMAS 4 POSICOES', 'TOTAL QUANTIDADE DE LINHAS']
    df_principal = pd.merge(df_principal, total_quantidade_linhas, on='ULTIMAS 4 POSICOES', how='left')
    df_principal = df_principal.drop_duplicates(subset=['ULTIMAS 4 POSICOES'])
    df_comparacao = pd.merge(df_principal, df_lista_nomes[['CHAVE', 'NOME', 'QUANTIDADE EM PUBLICAÇÃO']], left_on='ULTIMAS 4 POSICOES', right_on='CHAVE', how='inner')
    df_resultado = df_comparacao[['NOME', 'ULTIMAS 4 POSICOES', 'TOTAL QUANTIDADE DE LINHAS', 'QUANTIDADE EM PUBLICAÇÃO']]

    # Salva o resultado em um arquivo CSV para ser usado no script sort_agrup_comp
    df_resultado.to_csv(output_csv, index=False, sep=';', encoding='latin1')
    return df_resultado

# Caminhos dos arquivos locais (substitua pelo caminho completo se necessário)
caminho_arquivo_principal = r"C:\Users\c1r6\PycharmProjects\STREAMLIT\Controle Processos Publicação SCOMP2.xlsx"
caminho_arquivo_lista_nomes = r"C:\Users\c1r6\PycharmProjects\STREAMLIT\ListaNomes.xlsx"

# Executa o processamento e salva em um arquivo CSV
processar_arquivos(caminho_arquivo_principal, caminho_arquivo_lista_nomes)










