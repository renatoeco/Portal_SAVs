
import streamlit as st
from pymongo import MongoClient
from datetime import datetime



# ##################################################################
# CONFIGURAÇÕES DA INTERFACE
# ##################################################################

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




# ##################################################################
# LOGO
# ##################################################################

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
st.write("")
st.write("")


# ##################################################################
# CONEXÃO COM O BANCO DE DADOS MONGO
# ##################################################################


# # Conectar Mongo Atlas
# # Obtém a string de conexeão do st.secrets
# MONGODB_URI = st.secrets['mongo_atlas']['MONGO_URI']
# # Cliente do Mongo Atlas (nuvem)
# cliente = MongoClient(MONGODB_URI)

# Conectar ao MongoDB local
cliente = MongoClient('mongodb://localhost:27017/')  # Cria uma conexão com o banco de dados MongoDB
banco_de_dados = cliente["plataforma_sav"]  # Seleciona o banco de dados








# ##################################################################
# FUNÇÕES AUXILIARES
# ##################################################################


# Cerregar usuários internos no banco de dados ------------------------------
def carregar_internos():
    return banco_de_dados["usuarios_internos"]  # Seleciona a coleção


# Cerregar usuários externos no banco de dados ------------------------------
def carregar_externos():
    return banco_de_dados["usuarios_externos"]  # Seleciona a coleção




def check_cpf(cpf_input):
    # Remover pontos e traços, considerando apenas os números
    cpf_numeros = ''.join(filter(str.isdigit, cpf_input))

    # Inicializa session_state se não existir
    if "tipo_usuario" not in st.session_state:
        st.session_state.tipo_usuario = None
    if "cpf_inserido" not in st.session_state:
        st.session_state.cpf_inserido = None
    if "usuario" not in st.session_state:
        st.session_state.usuario = None

    # Verifica se o CPF tem exatamente 11 dígitos
    if len(cpf_numeros) == 11:
        st.session_state.cpf_inserido = cpf_numeros  # Atualiza CPF no session state

        # Busca primeiro nos usuários internos
        usuarios_internos = carregar_internos()
        usuario = usuarios_internos.find_one({"cpf": cpf_numeros})
        if usuario:
            st.session_state.tipo_usuario = "interno"
            st.session_state.usuario = usuario  # Salva o usuário no session_state
            return True  # Retorna imediatamente, sem carregar usuários externos

        # Se não for interno, busca nos usuários externos
        usuarios_externos = carregar_externos()
        usuario = usuarios_externos.find_one({"cpf": cpf_numeros})
        if usuario:
            st.session_state.tipo_usuario = "externo"
            st.session_state.usuario = usuario  # Salva o usuário no session_state
        else:
            st.session_state.tipo_usuario = "novo"
            st.session_state.usuario = None  # Não encontrou usuário

        return True  # Retorna após verificar os externos e novo

    else:
        return False  # CPF inválido





# ##################################################################
# Página de login
# ##################################################################


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
    st.write("")
    st.write("")


    # INFORME SEU CPF
    col1, col2, col3 = st.columns([5, 2, 5])    

    # Solicita o CPF
    with col2.form("form_login", border=False):
        cpf_input = st.text_input("Digite seu CPF", placeholder="000.000.000-00")
        if st.form_submit_button("Entrar"):
            # Verificar o CPF
            resultado = check_cpf(cpf_input)
            
            if resultado is True:
                st.session_state.logged_in = True  # Marca que o usuário está logado
                st.rerun()  # Atualiza a página
            else:
                st.error("CPF inválido.")
        # else:
        #     col2.error("CPF inválido! O CPF deve ter exatamente 11 números.")



# ##################################################################
# PÁGINA DO USUÁRIO INTERNO
# ##################################################################


def home_page():

    # USUÁRIO INTERNO ---------------------------

    if st.session_state.tipo_usuario == "interno":
        
        # Captura o usuário do session_state para a variável
        usuario = st.session_state.usuario
     

        st.sidebar.write("Usuário encontrado:", usuario)


    st.markdown(
        f"""
        <div>
            <h3 style="color: gray;">Olá {usuario['nome_completo'].split(' ')[0]}</h3>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write("")

    minhas_viagens, nova_sav = st.tabs(["Minhas Viagens", "Nova Solicitação de Viagem"])

    with minhas_viagens:
        st.write("Minhas Viagens")

    with nova_sav:

        # URL do seu formulário JotForm
        jotform_url = f"{st.secrets['links']['url_form_int']}?nomeCompleto={usuario['nome_completo']}&dataDe={usuario['data_nascimento']}'&genero={usuario['genero']}&rg={usuario['rg']}&cpf={usuario['cpf']}&telefone={usuario['telefone']}&email={usuario['email']}&emailDoa={usuario['email_coordenador']}&banco={usuario['banco']['nome']}&agencia={usuario['banco']['agencia']}&conta={usuario['banco']['conta']}"

        # Exibir o iframe
        st.components.v1.iframe(jotform_url, width=None, height=3550)







# ##################################################################
# NAVEGAÇÃO DE PÁGINAS
# ##################################################################



# Verifica se o usuário já está logado
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False  # Define o estado de login como falso inicialmente

# Exibe a página de login ou a página principal, dependendo do estado de login
if st.session_state.logged_in:
    home_page()  # Página após login
else:
    pagina_login()  # Página de login





