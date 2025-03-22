import streamlit as st


# containers
# columns

secao_usuario = st.session_state
nome_usuario = None
if "username" in secao_usuario:
    nome_usuario = secao_usuario.name

coluna_esquerda, coluna_direita = st.columns([1, 1])

coluna_esquerda.title("Time SCOMP")
if nome_usuario:
    coluna_esquerda.write(f"#### Bem vindo, {nome_usuario}") # markdown
botao_dashboards = coluna_esquerda.button("Dashboard Projetos")
botao_indicadores = coluna_esquerda.button("Principais Indicadores")
botao_sorteador = coluna_esquerda.button("Sorteador")
botao_sort_agrupamentos = coluna_esquerda.button("Sorteador Agrupamentos")
botao_sort_agrup_comp = coluna_esquerda.button("Sorteador AgrupaComprador")

if botao_dashboards:
    st.switch_page("dashboard.py")
if botao_indicadores:
    st.switch_page("indicadores.py")
if botao_sorteador:
    st.switch_page("sorteador.py")
if botao_sort_agrupamentos:
    st.switch_page("sort_agrupamento.py")
if botao_sort_agrup_comp:
    st.switch_page("sort_agrup_comp.py")

container = coluna_direita.container(border=False)
container.image("imagens/croupier.webp")
