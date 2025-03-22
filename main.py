import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth

st.set_page_config(
    page_title="SCOMP",  # Define o título da aba
    page_icon="imagens/logo.png"  # Caminho para o seu ícone
)

@st.cache_data
def carregar_dados():
    tabela = pd.read_excel("Base.xlsx")
    return tabela

base = carregar_dados()

    
pg = st.navigation(
    {
    "Home": [st.Page("homepage.py", title="SCOMP")],
    "Dashboards": [st.Page("dashboard.py", title="Dashboard"), st.Page("indicadores.py", title="Indicadores")],
    "Sorteador": [st.Page("sorteador.py", title="Sorteador")],
    "Sort_Agrupamentos": [st.Page("sort_agrupamento.py", title="Sorteador Agrupamentos")],
    "Sort_Agrupacomprador": [st.Page("sort_agrup_comp.py", title="Sorteador AgrupaComprador")]
    }
)


pg.run()
