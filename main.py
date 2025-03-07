import streamlit as st
import re


st.set_page_config(layout="wide")  # Define o layout para ocupar toda a largura

# CSS para reduzir o espaço no topo da página
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 3rem !important; /* Remove espaço superior */
        }
    </style>
    """,
    unsafe_allow_html=True
)




# LOGO

logo_url = "https://ispn.org.br/site/wp-content/uploads/2021/04/logo_ISPN_2021.png"

# Usando HTML para centralizar a imagem
st.markdown(
    f"""
    <div style="text-align: center;">
        <img src="{logo_url}" width="250">
    </div>
    """,
    unsafe_allow_html=True
)


st.write("")
st.write("")
st.write("")
st.write("")


# Título
st.markdown(
    """
    <div style="text-align: center;">
        <h2>Gestor de Viagens do ISPN</h2>
    </div>
    """,
    unsafe_allow_html=True
)


st.write("")
st.write("")
st.write("")



# INFORME SEU CPF

col1, col2, col3 = st.columns([3, 1, 3])    

# Criar um campo de input para CPF
cpf_input = col2.text_input("Informe seu CPF", max_chars=14, placeholder="000.000.000-00")

# Função para validar CPF
def validar_cpf(cpf):
    """Verifica se o CPF tem o formato correto."""
    padrao = r"^\d{3}\.\d{3}\.\d{3}-\d{2}$"
    return re.match(padrao, cpf)

# Exibir mensagem de erro caso o CPF esteja inválido
if cpf_input:
    if not validar_cpf(cpf_input):
        st.error("CPF inválido! Use o formato 000.000.000-00")
    else:
        st.success("CPF válido!")






# st.title("Formulário")

# nomeCompleto = "Renato Verdadeiro"

# # URL do seu formulário JotForm (substitua pela sua URL real)
# jotform_url = f"https://form.jotform.com/241803741227654?nomeCompleto={nomeCompleto}"

# # Exibir o iframe
# st.components.v1.iframe(jotform_url, width=None, height=3450, scrolling=True)

