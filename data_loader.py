import streamlit as st
import pandas as pd

@st.cache_data
def carregar_dados():
    tabela = pd.read_excel("Base.xlsx")
    return tabela

@st.cache_data
def carregar_nomes():
    tabela = pd.read_excel("ListaNomes.xlsx")
    return tabela

@st.cache_data
def carregar_agrupamento():
    tabela = pd.read_excel("xra.xlsx")
    return tabela