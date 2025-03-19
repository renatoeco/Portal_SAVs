
import streamlit as st
import pandas as pd
from pymongo import MongoClient
from datetime import date
import re

import gspread
from google.oauth2.service_account import Credentials



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
# CONEXÃO COM GOOGLE SHEETS
# ##################################################################

# Escopo necessário para acessar os dados do Google Sheets
scope = [
    "https://www.googleapis.com/auth/spreadsheets"
]

# Autenticação usando a conta de serviço
creds = Credentials.from_service_account_file("/home/renato/Projetos_Python/Portal_SAVs/credentials.json", scopes=scope)
client = gspread.authorize(creds)

# ID da planilha
sheet_id = st.secrets.links.id_sheet_savs_int



# ##################################################################
# FUNÇÕES AUXILIARES
# ##################################################################



# Função para transformar o itinerário em uma lista de dicionários
def parse_itinerario(itinerario_texto):

    viagens = []
    
    # Quebrar o texto pela quebra de linha
    trechos = itinerario_texto.splitlines()


    for trecho in trechos:
        partes = trecho.split(", ")  # Separar cada informação pelo padrão ", "
        viagem = {}

        for parte in partes:
            chave_valor = parte.split(": ", 1)  # Divide apenas na primeira ocorrência de ": "
            if len(chave_valor) == 2:
                chave, valor = chave_valor
                viagem[chave.strip()] = valor.strip()  # Adiciona ao dicionário

        viagens.append(viagem)

    return viagens

# Função para transformar as diarias em uma lista de dicionários
def parse_diarias(diarias_texto):
    diarias = []

    # Quebrar o texto pela quebra de linha
    linhas = diarias_texto.splitlines()

    for linha in linhas:
        partes = linha.split(", ")  # Separar cada informação pelo padrão ", "
        diaria = {}

        for parte in partes:
            chave_valor = parte.split(": ", 1)  # Divide apenas na primeira ocorrência de ": "
            if len(chave_valor) == 2:
                chave, valor = chave_valor
                diaria[chave.strip()] = valor.strip()  # Adiciona ao dicionário

        diarias.append(diaria)

    return diarias



# Função para mostrar os detalhes da SAV no diálogo
@st.dialog("Detalhes da Viagem", width='large')
def mostrar_detalhes_sav(row):

    # TRATAMENTO DO ITINERÁRIO
    # Transformar o itinerário em uma lista de dicionários
    viagens = parse_itinerario(row["Itinerário:"])
    # Criar um DataFrame a partir do dicionário
    df_trechos = pd.DataFrame(viagens)
    # Substituir os campos com None por ""
    df_trechos.fillna("", inplace=True)
    # Renomear colunas
    df_trechos.rename(columns={"Tipo de transporte": "Transporte", "Horário de preferência": "Horário"}, inplace=True)


    # TRATAMENTO DAS DIÁRIAS
    # Transformar as diárias em uma lista de dicionários
    diarias = parse_diarias(row["Diárias"])
    # Criar um DataFrame a partir da lista de dicionários
    df_diarias = pd.DataFrame(diarias)
    # Substituir os campos com None por ""
    df_diarias.fillna("", inplace=True)


    # TRATAMENTO DO LINK DE EDIÇÃO
    sumbission_id = row["Submission ID"]
    link_edicao = f"https://www.jotform.com/edit/{sumbission_id}"

    col1, col2, col3 = st.columns([1, 1, 1])

    with col3.popover("Editar a SAV", icon=":material/edit:", use_container_width=True):
        st.markdown(f"<a href='{link_edicao}' target='_blank'>Clique aqui para editar a SAV</a>", unsafe_allow_html=True)


    # INFORMAÇÕES
    st.write(f"**Código:** {row['Código da viagem:']}")
    st.write(f"**Data da solicitação:** {row['Submission Date']}")
    st.write(f"**Objetivo:** {row['Descrição do objetivo da viagem:']}")
    st.write(f"**Fonte de recurso:** {row['Qual é a fonte do recurso?']}")

    # Exibir os detalhes do itinerário como tabela
    st.write("**Itinerário:**")
    st.dataframe(df_trechos, use_container_width=True, hide_index=True)

    # Exibir os detalhes das diárias como tabela
    st.write("**Diárias:**")
    st.dataframe(df_diarias, use_container_width=False, hide_index=True)

    st.write(f"**Custo pago pelo anfitrião:** {row['A viagem tem algum custo pago pelo anfitrião?']}")
    st.write(f"**É necessária locação de veículo?** {row['Será necessário locação de veículo?']}")
    st.write(f"**Tipo de veículo:** {row['Descreva o tipo de veículo desejado:']}")
    st.write(f"**Observações:** {row['Observações gerais:']}")
    # st.write(f"**Link para edição:** {link_edicao}")

    st.write('')




@st.dialog("Detalhes do Relatório", width='large')
def mostrar_detalhes_rvs(row, df_rvss):

    # Selecionando o relatório a partir do código da SAV
    relatorio = df_rvss[df_rvss["Código da viagem:"].str.upper() == row["Código da viagem:"].upper()].iloc[0]




    # TRATAMENTO DO LINK DE EDIÇÃO
    sumbission_id = relatorio["Submission ID"]
    link_edicao = f"https://www.jotform.com/edit/{sumbission_id}"

    col1, col2, col3 = st.columns([1, 1, 1])

    with col3.popover("Editar o Relatório", icon=":material/edit:", use_container_width=True):
        st.markdown(f"<a href='{link_edicao}' target='_blank'>Clique aqui para editar o Relatório</a>", unsafe_allow_html=True)



    # INFORMAÇÕES
    st.write(f"**Código da viagem:** {row['Código da viagem:']}")   # Pega o código direto da SAV

    st.write(f"**Data do envio do relatório:** {relatorio['Submission Date']}")
    st.write(f"**Fonte de recurso:** {relatorio['Qual é a fonte do recurso?']}")
    st.write(f"**Período da viagem:** {relatorio['Período da viagem:']}")
    st.write(f"**Cidade(s) de destino:** {relatorio['Cidade(s) de destino:']}")
    
    
    st.write(f"**Modalidade:** {relatorio['Modalidade:']}")
    st.write(f"**Número de pernoites:** {relatorio['Número de pernoites:']}")
    st.write(f"**Modo de transporte até o destino:** {relatorio['Modo de transporte até o destino:']}")
    st.write(f"**Valor gasto com transporte no destino:** {relatorio['Valor gasto com transporte no destino (R$):']}")
    st.write(f"**Valor das diárias recebidas:** {relatorio['Valor das diárias recebidas (R$):']}")
    st.write(f"**Itens de despesa cobertos pelo anfitrião (descrição e valor):** {relatorio['Itens de despesa cobertos pelo anfitrião (descrição e valor):']}")
    st.write(f"**Atividades realizadas na viagem:** {relatorio['Descreva as atividades realizadas na viagem:']}")
    st.write(f"**Principais Resultados / Produtos:** {relatorio['Principais Resultados / Produtos:']}")

    # Convertendo a string em uma lista de URLs
    lista_fotos = relatorio['Inclua 2 fotos da viagem:'].split("\n")
    # Criando colunas dinamicamente com base na quantidade de fotos
    num_fotos = len(lista_fotos)
    cols = st.columns(num_fotos)  # Cria colunas iguais ao número de fotos
    # Exibindo cada foto em uma coluna
    for idx, (col, foto) in enumerate(zip(cols, lista_fotos), start=1):
        with col:
            st.image(foto)


    st.write(f"**Documentos anexados:** {relatorio['Faça upload dos anexos:']}")
    st.write(f"**Despesas cobertas pelo anfitrião:** {relatorio['Despesas cobertas pelo anfitrião (descrição e valor):']}")
    # st.write(f"**Submission ID:** {relatorio['Submission ID']}")


    st.write(f"**Observações:** {relatorio['Observações gerais:']}")

    st.markdown(f"**Observações:** {relatorio['Observações gerais:']}", unsafe_allow_html=True)



    # # st.write(f"**Link para edição:** {link_edicao}")

    st.write('')








# Carregar usuários internos no banco de dados ------------------------------
def carregar_internos():
    
    # criar um dataframe com os usuários internos
    df_usuarios_internos = pd.DataFrame(list(banco_de_dados["usuarios_internos"].find()))
    
    # Considerar apenas os números da coluna cpf
    df_usuarios_internos["cpf"] = df_usuarios_internos["cpf"].astype(str).str.replace(r"\D", "", regex=True)

    return df_usuarios_internos



# Cerregar usuários externos no banco de dados ------------------------------
def carregar_externos():
    # criar um dataframe com os usuários internos
    df_usuarios_externos = pd.DataFrame(list(banco_de_dados["usuarios_externos"].find()))
    
    # Considerar apenas os números da coluna cpf
    df_usuarios_externos["cpf"] = df_usuarios_externos["cpf"].astype(str).str.replace(r"\D", "", regex=True)

    return df_usuarios_externos


# Carregar SAVs internas no google sheets ------------------------------
@st.cache_data
def carregar_savs_int():

    sheet = client.open_by_key(sheet_id)

    # values_savs = sheet.worksheet("TESTE RENATO SAVs").get_all_values()
    values_savs = sheet.worksheet("Recebimento de SAVs").get_all_values()

    # Criar DataFrame de SAVs. A primeira linha é usada como cabeçalho
    df_savs = pd.DataFrame(values_savs[1:], columns=values_savs[0])

    # Converter as colunas de data para datetime
    df_savs["Submission Date"] = pd.to_datetime(df_savs["Submission Date"])  # Garantir que é datetime
    df_savs["Submission Date"] = df_savs["Submission Date"].dt.strftime("%d/%m/%Y")  # Converter para string no formato brasileiro

    # Filtar SAVs com o prefixo "SAV-"
    df_savs = df_savs[df_savs['Código da viagem:'].str.upper().str.startswith('SAV-')]
    # df_savs = df_savs[df_savs['Código da viagem:'].str.lower().str.startswith('sav-')]

    # st.write(df_savs)

    return df_savs


# Carregar RVSs internos no google sheets ------------------------------
@st.cache_data
def carregar_rvss_int():

    sheet = client.open_by_key(sheet_id)

    # values_rvss = sheet.worksheet("TESTE RENATO SAVs").get_all_values()
    values_rvss = sheet.worksheet("Recebimento de RVSs").get_all_values()

    # Criar DataFrame de RVSs. A primeira linha é usada como cabeçalho
    df_rvss = pd.DataFrame(values_rvss[1:], columns=values_rvss[0])

    # Filtar SAVs com o prefixo "SAV-"
    df_rvss = df_rvss[df_rvss['Código da viagem:'].str.upper().str.startswith('SAV-')]
    # df_rvss = df_rvss[df_rvss['Código da viagem:'].str.lower().str.startswith('sav-')]

    # Converter as colunas de data para datetime
    df_rvss["Submission Date"] = pd.to_datetime(df_rvss["Submission Date"])  # Garantir que é datetime
    df_rvss["Submission Date"] = df_rvss["Submission Date"].dt.strftime("%d/%m/%Y")  # Converter para string no formato brasileiro


    return df_rvss







# Função para checar o CPF no login ------------------------------
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
        df_usuarios_internos = carregar_internos()
        
        # Verificar se o CPF existe nos usuários internos
        usuario = df_usuarios_internos[df_usuarios_internos["cpf"] == cpf_numeros].iloc[0].to_dict()
      
        if usuario:
            st.session_state.tipo_usuario = "interno"
            st.session_state.usuario = usuario  # Salva o usuário no session_state
            return True  # Retorna imediatamente, sem carregar usuários externos


        # Se não for interno, busca nos usuários externos
        df_usuarios_externos = carregar_externos()
      
        # Verificar se o CPF existe nos usuários externos
        usuario = df_usuarios_externos[df_usuarios_externos["cpf"] == cpf_numeros].iloc[0].to_dict()
        
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

    df_savs_int = carregar_savs_int()
    df_savs_int = df_savs_int.replace({'\$': '\\$'}, regex=True)


    df_rvss_int = carregar_rvss_int()
    df_rvss_int = df_rvss_int.replace({'\$': '\\$'}, regex=True)


    # USUÁRIO INTERNO ---------------------------

    if st.session_state.tipo_usuario == "interno":
        
        # Captura o usuário do session_state para a variável usuario
        usuario = st.session_state.usuario
     



        col1, col2 = st.columns([8, 1])

        col1.markdown(
            f"""
            <div>
                <h3 style="color: gray;">Olá {usuario['nome_completo'].split(' ')[0]}</h3>
            </div>
            """,
            unsafe_allow_html=True
        )

        if col2.button("Atualizar", icon=":material/refresh:", use_container_width=True):
            st.session_state.status_usuario = ""
            st.cache_data.clear()
            st.rerun()  
            
            
        st.write("")

        # Abas da home
        minhas_viagens, nova_sav = st.tabs([":material/flight_takeoff: Minhas Viagens", ":material/add: Nova Solicitação de Viagem"])


        # ABA MINHAS VIAGENS

        with minhas_viagens:
            df_savs_int = carregar_savs_int()
            df_rvss_int = carregar_rvss_int()

            # Limpar a coluna CPF: quero apenas os números
            df_savs_int['CPF:'] = df_savs_int['CPF:'].str.replace(r'[^\d]+', '', regex=True)

            # Filtar SAVs com o CPF do usuário
            df_savs_int = df_savs_int[df_savs_int['CPF:'].astype(str) == str(usuario['cpf'])]

            # Capturar a data da viagem
            df_savs_int['Data da viagem:'] = df_savs_int['Itinerário:'].str[6:16].replace('-', '/', regex=True)

            # Capturar todos os destinos
            # Expressão regular para capturar o que está entre "Cidade de chegada: " e ","
            destinos = r'Cidade de chegada: (.*?)(?:,|$)'
            # Aplicar a regex para cada linha da coluna
            df_savs_int["Destinos:"] = df_savs_int["Itinerário:"].apply(lambda x: ' > '.join(re.findall(destinos, x)))

        
            # Criar cabeçalho da "tabela"
            col1, col2, col3, col4, col5 = st.columns([2, 2, 7, 2, 2])

            col1.write('**Código da viagem**')
            col2.write('**Data da viagem**')
            col3.write('**Itinerário**')
            # col4.write('**SAVs**')
            # col5.write('**Relatórios**')


            # Iniciar a variável na session_state que vai identificar se o usuário está impedido ou não de enviar relatório (se tem algum pendente)
            st.session_state.status_usuario = ""

            # Iterar sobre a lista de viagens
            for index, row in df_savs_int[::-1].iterrows():

                # Preparar o link personalizado para o relatório -----------------------------------------------------

                # Extrair cidade(s) de destino
                # Transformar o itinerário em uma lista de dicionários
                trechos = parse_itinerario(row["Itinerário:"])

                # Pegando a primeira e a última data
                data_inicial = trechos[0]["Data"]
                data_final = trechos[-1]["Data"]
                periodo_viagem = f"{data_inicial} a {data_final}".replace('-', '/')

                # Extraindo todas as "Cidade de chegada" e concatenando com vírgula
                cidades_chegada = [viagem["Cidade de chegada"] for viagem in trechos]
                destinos = ", ".join(cidades_chegada)

                # URL do formulário de RVS interno
                jotform_rvs_interno_url = f"{st.secrets['links']['url_rvs_int']}?codigoDa={row['Código da viagem:']}&qualE={row['Qual é a fonte do recurso?']}&nomeDo={row['Nome completo:']}&email={row['E-mail:']}&cidadesDe={destinos}&periodoDa={periodo_viagem}"

                # ----------------------------------------------------------------------------------------------------- 

                # Conteúdo da lista de viagens

                col1, col2, col3, col4, col5 = st.columns([2, 2, 7, 2, 2])
                
                col1.write(row['Código da viagem:'])
                col2.write(row['Data da viagem:'])
                col3.write(row['Destinos:'])
                col4.button('Detalhes', key=f"detalhes_{index}", on_click=mostrar_detalhes_sav, args=(row,), use_container_width=True, icon=":material/info:")
                


                # Botão dinâmico sobre o relatório --------------------------------------------

                # Verificar se o relatório foi entregue. Procura se tem o código da SAV em algum relatório 
                if row['Código da viagem:'].upper() in df_rvss_int['Código da viagem:'].str.upper().values:

                    status_relatorio = "entregue"

                # Se não tem nenhum relatório com esse código de SAV
                else:
                    status_relatorio = "pendente"

                    # Se a data_final da viagem menor do que hoje, o usuário está impedido
                    if pd.to_datetime(data_final, dayfirst=True).timestamp() < pd.to_datetime(date.today()).timestamp():
                    
                        st.session_state.status_usuario = "impedido"


                # Se o relatório foi entregue, vê o relatório  
                if status_relatorio == "entregue":
                    col5.button('Relatório entregue', key=f"entregue_{index}", on_click=mostrar_detalhes_rvs, args=(row, df_rvss_int), use_container_width=True, icon=":material/check:", type="primary")
                
                # Se não foi entregue, botão para enviar
                # else:
                if status_relatorio == "pendente":
                    with col5.popover('Enviar relatório', use_container_width=True, icon=":material/description:"):
                        st.markdown(f"<a href='{jotform_rvs_interno_url}' target='_blank'>Clique aqui para enviar o relatório</a>", unsafe_allow_html=True)


                st.divider()  # Separador entre cada linha da tabela




        # ABA DE NOVA SOLICITAÇÃO
        
        with nova_sav:

            if st.session_state.status_usuario == "impedido":
                st.write('')
                st.write('')
                st.write('')


                st.markdown("""
                    <div style="text-align: center;">
                        <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded" rel="stylesheet">
                        <span class="material-symbols-rounded" style="font-size:58px; color:red;">
                            warning
                        </span>
                    </div>
                """, unsafe_allow_html=True)

                st.write('')


                st.markdown("<div style='text-align: center; color: red; font-size: 20px;'>Você precisa enviar os <strong>relatórios pendentes</strong> antes de solicitar uma nova viagem.</div>", unsafe_allow_html=True)

            else:

                # URL do formulário de SAV interna
                jotform_sav_interno_url = f"{st.secrets['links']['url_sav_int']}?nomeCompleto={usuario['nome_completo']}&dataDe={usuario['data_nascimento']}'&genero={usuario['genero']}&rg={usuario['rg']}&cpf={usuario['cpf']}&telefone={usuario['telefone']}&email={usuario['email']}&emailDoa={usuario['email_coordenador']}&banco={usuario['banco']['nome']}&agencia={usuario['banco']['agencia']}&conta={usuario['banco']['conta']}"

                # Exibir o iframe
                st.components.v1.iframe(jotform_sav_interno_url, width=None, height=3550)







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





