
import streamlit as st

# Defina o CPF correto
CPF_CORRETO = "11111111111"  # CPF de exemplo


# CONFIGURAÇÕES DO STREAMLIT
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

# Espaçamentos
st.write("")
st.write("")
st.write("")
st.write("")

# Função para verificar o CPF
def check_cpf(cpf_input):
    # Remover pontos e traços para considerar apenas os números
    cpf_numeros = ''.join(filter(str.isdigit, cpf_input))
    
    # Verificar se o CPF tem exatamente 11 números
    if len(cpf_numeros) == 11:
        # Verificar se o CPF é o correto
        if cpf_numeros == CPF_CORRETO:
            return True
        else:
            return False
    else:
        return None  # Retorna None se o CPF não for válido

# Página de login
def pagina_login():
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
    col1, col2, col3 = st.columns([5, 2, 5])    

    # Solicita o CPF
    cpf_input = col2.text_input("Digite seu CPF", placeholder="000.000.000-00")

    if col2.button("Entrar"):
        # Verificar o CPF
        resultado = check_cpf(cpf_input)
        
        if resultado is True:
            st.session_state.logged_in = True  # Marca que o usuário está logado
            st.rerun()  # Atualiza a página
        else:
            col2.error("CPF incorreto")
        # else:
        #     col2.error("CPF inválido! O CPF deve ter exatamente 11 números.")

# Página após o login
def home_page():
    st.title("Página Principal")
    st.write("Bem-vindo ao sistema! Você está logado com sucesso.")

# NAVEGAÇÃO DE PÁGINAS
# Verifica se o usuário já está logado
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False  # Define o estado de login como falso inicialmente

# Exibe a página de login ou a página principal, dependendo do estado de login
if st.session_state.logged_in:
    home_page()  # Página após login
else:
    pagina_login()  # Página de login



# import streamlit as st

# # Defina o CPF correto
# CPF_CORRETO = "11111111111"  # CPF de exemplo



# # CONFIGURAÇÕES DO STREAMLIT

# st.set_page_config(layout="wide")  # Define o layout para ocupar toda a largura

# # CSS para reduzir o espaço no topo da página
# st.markdown(
#     """
#     <style>
#         .block-container {
#             padding-top: 3rem !important; /* Remove espaço superior */
#         }
#     </style>
#     """,
#     unsafe_allow_html=True
# )




# # LOGO

# logo_url = "https://ispn.org.br/site/wp-content/uploads/2021/04/logo_ISPN_2021.png"

# # Usando HTML para centralizar a imagem
# st.markdown(
#     f"""
#     <div style="text-align: center;">
#         <img src="{logo_url}" width="250">
#     </div>
#     """,
#     unsafe_allow_html=True
# )


# st.write("")
# st.write("")
# st.write("")
# st.write("")




# # Função para verificar o CPF
# def check_cpf(cpf):
#     return cpf == CPF_CORRETO


# # Página de login
# def pagina_login():
#     # Título
#     st.markdown(
#         """
#         <div style="text-align: center;">
#             <h2>Gestor de Viagens do ISPN</h2>
#         </div>
#         """,
#         unsafe_allow_html=True
#     )


#     st.write("")
#     st.write("")
#     st.write("")



#     # INFORME SEU CPF

#     col1, col2, col3 = st.columns([5, 2, 5])    

#     # Solicita o CPF
#     cpf = col2.text_input("Digite seu CPF", placeholder="000.000.000-00")

#     if col2.button("Entrar"):
#         if check_cpf(cpf):
#             st.session_state.logged_in = True  # Marca que o usuário está logado
#             st.rerun()
#         else:
#             col2.error("CPF incorreto")


# # Página após o login
# def home_page():
#     st.title("Página Principal")
#     st.write("Bem-vindo ao sistema! Você está logado com sucesso.")




# # NAVEGAÇÃO DE PÁGINAS

# # Verifica se o usuário já está logado
# if "logged_in" not in st.session_state:
#     st.session_state.logged_in = False  # Define o estado de login como falso inicialmente

# # Exibe a página de login ou a página principal, dependendo do estado de login
# if st.session_state.logged_in:
#     home_page()  # Página após login
# else:
#     pagina_login()  # Página de login





# st.title("Formulário")

# nomeCompleto = "Renato Verdadeiro"

# # URL do seu formulário JotForm (substitua pela sua URL real)
# jotform_url = f"https://form.jotform.com/241803741227654?nomeCompleto={nomeCompleto}"

# # Exibir o iframe
# st.components.v1.iframe(jotform_url, width=None, height=3450, scrolling=True)

