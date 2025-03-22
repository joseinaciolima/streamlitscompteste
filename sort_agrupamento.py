import streamlit as st
import pandas as pd
import random

# Adiciona o botão de upload de arquivo para o usuário carregar a planilha de nomes
uploaded_file = st.file_uploader("Selecione o arquivo 'ListaNomes.xlsx'", type=['xlsx'])

if uploaded_file is not None:
    # Processa o arquivo de nomes carregado
    nomes_df = pd.read_excel(uploaded_file)  # Assume que o arquivo é um Excel
    nomes_df.columns = nomes_df.columns.str.upper()  # Corrige os nomes das colunas para maiúsculas

    # Verifica se as colunas "NOME" e "ACEITA?" existem no arquivo
    if 'NOME' in nomes_df.columns and 'ACEITA?' in nomes_df.columns:
        # Filtra as pessoas que marcaram "S" na coluna "ACEITA?"
        nomes_filtrados = nomes_df[nomes_df['ACEITA?'] == 'S']

        # Converte a coluna com os nomes em uma lista
        nomes = nomes_filtrados['NOME'].tolist()

        # Configuração inicial de estado
        if 'vencedor' not in st.session_state:
            st.session_state.vencedor = None

        # Título da aplicação
        st.title("Sorteio agrupamento 2203 (50 itens)")

        # Instrução
        st.write("Clique no botão 'Play' para sortear um nome aleatório.")

        # Verifica se a lista de nomes está vazia
        if len(nomes) == 0:
            st.error("Nenhuma pessoa elegível para o sorteio. Verifique a coluna 'Aceita?' no arquivo 'ListaNomes.xlsx'.")
        else:
            # Botão de Play (com símbolo ">")
            if st.button("▶️ Play"):
                st.session_state.vencedor = random.choice(nomes)

            # Exibe o vencedor atual, se houver
            if st.session_state.vencedor:
                st.markdown(
                    f"""
                    <div style='background-color: #d4edda; padding: 10px; border-radius: 5px;'>
                        <span style='color: #155724; font-weight: bold;'>🎉 O vencedor do sorteio foi:</span>
                        <span style='margin-left: 20px; color: #155724;'>{st.session_state.vencedor}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            # Botão de Reiniciar para apagar o resultado
            if st.button("🔄 Reiniciar"):
                # Limpa o estado do vencedor
                st.session_state.vencedor = None
                # Reinicia a interface
                st.rerun()
    else:
        st.error("O arquivo carregado não contém as colunas 'NOME' e/ou 'ACEITA?'. Por favor, verifique o arquivo e tente novamente.")
else:
    st.warning("Por favor, carregue um arquivo 'ListaNomes.xlsx' para iniciar o sorteio.")

