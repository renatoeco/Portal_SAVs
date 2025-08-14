import streamlit as st
import pandas as pd
from pymongo import MongoClient
from datetime import date
import re
import random
import smtplib
from email.mime.text import MIMEText
import time
from urllib.parse import quote


import gspread
from google.oauth2.service_account import Credentials



# ##################################################################
# CONFIGURAÇÕES DA INTERFACE
# ##################################################################

st.set_page_config(
    layout="wide", 
    page_title="Portal de Viagens do ISPN",
    page_icon="imagens/logo_ISPN_favicon.png"  # Define o favicon
    )

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


# Conectar Mongo Atlas
# Obtém a string de conexeão do st.secrets
MONGODB_URI = st.secrets['senhas']['string_conexao']
# Cliente do Mongo Atlas (nuvem)
cliente = MongoClient(MONGODB_URI)

# Conectar ao MongoDB local
# cliente = MongoClient('mongodb://localhost:27017/')  # Cria uma conexão com o banco de dados MongoDB

banco_de_dados = cliente["plataforma_sav"]  # Seleciona o banco de dados


# ##################################################################
# CONEXÃO COM GOOGLE SHEETS
# ##################################################################

# Escopo necessário para acessar os dados do Google Sheets
scope = [
    "https://www.googleapis.com/auth/spreadsheets"
]

# Autenticação usando a conta de serviço

# Ler credenciais do st.secrets
creds_dict = st.secrets["credentials_drive"]
# Criar credenciais do Google usando os dados do st.secrets
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)

client = gspread.authorize(creds)

# ID da planilha
sheet_id = st.secrets.ids.id_planilha_recebimento



# ##################################################################
# FUNÇÕES AUXILIARES
# ##################################################################

# Faz o encode de valores para URL, pra usar em URL dinâmicas
def encode_params(params):
    return "&".join(f"{k}={quote(str(v), safe='')}" for k, v in params.items())


# Tratamento quando não há todos os dados da pessoa no BD
def safe_get(dicionario, chave, default=""):
    # Obtém o valor da chave no dicionário, ou um valor padrão se a chave não existir
    valor = dicionario.get(chave, default)
    
    # Verifica se o valor é NaN (Not a Number) usando pandas.isna()
    # Se for NaN, retorna uma string vazia
    # Caso contrário, retorna o valor normalmente
    return "" if pd.isna(valor) else valor


# Função para enviar e-mail com código de verificação
def enviar_email(destinatario, codigo):
    remetente = st.secrets["senhas"]["endereco_email"]
    senha = st.secrets["senhas"]["senha_email"]

    assunto = f"Código de Verificação: {codigo}"

    corpo = f"""
    <html>
        <body>
            <h2>Portal de Viagens do ISPN</h2>
            <p style='font-size: 1.3em;'>
                Seu código de verificação é: <strong>{codigo}</strong>
            </p>
        </body>
    </html>
    """

    msg = MIMEText(corpo, "html")  # Especifica que o conteúdo é HTML
    msg["Subject"] = assunto
    msg["From"] = remetente
    msg["To"] = destinatario

    # Tenta enviar o e-mail com o código de verificação
    try:
        # Conecta ao servidor de e-mail do Gmail
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            # Faz login com o e-mail e senha do remetente
            server.login(remetente, senha)
            # Envia o e-mail
            server.sendmail(remetente, destinatario, msg.as_string())
        # Se der certo, retorna True
        return True
    except Exception as e:
        # Se der errado, exibe o erro e retorna False
        st.error(f"Erro ao enviar e-mail: {e}")
        return False



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


# !!!!!!!!!!!!!!!!!!!!!!
    if st.session_state.tipo_usuario == "interno":
        # TRATAMENTO DAS DIÁRIAS
        # Transformar as diárias em uma lista de dicionários
        diarias = parse_diarias(row["Diárias"])
        # Criar um DataFrame a partir da lista de dicionários
        df_diarias = pd.DataFrame(diarias)
        # Substituir os campos com None por ""
        df_diarias.fillna("", inplace=True)


    # TRATAMENTO DO LINK DE EDIÇÃO
    sumbission_id = row["Submission ID"]

    usuario = st.session_state.usuario

    link_edicao = f"https://www.jotform.com/edit/{sumbission_id}"

    col1, col2, col3 = st.columns([1, 1, 1])


# !!!!!!!!!!!!!!!!!!!!!!
    # Só interno
    # Botão de editar
    if st.session_state.tipo_usuario == "interno":
        col3.link_button("Editar a Solicitação", icon=":material/edit:", use_container_width=True, url=link_edicao)


    # INFORMAÇÕES
    # Se a SAV for para terceiros, mostra o nome do viajante
    if row["Código da viagem:"].startswith("TRC"):
        st.write(f"**Nome do(a) viajante:** {row['Nome do(a) viajante:']}")
    st.write(f"**Código da viagem:** {row['Código da viagem:']}")
    st.write(f"**Data da solicitação:** {row['Submission Date']}")
    st.write(f"**Objetivo:** {row['Descrição do objetivo da viagem:']}")
    st.write(f"**Fonte de recurso:** {row['Qual é a fonte do recurso?']}")

# !!!!!!!!!!!!!!!!!!!!!!
    # Só externo
    if st.session_state.tipo_usuario == "externo":
        # Ponto focal
        st.write(f"**Ponto focal:** {row['Ponto focal:']}")


    # Exibir os detalhes do itinerário como tabela
    st.write("**Itinerário:**")
    st.dataframe(df_trechos, use_container_width=True, hide_index=True)

# !!!!!!!!!!!!!!!!!!!!!!
    # Só interno
    if st.session_state.tipo_usuario == "interno":
        # Exibir os detalhes das diárias como tabela
        st.write("**Diárias:**")
        st.dataframe(df_diarias, use_container_width=False, hide_index=True)

        st.write(f"**Custo pago pelo anfitrião:** {row['A viagem tem algum custo pago pelo anfitrião?']}")
    

    st.write(f"**Será necessário um veículo?** {row['Será necessário locação de veículo?']}")

    # Container para botar uma borda em torno das informações do veículo alugado ou do ISPN
    veiculo = st.container(border=True)

    if row.get('Um veículo alugado ou um veículo do ISPN em Santa Inês?'):
        veiculo.write(row['Um veículo alugado ou um veículo do ISPN em Santa Inês?'])


    # VEÍCULO ALUGADO
    if row.get('Descreva o tipo de veículo desejado:'):
        veiculo.write(row['Descreva o tipo de veículo desejado:'])

    if row.get('Detalhe os locais e horários de retirada e retorno do veículo alugado:'):
        veiculo.write(row['Detalhe os locais e horários de retirada e retorno do veículo alugado:'])

    # VEÍCULO DO ISPN
    if row.get('Escolha o veículo:'):
        veiculo.write(row['Escolha o veículo:'])

    if row.get('Quais são os horários previstos de retirada e retorno do veículo?'):
        veiculo.write(row['Quais são os horários previstos de retirada e retorno do veículo?'])


    st.write(f"**Observações:** {row['Observações gerais:']}")

    st.write('')


@st.dialog("Detalhes do Relatório", width='large')
def mostrar_detalhes_rvs(row, df_rvss):

    # Selecionando o relatório a partir do código da SAV
    relatorio = df_rvss[df_rvss["Código da viagem:"].str.upper() == row["Código da viagem:"].upper()].iloc[0]

    # TRATAMENTO DO LINK DE EDIÇÃO
    sumbission_id = relatorio["Submission ID"]
    link_edicao = f"https://www.jotform.com/edit/{sumbission_id}"


    # Botão para editar o relatório
    col1, col2, col3 = st.columns([1, 1, 1])
    col3.link_button("Editar o Relatório", icon=":material/edit:", use_container_width=True, url=link_edicao)

    # INFORMAÇÕES
    if row["Código da viagem:"].startswith("TRC"):
        st.write(f"**Nome do(a) viajante:** {row['Nome do(a) viajante:']}")
    st.write(f"**Código da viagem:** {row['Código da viagem:']}")   # Pega o código direto da SAV
    st.write(f"**Data do envio do relatório:** {relatorio['Submission Date']}")
    st.write(f"**Fonte de recurso:** {relatorio['Qual é a fonte do recurso?']}")
    st.write(f"**Período da viagem:** {relatorio['Período da viagem:']}")
    st.write(f"**Cidade(s) de destino:** {relatorio['Cidade(s) de destino:']}")

# !!!!!!!!!!!!!!!!!!!
    if st.session_state.tipo_usuario == "interno":
        
        try: # Não tem no relatório de terceiros.
            st.write(f"**Modalidade:** {relatorio['Modalidade:']}")
        except:
            pass

        try: # Não tem no relatório de terceiros.
            st.write(f"**Modo de transporte até o destino:** {relatorio['Modo de transporte até o destino:']}")
        except:
            pass

        try: # Não tem no relatório de terceiros.
            st.write(f"**Despesas cobertas pelo anfitrião (descrição e valor):** {relatorio['Despesas cobertas pelo anfitrião (descrição e valor):']}")
        except:
            pass

    st.write(f"**Número de pernoites:** {relatorio['Número de pernoites:']}")
    st.write(f"**Valor das diárias recebidas:** {relatorio['Valor das diárias recebidas (R$):']}")
    st.write(f"**Valor gasto com transporte no destino:** {relatorio['Valor gasto com transporte no destino (R$):']}")
    st.write(f"**Atividades realizadas na viagem:** {relatorio['Descreva as atividades realizadas na viagem:']}")
    st.write(f"**Principais Resultados / Produtos:** {relatorio['Principais Resultados / Produtos:']}")

    # Fotos
    st.write("**Fotos da viagem:**")
    # Convertendo a string em uma lista de URLs
    lista_fotos = relatorio['Inclua 2 fotos da viagem:'].split("\n")
    # Criando colunas dinamicamente com base na quantidade de fotos
    num_fotos = len(lista_fotos)
    cols = st.columns(num_fotos)  # Cria colunas iguais ao número de fotos
    # Exibindo cada foto em uma coluna
    for idx, (col, foto) in enumerate(zip(cols, lista_fotos), start=1):
        with col:
            st.image(foto)

    # Anexos
    st.write("**Documentos anexados:**")
    # Fazendo o split nas quebras de linha
    url_list = relatorio['Faça upload dos anexos:'].split("\n")
    for url in reversed(url_list):
        # Obtém o nome do arquivo
        nome_arquivo = url.split("/")[-1]  
        # Mostra o link na página
        st.markdown(f'<a href="{url}" target="_blank">{nome_arquivo}</a><br>', unsafe_allow_html=True)
       
    st.write(f"**Observações:** {relatorio['Observações gerais:']}")

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
# @st.cache_data(show_spinner=False)
def carregar_savs_int():

    sheet = client.open_by_key(sheet_id)
    
    values_savs = sheet.worksheet("SAVs INTERNAS Portal").get_all_values()
    # values_savs = sheet.worksheet("TESTE RENATO SAVs").get_all_values()
    # values_savs = sheet.worksheet("Recebimento de SAVs").get_all_values()

    # Criar DataFrame de SAVs. A primeira linha é usada como cabeçalho
    df_savs = pd.DataFrame(values_savs[1:], columns=values_savs[0])

    # Converter as colunas de data para datetime
    df_savs["Submission Date"] = pd.to_datetime(df_savs["Submission Date"])  # Garantir que é datetime
    df_savs["Submission Date"] = df_savs["Submission Date"].dt.strftime("%d/%m/%Y")  # Converter para string no formato brasileiro

    # Filtar SAVs com o prefixo "SAV-"
    df_savs = df_savs[df_savs['Código da viagem:'].str.upper().str.startswith('SAV-')]

    df_savs = df_savs.replace({'\$': '\\$'}, regex=True)


    return df_savs


# Carregar RVSs internos no google sheets ------------------------------
# @st.cache_data(show_spinner=False)
def carregar_rvss_int():

    sheet = client.open_by_key(sheet_id)

    # Planilha de recebimento de RVSs internos
    values_rvss = sheet.worksheet("RVSs INTERNOS Portal").get_all_values()

    # Criar DataFrame de RVSs. A primeira linha é usada como cabeçalho
    df_rvss = pd.DataFrame(values_rvss[1:], columns=values_rvss[0])

    # Filtar SAVs com o prefixo "SAV-"
    df_rvss = df_rvss[df_rvss['Código da viagem:'].str.upper().str.startswith('SAV-')]

    # Converter as colunas de data para datetime
    df_rvss["Submission Date"] = pd.to_datetime(df_rvss["Submission Date"])  # Garantir que é datetime
    df_rvss["Submission Date"] = df_rvss["Submission Date"].dt.strftime("%d/%m/%Y")  # Converter para string no formato brasileiro

    df_rvss = df_rvss.replace({'\$': '\\$'}, regex=True)

    return df_rvss


# Carregar SAVs externas no google sheets ------------------------------
# @st.cache_data(show_spinner=False)
def carregar_savs_ext():

    # Abrir a planilha de SAVs externas
    sheet = client.open_by_key(sheet_id)

    # Ler todos os valores da planilha
    values_savs = sheet.worksheet("SAVs EXTERNAS Portal").get_all_values()

    # Criar DataFrame de SAVs. A primeira linha é usada como cabeçalho
    df_savs = pd.DataFrame(values_savs[1:], columns=values_savs[0])

    # Converter as colunas de data para datetime
    df_savs["Submission Date"] = pd.to_datetime(df_savs["Submission Date"])  # Garantir que é datetime
    df_savs["Submission Date"] = df_savs["Submission Date"].dt.strftime("%d/%m/%Y")  # Converter para string no formato brasileiro

    # Filtar SAVs com o prefixo "EXT-"
    df_savs = df_savs[df_savs['Código da viagem:'].str.upper().str.startswith('EXT-')]
   
    # Substitui o caractere $ por \$ para que o Streamlit possa exibir corretamente
    df_savs = df_savs.replace({'\$': '\\$'}, regex=True)

    # Renomeia as colunas para que tenham nomes mais legíveis
    df_savs.rename(columns={'Insira aqui os seus deslocamentos. Cada trecho em uma nova linha:': 'Itinerário:',
                            'Nome do ponto focal no ISPN (a pessoa que está convidando)': 'Ponto focal:'}, inplace=True)

    return df_savs


# Carregar RVSs externos no google sheets ------------------------------
# @st.cache_data(show_spinner=False)
def carregar_rvss_ext():

    # Abrir a planilha de RVSs externas
    sheet = client.open_by_key(sheet_id)

    # Ler todos os valores da planilha
    # values_rvss = sheet.worksheet("TESTE RENATO SAVs").get_all_values()
    values_rvss = sheet.worksheet("RVSs EXTERNOS Portal").get_all_values()

    # Criar DataFrame de RVSs. A primeira linha é usada como cabeçalho
    df_rvss = pd.DataFrame(values_rvss[1:], columns=values_rvss[0])

    # Filtar SAVs com o prefixo "EXT-"
    df_rvss = df_rvss[df_rvss['Código da viagem:'].str.upper().str.startswith('EXT-')]

    # Converter as colunas de data para datetime
    df_rvss["Submission Date"] = pd.to_datetime(df_rvss["Submission Date"])  # Garantir que é datetime
    df_rvss["Submission Date"] = df_rvss["Submission Date"].dt.strftime("%d/%m/%Y")  # Converter para string no formato brasileiro

    df_rvss = df_rvss.replace({'\$': '\\$'}, regex=True)

    return df_rvss


# Carregar SAVs de terceiros no google sheets ------------------------------
# @st.cache_data(show_spinner=False)
def carregar_savs_trc():

    # Abrir a planilha de SAVs de terceiros
    sheet = client.open_by_key(sheet_id)

    # Ler todos os valores da planilha
    values_savs = sheet.worksheet("SAVs TERCEIROS Portal").get_all_values()

    # Criar DataFrame de SAVs. A primeira linha é usada como cabeçalho
    df_savs = pd.DataFrame(values_savs[1:], columns=values_savs[0])

    # Converter as colunas de data para datetime
    df_savs["Submission Date"] = pd.to_datetime(df_savs["Submission Date"])  # Garantir que é datetime
    df_savs["Submission Date"] = df_savs["Submission Date"].dt.strftime("%d/%m/%Y")  # Converter para string no formato brasileiro

    # Filtar SAVs com o prefixo "TRC-"
    df_savs = df_savs[df_savs['Código da viagem:'].str.upper().str.startswith('TRC-')]
   
    # Substitui o caractere $ por \$ para que o Streamlit possa exibir corretamente
    df_savs = df_savs.replace({'\$': '\\$'}, regex=True)

    # Renomeia as colunas para que tenham nomes mais legíveis
    df_savs.rename(columns={'Insira aqui os deslocamentos considerando IDA e VOLTA. Cada trecho em uma nova linha:': 'Itinerário:'}, inplace=True)

    return df_savs


# Carregar RVSs externos no google sheets ------------------------------
# @st.cache_data(show_spinner=False)
def carregar_rvss_trc():

    # Abrir a planilha de RVSs externas
    sheet = client.open_by_key(sheet_id)

    # Ler todos os valores da planilha
    # values_rvss = sheet.worksheet("TESTE RENATO SAVs").get_all_values()
    values_rvss = sheet.worksheet("RVSs TERCEIROS Portal").get_all_values()

    # Criar DataFrame de RVSs. A primeira linha é usada como cabeçalho
    df_rvss_terceiros = pd.DataFrame(values_rvss[1:], columns=values_rvss[0])

    # Filtar SAVs com o prefixo "TRC-"
    df_rvss_terceiros = df_rvss_terceiros[df_rvss_terceiros['Código da viagem:'].str.upper().str.startswith('TRC-')]

    # Converter as colunas de data para datetime
    df_rvss_terceiros["Submission Date"] = pd.to_datetime(df_rvss_terceiros["Submission Date"])  # Garantir que é datetime
    df_rvss_terceiros["Submission Date"] = df_rvss_terceiros["Submission Date"].dt.strftime("%d/%m/%Y")  # Converter para string no formato brasileiro

    df_rvss_terceiros = df_rvss_terceiros.replace({'\$': '\\$'}, regex=True)

    return df_rvss_terceiros


@st.dialog("Cadastrar viajante externo", width="large")
def cadastrar_externo():
    with st.form("cadastrar_externo"):
        # Criação de duas colunas para organização dos campos no formulário
        col1, espaco, col2 = st.columns([12, 1, 12])

        # COLUNA 1

        # Campo para o nome completo
        nome_input = col1.text_input("Nome Completo")

        # Campo para o CPF
        cpf_input = col1.text_input("CPF")

        # Campo para a data de nascimento
        data_nascimento_input = col1.text_input("Data de Nascimento")

        # Campo para e-mail
        email_input = col1.text_input("E-mail")

        # COLUNA 2

        # Campo para seleção de gênero
        genero_input = col2.selectbox(
            "Gênero",
            ["", "Masculino", "Feminino", "Outro"],
        )

        # Campo para o RG e órgão emissor
        rg_input = col2.text_input("RG e órgão emissor")

        # Campo para o telefone
        telefone_input = col2.text_input("Telefone")

        # Espaço para alinhamento visual com os demais campos
        col2.markdown("<div style='height: 84px'></div>", unsafe_allow_html=True)

        # DADOS BANCÁRIOS

        # Campo para o nome do banco
        banco_nome_input = col1.text_input("Banco", value="")

        # Campo para o número da agência
        banco_agencia_input = col2.text_input("Agência", value="")

        # Campo para o número da conta
        banco_conta_input = col2.text_input("Conta", value="")

        # Campo para o tipo de conta
        banco_tipo_input = col1.selectbox(
            "Tipo de Conta", 
            ["Conta Corrente", "Conta Poupança", "Conta Salário"], 
            index=0
        )

        st.write('')


        if st.form_submit_button("Cadastrar viajante externo", icon=":material/person_add:", type="primary"):
            # Verifica se há erros nos campos
            erros = []

            # Verifica se o nome completo foi preenchido
            if not nome_input:
                erros.append("Nome completo é obrigatório.")

            # Verifica se o CPF foi preenchido
            if not cpf_input:
                erros.append("CPF é obrigatório.")

            # Verifica se a data de nascimento está no formato correto
            if not re.match(r"^\d{2}/\d{2}/\d{4}$", data_nascimento_input):
                erros.append("Data de nascimento inválida. Use o formato DD/MM/AAAA.")

            # Verifica se o e-mail é válido
            if not re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", email_input):
                erros.append("E-mail inválido.")

            # Verifica se o gênero foi selecionado
            if genero_input == "":
                erros.append("Gênero é obrigatório.")

            # Verifica se o RG foi preenchido
            if not rg_input:
                erros.append("RG é obrigatório.")

            # Verifica se o telefone tem o tamanho correto
            if len(telefone_input) < 10 or len(telefone_input) > 11:
                erros.append("Telefone inválido. Use DDD + número.")

            # Verifica se todos os campos bancários foram preenchidos
            if not banco_nome_input or not banco_agencia_input or not banco_conta_input:
                erros.append("Todos os campos bancários devem ser preenchidos.")

            # Se houver erros, exibe-os
            if erros:
                for erro in erros:
                    st.error(erro)
            else:
                # Se não houver erros, grava os dados no banco de dados
                atualizacoes = {
                    "nome_completo": nome_input,
                    "cpf": cpf_input,
                    "email": email_input,
                    "data_nascimento": data_nascimento_input,
                    "genero": genero_input,
                    "rg": rg_input,
                    "telefone": telefone_input,
                    "banco": {
                        "nome": banco_nome_input,
                        "agencia": banco_agencia_input,
                        "conta": banco_conta_input,
                        "tipo": banco_tipo_input,
                    }
                }
                # Insere o novo usuário no banco de dados
                banco_de_dados["usuarios_externos"].insert_one(atualizacoes)
                # Exibe uma mensagem de sucesso
                st.success(":material/check: Viajante cadastrado com sucesso!")
                # Aguarda 3 segundos antes de atualizar a página
                time.sleep(3)
                # Atualiza a página
                st.rerun()



# Função para verificar CPF e identificar o usuário------------------------------
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
        # Atualiza CPF no session state
        st.session_state.cpf_inserido = cpf_numeros  

        # Busca primeiro nos usuários internos
        df_usuarios_internos = carregar_internos()

        # Verifica se existe um usuário interno com o CPF informado
        usuario_interno = df_usuarios_internos[df_usuarios_internos["cpf"] == cpf_numeros]
        
        # Se encontrou pelo menos um resultado, o CPF é de um usuário interno
        if not usuario_interno.empty:  
            # Recupera o dicionário do usuário interno
            usuario = usuario_interno.iloc[0].to_dict()
            # Atualiza o tipo de usuário e o usuário no session state
            st.session_state.tipo_usuario = "interno"
            st.session_state.usuario = usuario  
            # Retorna True, sem precisar carregar os usuários externos
            return True

        # Se não for interno, busca nos usuários externos
        df_usuarios_externos = carregar_externos()
      
        # Verifica se o CPF existe nos usuários externos
        usuario_externo = df_usuarios_externos[df_usuarios_externos["cpf"] == cpf_numeros]

        if not usuario_externo.empty:  # Se encontrou pelo menos um resultado
            usuario = usuario_externo.iloc[0].to_dict()
            st.session_state.tipo_usuario = "externo"
            st.session_state.usuario = usuario  
            return True  # Retorna imediatamente

        # Se não encontrou nem interno nem externo, marca como "novo"
        st.session_state.tipo_usuario = "novo"
        st.session_state.usuario = None  
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



# Cabeçalho das duas telas de login
def cabecalho_login():
    # Título
    st.markdown(
        """
        <div style="text-align: center;">
            <h2>Portal de Viagens do ISPN</h2>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write("")
    st.write("")
    st.write("")
    st.write("")
    st.write("")


# Página de login etapa 1 - CPF
def pagina_login_etapa_1():
    cabecalho_login()


    # INFORME SEU CPF
    col1, col2, col3 = st.columns([5, 2, 5])    


    # Formulário para solicitar o CPF
    with col2.form("form_login", border=False):
        cpf_input = st.text_input("Digite seu CPF", placeholder="000.000.000-00")
        if st.form_submit_button("Entrar"):
            
            # Verifica se o CPF é válido
            resultado = check_cpf(cpf_input)
            
            if resultado:

                # Se o CPF é novo, vai para a página de cadastro
                if st.session_state.tipo_usuario == "novo":
                    st.session_state.logged_in = "novo_cadastro"

                    # Força a atualização da página
                    st.rerun()


                # Se o usuário for externo ou interno
                elif st.session_state.tipo_usuario in ["externo", "interno"]:

                    # Atalho para desenvolvedor >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
                    # st.session_state.logged_in = "logado"

                    # Avançar para a etapa de código caso necessário
                    st.session_state.logged_in = "etapa_2_codigo"

                    st.rerun()

    
            else:
                # Se o CPF for inválido, exibe mensagem de erro
                st.error("CPF inválido.")


# Página de login etapa 2 - Código por e-mail
def pagina_login_etapa_2():
    if "codigo_enviado" not in st.session_state:
        st.session_state.codigo_enviado = False
    if "codigo_verificacao" not in st.session_state:
        st.session_state.codigo_verificacao = None
    
    # Exibe o cabeçalho com o título
    cabecalho_login()

    # Informa que o código foi enviado para o e-mail
    st.markdown(
        """
        <div style="text-align: center;">
            <strong style="font-size: 1.2em; color: #007ad3;">Foi enviado um código de 3 dígitos para o seu e-mail.</strong>
            
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write('')

    # Exibe o e-mail do usuário
    st.markdown(
        f"""
        <div style="text-align: center;">
            <p style="font-size: 1.2em">{st.session_state.usuario["email"]}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write('')
    st.write('')
    st.write('')

    # Divide a tela em 3 colunas
    col1, col2, col3 = st.columns([5, 2, 5])    

    # Se ainda não há código gerado, cria um novo
    if not st.session_state.codigo_enviado:
        st.session_state.codigo_verificacao = str(random.randint(100, 999))  # Garante que seja string
        
        # Envia o e-mail
        if enviar_email(st.session_state.usuario["email"], st.session_state.codigo_verificacao):
            st.session_state.codigo_enviado = True

    # Solicita o Código
    with col2.form("codigo_login", border=False):
        codigo_input = st.text_input("Informe o código recebido", placeholder="000")
        if st.form_submit_button("Confirmar"):
            if codigo_input == st.session_state.codigo_verificacao:
                st.session_state.logged_in = "logado"  # Avança para a home
                st.rerun()
            else:
                st.error("Código inválido.")



# Página de Cadastrar novo usuário
def novo_cadastro():

    # Exibe o cabeçalho da página de novo cadastro
    cabecalho_login()

    # Cria colunas na tela
    col1, col2, col3 = st.columns([2, 2, 2])

    # Adiciona um subtítulo para o cadastro
    col2.subheader("Novo cadastro")
  
    with col2.form(key='form_usuario'):
        
        # Campos do formulário para o usuário preencher
        nome_completo = st.text_input("Nome Completo")
        data_nascimento = st.date_input("Data de Nascimento", format="DD/MM/YYYY", value=None)
        cpf = st.text_input("CPF", value=st.session_state.cpf_inserido if st.session_state.cpf_inserido else "")
        genero = st.selectbox("Gênero", [""] + ["Masculino", "Feminino", "Outro"], index=0)
        rg = st.text_input("RG e Órgão Emissor")

        telefone = st.text_input("Telefone", placeholder="(00) 00000-0000")

        email = st.text_input("E-mail")
        
        # Dados bancários do usuário
        st.write("**Dados Bancários**")
        banco_nome = st.text_input("Nome do Banco")
        agencia = st.text_input("Agência")
        conta = st.text_input("Conta")
        tipo_conta = st.selectbox("Tipo de Conta", ["Conta Corrente", "Conta Poupança", "Conta Salário"], index=0)
        
        # Botão de submissão
        submit_button = st.form_submit_button("Cadastrar", type="primary")
        
        if submit_button:
            # Verifica se todos os campos estão preenchidos
            if not all([nome_completo, data_nascimento, cpf, genero, rg, telefone, email, banco_nome, agencia, conta, tipo_conta]):
                st.error("Por favor, preencha todos os campos.")
            else:
                # Insere um novo usuário na coleção do banco de dados
                colecao = banco_de_dados["usuarios_externos"]

                # Cria um dicionário com os dados do novo usuário
                novo_usuario = {
                    "nome_completo": nome_completo,
                    "data_nascimento": data_nascimento.strftime("%d/%m/%Y"),  # Formata a data no formato "DD/MM/YYYY"
                    "cpf": cpf,
                    "genero": genero,
                    "rg": rg,
                    "telefone": telefone,
                    "email": email,
                    "banco": {  # Dicionário com os dados bancários
                        "nome": banco_nome,
                        "agencia": agencia,
                        "conta": conta,
                        "tipo": tipo_conta
                    }
                }
                # Insere o novo usuário na coleção do banco de dados
                colecao.insert_one(novo_usuario)

                # Atualiza o estado da sessão com o novo usuário
                st.session_state.usuario = novo_usuario
                st.session_state.tipo_usuario = "externo"
                st.session_state.logged_in = "etapa_2_codigo"

                # Recarrega a aplicação
                st.rerun()


# ##################################################################
# PÁGINA DO USUÁRIO INTERNO
# ##################################################################


def home_page():

# !!!!!!!!!!!!!!
    # Carregar dados com base no tipo de usuário
    if st.session_state.tipo_usuario == "interno":
        # Usuário interno: 
        # carrega SAVs e RVSs internas
        df_savs = carregar_savs_int()
        df_rvss = carregar_rvss_int()

        # carrega SAVs e RVSs de terceiros
        df_savs_terceiros = carregar_savs_trc()
        df_rvss_terceiros = carregar_rvss_trc()


    elif st.session_state.tipo_usuario == "externo":
        # Usuário externo: carrega SAVs e RVSs externas
        df_savs = carregar_savs_ext()
        df_rvss = carregar_rvss_ext()


        
    # Captura o usuário do session_state para a variável usuario
    usuario = st.session_state.usuario
    

    # Cria colunas para o nome do usuário e o botão atualizar
    col1, col2, col3, col4, col5 = st.columns([2, 2, 7, 3, 3])

    # Exibe o nome do usuário
    col1.markdown(
        f"""
        <div>
            <h3 style="color: gray;">Olá {usuario['nome_completo'].split(' ')[0]}</h3>
        </div>
        """,
        unsafe_allow_html=True
    )


    # Botão meu cadastro
    @st.dialog("Meu cadastro", width="large")
    def meu_cadastro():
        with st.form("meu_cadastro"):
            

            # Obtém o CPF numérico do usuário
            usuario_cpf_numerico = "".join(filter(str.isdigit, usuario['cpf']))

            col1, espaco, col2 = st.columns([12, 1, 12])

            # COLUNA 1

            # 1. Nome
            nome_input = col1.text_input("Nome Completo", value=usuario.get("nome_completo", ""))

            # 2. Exibe o CPF, com a formatação
            cpf_input = col1.text_input("CPF", value=f"{usuario['cpf'][:3]}.{usuario['cpf'][3:6]}.{usuario['cpf'][6:9]}-{usuario['cpf'][9:]}", disabled=True)

            
            #  3. Data de nascimento
            data_nascimento_input = col1.text_input("Data de Nascimento", value=usuario.get("data_nascimento", "") if pd.notna(usuario.get("data_nascimento")) else "")

            #  4. e-mail
            email_input = col1.text_input("E-mail", value=usuario.get("email", ""))
            
            # 5. Banco
            # Ver bloco abaixo



            # COLUNA 2

            # 1. Gênero
            genero_input = col2.selectbox(
                "Gênero",
                ["", "Masculino", "Feminino", "Outro"],
                index=["", "Masculino", "Feminino", "Outro"].index(usuario.get("genero", ""))
                if usuario.get("genero") in ["Masculino", "Feminino", "Outro"] else 0
            )


            # 2. Exibe o campo de RG e órgão emissor com valor vazio se não encontrado
            rg_input = col2.text_input("RG e órgão emissor", value=usuario.get("rg", "") if pd.notna(usuario.get("rg")) else "")


            #  3. Telefone
            telefone_input = col2.text_input("Telefone", value=usuario.get("telefone", "") if pd.notna(usuario.get("telefone")) else "")


# !!!!!!!!!!!!!!!!!!!!!
            # 4. E-mail do coordenador

            if st.session_state.tipo_usuario == "interno":
                email_coordenador_input = col2.text_input("E-mail do(a) Coordenador(a)", value=usuario.get("email_coordenador", "") if pd.notna(usuario.get("email_coordenador")) else "")

            elif st.session_state.tipo_usuario == "externo":
                col2.markdown("<div style='height: 84px'></div>", unsafe_allow_html=True)

            # col2.write('')
            # col2.write("**Dados Bancários**")


            #  5. Banco
            # Verifica se a chave 'banco' existe no cadastro do usuário
            if 'banco' in usuario:  # Verifica se a chave 'banco' existe no cadastro
                # Exibe os campos bancários com dados do banco, se existir
                banco_nome_input = col1.text_input("Banco", value=usuario.get("banco", {}).get("nome", ""))
                banco_agencia_input = col2.text_input("Agência", value=usuario.get("banco", {}).get("agencia", ""))
                banco_conta_input = col2.text_input("Conta", value=usuario.get("banco", {}).get("conta", ""))
                banco_tipo_input = col1.selectbox(
                    "Tipo de Conta", 
                    ["Conta Corrente", "Conta Poupança", "Conta Salário"], 
                    index=["Conta Corrente", "Conta Poupança", "Conta Salário"].index(usuario.get("banco", {}).get("tipo", ""))
                )
            else:
                # Se não existir a chave 'banco', os campos bancários são exibidos vazios
                banco_nome_input = col1.text_input("Banco", value="")
                banco_agencia_input = col2.text_input("Agência", value="")
                banco_conta_input = col2.text_input("Conta", value="")
                banco_tipo_input = col1.selectbox(
                    "Tipo de Conta", 
                    ["Conta Corrente", "Conta Poupança", "Conta Salário"], 
                    index=0  # Por padrão, seleciona o primeiro valor (Conta Corrente)
                )

            st.write('')
            # Ao clicar no botão de "Atualizar cadastro", realiza a atualização dos dados
            if st.form_submit_button("Atualizar cadastro", icon=":material/refresh:", type="primary"):
                atualizacoes = {}
                
                # Verifica se o usuário foi encontrado no banco de dados
                if usuario:
                    # Atualiza o nome completo
                    if nome_input != usuario.get("nome_completo", ""):
                        atualizacoes["nome_completo"] = nome_input
                        usuario["nome_completo"] = nome_input
                    
                    # Atualiza o e-mail se for válido
                    if email_input != usuario.get("email", ""):
                        if re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", email_input):
                            atualizacoes["email"] = email_input
                            usuario["email"] = email_input
                        else:
                            st.error("E-mail inválido. Insira um endereço válido.")
                            return
                    
                    # Atualiza o telefone se for válido
                    if telefone_input != usuario.get("telefone", ""):
                        telefone_numerico = "".join(filter(str.isdigit, telefone_input))
                        if len(telefone_numerico) < 10 or len(telefone_numerico) > 11:
                            st.error("Telefone inválido. Insira um telefone válido com DDD e número.")
                            return
                        atualizacoes["telefone"] = telefone_input
                        usuario["telefone"] = telefone_input
                    
                    # Atualiza a data de nascimento se for válida
                    if data_nascimento_input != usuario.get("data_nascimento", ""):
                        data_numerica = "".join(filter(str.isdigit, data_nascimento_input))
                        if len(data_numerica) != 8:
                            st.error("Data de nascimento inválida. Insira uma data no formato DD/MM/YYYY.")
                            return
                        atualizacoes["data_nascimento"] = data_nascimento_input
                        usuario["data_nascimento"] = data_nascimento_input
                    
                    # Atualiza o gênero
                    if genero_input != usuario.get("genero", ""):
                        atualizacoes["genero"] = genero_input
                        usuario["genero"] = genero_input
                    
                    # Atualiza o RG e órgão emissor
                    if rg_input != usuario.get("rg", ""):
                        atualizacoes["rg"] = rg_input
                        usuario["rg"] = rg_input

# !!!!!!!!!!!!!!!!!!!!!
                    # Atualiza o e-mail do coordenador se for válido
                    if st.session_state.tipo_usuario == "interno":
                        if email_coordenador_input != usuario.get("email_coordenador", ""):
                            if re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", email_coordenador_input):
                                atualizacoes["email_coordenador"] = email_coordenador_input
                                usuario["email_coordenador"] = email_coordenador_input
                            else:
                                st.error("E-mail do coordenador inválido. Insira um endereço válido.")
                                return


                    banco_atualizacoes = {}
                    # Atualiza os dados bancários se forem diferentes
                    if banco_nome_input != usuario.get("banco", {}).get("nome", ""):
                        banco_atualizacoes["nome"] = banco_nome_input
                    if banco_agencia_input != usuario.get("banco", {}).get("agencia", ""):
                        banco_atualizacoes["agencia"] = banco_agencia_input
                    if banco_conta_input != usuario.get("banco", {}).get("conta", ""):
                        banco_atualizacoes["conta"] = banco_conta_input
                    if banco_tipo_input != usuario.get("banco", {}).get("tipo", ""):
                        banco_atualizacoes["tipo"] = banco_tipo_input
                    
                    # Se houver atualizações no banco, aplica as alterações
                    if banco_atualizacoes:
                        atualizacoes["banco"] = {**usuario.get("banco", {}), **banco_atualizacoes}
                        usuario["banco"] = atualizacoes["banco"]
                    
                    # Atualiza o cadastro no banco de dados
                    
# !!!!!!!!!!!!!!!!!!!!!

                    if st.session_state.tipo_usuario == "interno":
                        banco_de_dados["usuarios_internos"].update_one(
                            {"cpf": usuario_cpf_numerico},
                            {"$set": atualizacoes}
                        )

                    elif st.session_state.tipo_usuario == "externo":
                        banco_de_dados["usuarios_externos"].update_one(
                            {"cpf": usuario_cpf_numerico},
                            {"$set": atualizacoes}
                        )

                    # Se a atualização foi realizada com sucesso, exibe uma mensagem de sucesso
                    # e recarrega a página após alguns segundos
                    st.success("Cadastro atualizado com sucesso!")
                    time.sleep(3)
                    st.rerun()
                else:
                    # Se não houver nenhum usuário com o CPF informado, exibe uma mensagem de erro
                    st.error("Usuário não encontrado.")
                    
    # Botão de acesso ao Meu cadastro
    if col4.button("Meu cadastro", icon=":material/person:", use_container_width=True):
        meu_cadastro()



    # Botão para atualizar a página
    if col5.button("Atualizar página", icon=":material/refresh:", use_container_width=True):
        # Limpa o session_state e o cache, e recarrega a página
        st.session_state.status_usuario = ""
        st.cache_data.clear()
        st.rerun()  
        
        
    st.write("")

# !!!!!!!!!!!!!!!!!!!!!!!!
    if st.session_state.tipo_usuario == "interno":

        # Abas da home
        minhas_viagens, nova_sav, terceiros = st.tabs([":material/flight_takeoff: Minhas Viagens", ":material/add: Nova Solicitação de Viagem", ":material/group: Solicitações para Terceiros"])

    elif st.session_state.tipo_usuario == "externo":
        minhas_viagens, nova_sav = st.tabs([":material/flight_takeoff: Minhas Viagens", ":material/add: Nova Solicitação de Viagem"])

    # ABA MINHAS VIAGENS

    with minhas_viagens:

        # Limpar a coluna CPF: quero apenas os números
        df_savs['CPF:'] = df_savs['CPF:'].str.replace(r'[^\d]+', '', regex=True)

        # Filtar SAVs com o CPF do usuário
        df_savs = df_savs[df_savs['CPF:'].astype(str) == str(usuario['cpf'])]

        # Capturar a data da viagem
        df_savs['Data da viagem:'] = df_savs['Itinerário:'].str[6:16].replace('-', '/', regex=True)


# !!!!!!!!!!!!!!
        # if st.session_state.tipo_usuario == "interno":
        destinos = r'Cidade de chegada: (.*?)(?:,|$)'
        # elif st.session_state.tipo_usuario == "externo":
            # destinos = r'Cidade de chegada: (.*?)(?:,|$)'
        
        
        # Aplicar a regex para cada linha da coluna
        df_savs["Destinos:"] = df_savs["Itinerário:"].apply(lambda x: ' > '.join(re.findall(destinos, x)))

    
        # Criar cabeçalho da "tabela"
        col1, col2, col3, col4, col5 = st.columns([2, 2, 7, 3, 3])

        col1.write('**Código da viagem**')
        col2.write('**Data da viagem**')
        col3.write('**Itinerário**')
        col4.write('**Solicitações**')
        col5.write('**Relatórios**')

        # Iniciar a variável na session_state que vai identificar se o usuário está impedido ou não de enviar relatório (se tem algum pendente)
        st.session_state.status_usuario = ""

        # Iterar sobre a lista de viagens
        for index, row in df_savs[::-1].iterrows():

            # Preparar o link personalizado para o relatório -----------------------------------------------------

            # Extrair cidade(s) de destino
            # Transformar o itinerário em uma lista de dicionários
            trechos = parse_itinerario(row["Itinerário:"])

            # Pegando a primeira e a última data
            data_inicial = trechos[0]["Data"]
            data_final = trechos[-1]["Data"]

            # Formata a data do período da viagem para o formato DD/MM/YYYY a DD/MM/YYYY
            periodo_viagem = f"{data_inicial} a {data_final}".replace('-', '/')

# !!!!!!!!!!!!!!!!!!!!
            # Extraindo todas as "Cidade de chegada" e concatenando com vírgula
            # if st.session_state.tipo_usuario == "interno":
            cidades_chegada = [viagem["Cidade de chegada"] for viagem in trechos]
            # elif st.session_state.tipo_usuario == "externo":
            #     cidades_chegada = [viagem["Cidade de chegada"] for viagem in trechos]
            
            destinos = ", ".join(cidades_chegada)


# !!!!!!!!!!!!!!!!!!!
            # Prepara as URLs de formulários com alguns campos pré-preenchidos
            if st.session_state.tipo_usuario == "interno":
                # URL do formulário de RVS interno
                params = {
                    "codigoDa": row["Código da viagem:"],
                    "qualE": row["Qual é a fonte do recurso?"],
                    "nomeDo": row["Nome completo:"],
                    "email": row["E-mail:"],
                    "cidadesDe": destinos,
                    "periodoDa": periodo_viagem
                }

                jotform_rvs_url = f"{st.secrets['links']['url_rvs_int']}?{encode_params(params)}"


            elif st.session_state.tipo_usuario == "externo":
                # URL do formulário de RVS externo
                params = {
                    "codigoDa": row["Código da viagem:"],
                    "qualE": row["Qual é a fonte do recurso?"],
                    "nomeDo": row["Nome completo:"],
                    "email": row["E-mail:"],
                    "cidadesDe": destinos,
                    "periodoDa": periodo_viagem
                }

                jotform_rvs_url = f"{st.secrets['links']['url_rvs_ext']}?{encode_params(params)}"

            # ----------------------------------------------------------------------------------------------------- 

            # Conteúdo da lista de viagens

            col1, col2, col3, col4, col5 = st.columns([2, 2, 7, 3, 3])
            
            col1.write(row['Código da viagem:'])
            col2.write(row['Data da viagem:'])
            col3.write(row['Destinos:'])
            col4.button('Detalhes', key=f"detalhes_{index}", on_click=mostrar_detalhes_sav, args=(row,), use_container_width=True, icon=":material/info:")
            

            # Botão dinâmico sobre o relatório --------------------------------------------

            # Verificar se o relatório foi entregue. Procura se tem o código da SAV em algum relatório 
            if row['Código da viagem:'].upper() in df_rvss['Código da viagem:'].str.upper().values:

                status_relatorio = "entregue"

            # Se não tem nenhum relatório com esse código de SAV
            else:
                status_relatorio = "pendente"

                # Se a data_final da viagem menor do que hoje, o usuário está impedido
                if pd.to_datetime(data_final, dayfirst=True).timestamp() < pd.to_datetime(date.today()).timestamp():
                
                    # Impede o usuário de enviar uma nova solicitação se tiver relatório pendente
                    st.session_state.status_usuario = "impedido"
                    

            # Se o relatório foi entregue, vê o relatório  
            if status_relatorio == "entregue":
                col5.button('Relatório entregue', key=f"entregue_{index}", on_click=mostrar_detalhes_rvs, args=(row, df_rvss), use_container_width=True, icon=":material/check:", type="primary")
            
            # Se não foi entregue, botão para enviar
            # else:
            if status_relatorio == "pendente":
                # Se não foi entregue, botão para enviar
                col5.link_button('Enviar relatório', use_container_width=True, icon=":material/description:", url=jotform_rvs_url)

            st.divider()  # Separador entre cada linha da tabela



    # ABA DE NOVA SOLICITAÇÃO
    
    with nova_sav:

        # Verifica se o usuário está impedido de enviar uma nova solicitação
        if st.session_state.status_usuario == "impedido":
            st.write('')
            st.write('')
            st.write('')

            # Exibe um aviso de impedimento
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
            banco_info = safe_get(usuario, 'banco', {}) if isinstance(usuario.get('banco'), dict) else {}

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

            # Verifica o tipo de usuário e gera a URL apropriada para o formulário de solicitação de viagem
            if st.session_state.tipo_usuario == "interno":

                jotform_sav_url = f"{st.secrets['links']['url_sav_int']}?nomeCompleto={safe_get(usuario, 'nome_completo')}&dataDe={safe_get(usuario, 'data_nascimento')}&genero={safe_get(usuario, 'genero')}&rg={safe_get(usuario, 'rg')}&cpf={safe_get(usuario, 'cpf')}&telefone={safe_get(usuario, 'telefone')}&email={safe_get(usuario, 'email')}&emailDoa={safe_get(usuario, 'email_coordenador')}&banco={safe_get(banco_info, 'nome')}&agencia={safe_get(banco_info, 'agencia')}&conta={safe_get(banco_info, 'conta')}&tipoDeConta={safe_get(banco_info, 'tipo')}"

                # Mensagem de manutenção
                # st.write('')
                # st.subheader(':material/build: Formulário temporariamente fora do ar para manutenção.')


                # Exibe o formulário em um iframe
                st.components.v1.iframe(jotform_sav_url, width=None, height=5000)

                col1, col2, col3 = st.columns(3)
                col2.subheader('Após enviar, role a página até o topo :material/keyboard_double_arrow_up:')


            elif st.session_state.tipo_usuario == "externo":
                # URL do formulário de SAV externa
                jotform_sav_url = f"{st.secrets['links']['url_sav_ext']}?nomeCompleto={usuario['nome_completo']}&dataDe={usuario['data_nascimento']}&genero={usuario['genero']}&rg={usuario['rg']}&cpf={usuario['cpf']}&telefone={usuario['telefone']}&email={usuario['email']}&banco={usuario['banco']['nome']}&agencia={usuario['banco']['agencia']}&conta={usuario['banco']['conta']}&tipoDeConta={safe_get(banco_info, 'tipo')}"

                # Exibe o formulário em um iframe
                st.components.v1.iframe(jotform_sav_url, width=None, height=4000)

                col1, col2, col3 = st.columns(3)
                col2.subheader('Após enviar, role a página até o topo :material/keyboard_double_arrow_up:')


# !!!!!!!!!!!!!!!!!!!!!!!!
 
    # Se for usuário interno, mostra a aba de SAVs para Terceiros
    if st.session_state.tipo_usuario == "interno":
       with terceiros:


        # NOVA SOLICITAÇÃO PARA TERCEIROS

        df_usuarios_externos = carregar_externos()
        df_usuarios_externos = df_usuarios_externos.sort_values(by='nome_completo', ascending=True)

        st.write('**Nova Solicitação para Terceiros**')
        st.write('')

        # Cria as colunas para o formulário
        col1, col2, col3, col4 = st.columns(4)

        # Selecione o(a) viajante:
        viajante_nome = col1.selectbox('Selecione o(a) viajante:', [""] + df_usuarios_externos['nome_completo'].tolist())

        if viajante_nome != "":

            viajante = df_usuarios_externos[df_usuarios_externos['nome_completo'] == viajante_nome].iloc[0].to_dict()

            # Monta a URL do JotForm para solicitação de SAV para Terceiros

            # Separa o dicionário do banco antes
            banco_info_ext = safe_get(viajante, 'banco') or {}

            # Função para formatar o CPF e garantir que seja tratado como string quando cair no google sheets, e assim preservar os zeros à esquerda
            def format_cpf(cpf: str) -> str:
                # Remove tudo que não for número
                digits = ''.join(filter(str.isdigit, cpf or ''))
                # Preenche com zeros à esquerda até ter 11 dígitos
                digits = digits.zfill(11)
                # Aplica a máscara 000.000.000-00
                return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"
            cpf_formatado = format_cpf(safe_get(usuario, 'cpf'))


            params = {
                "responsavel": safe_get(usuario, "nome_completo"),
                "email_responsavel": safe_get(usuario, "email"),
                "cpf_responsavel": cpf_formatado,
                "email_coordenador": safe_get(usuario, "email_coordenador"),
                "nome_viajante": safe_get(viajante, "nome_completo"),
                "dataDe": safe_get(viajante, "data_nascimento"),
                "genero": safe_get(viajante, "genero"),
                "rg": safe_get(viajante, "rg"),
                "cpf": safe_get(viajante, "cpf"),
                "telefone": safe_get(viajante, "telefone"),
                "email": safe_get(viajante, "email"),
                "banco": safe_get(banco_info_ext, "nome"),
                "agencia": safe_get(banco_info_ext, "agencia"),
                "conta": safe_get(banco_info_ext, "conta"),
                "tipoDeConta": safe_get(banco_info_ext, "tipo"),
            }

            jotform_sav_url = f"{st.secrets['links']['url_sav_trc']}?{encode_params(params)}"

            # Mostra a URL no Streamlit
            col2.write('')
            col2.write('')

            # Mensagem de manutenção.
            # col2.write('Site em manutenção. Tente novamente mais tarde.')

            col2.markdown(f"<a href='{jotform_sav_url}' target='_blank'>>> Clique aqui criar uma nova SAV para Terceiros</a>", unsafe_allow_html=True)

        else:

            # Se o viajante não for selecionado, mostra um aviso
            col3.write('O nome não aparece na lista?')
    
            # Botão de acesso ao Cadastro de Viajante Externo
            if col3.button("Cadastrar viajante", icon=":material/person_add:"):
                cadastrar_externo()

        st.divider()


        # LISTA DE VIAGENS DE TERCEIROS

        st.write('**Viagens solicitadas por mim**')
        st.write('')


        # Limpar a coluna CPF do responsável pela SAV quero apenas os números
        df_savs_terceiros['CPF do responsável pela SAV:'] = df_savs_terceiros['CPF do responsável pela SAV:'].str.replace(r'[^\d]+', '', regex=True)


        # Filtar SAVs com o CPF do usuário
        df_savs_terceiros = df_savs_terceiros[df_savs_terceiros['CPF do responsável pela SAV:'].astype(str) == str(usuario['cpf'])]

        # Capturar a data da viagem
        df_savs_terceiros['Data da viagem:'] = df_savs_terceiros['Itinerário:'].str[6:16].replace('-', '/', regex=True)

        # Expressão regular para capturar o nome da cidade de chegada
        destinos = r'Cidade de chegada: (.*?)(?:,|$)'
        
        
        # Aplicar a regex para cada linha da coluna
        df_savs_terceiros["Destinos:"] = df_savs_terceiros["Itinerário:"].apply(lambda x: ' > '.join(re.findall(destinos, x)))


        # Criar cabeçalho da "tabela"
        col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 4, 6, 3, 3])

        col1.write('Código da viagem')
        col2.write('Data da viagem')
        col3.write('Nome do(a) viajante')
        col4.write('Destinos')
        col5.write('Solicitações')
        col6.write('Relatórios')

        # Iterar sobre a lista de viagens
        for index, row in df_savs_terceiros[::-1].iterrows():

            # Preparar o link personalizado para o relatório -----------------------------------------------------

            # Extrair cidade(s) de destino
            # Transformar o itinerário em uma lista de dicionários
            trechos = parse_itinerario(row["Itinerário:"])

            # Pegando a primeira e a última data
            data_inicial = trechos[0]["Data"]
            data_final = trechos[-1]["Data"]

            # Formata a data do período da viagem para o formato DD/MM/YYYY a DD/MM/YYYY
            periodo_viagem = f"{data_inicial} a {data_final}".replace('-', '/')

# !!!!!!!!!!!!!!!!!!!!
            # Extraindo todas as "Cidade de chegada" e concatenando com vírgula
            # if st.session_state.tipo_usuario == "interno":
            cidades_chegada = [viagem["Cidade de chegada"] for viagem in trechos]
            # elif st.session_state.tipo_usuario == "externo":
            #     cidades_chegada = [viagem["Cidade de chegada"] for viagem in trechos]
            
            destinos = ", ".join(cidades_chegada)


# !!!!!!!!!!!!!!!!!!!
            # Prepara as URLs de formulários com alguns campos pré-preenchidos
            if st.session_state.tipo_usuario == "interno":
                # URL do formulário de RVS de Terceiros
                params = {
                    "codigoDa": row["Código da viagem:"],
                    "qualE": row["Qual é a fonte do recurso?"],
                    "responsavel": row["Responsável pela SAV:"],
                    "nome_viajante": row["Nome do(a) viajante:"],
                    "email": row["E-mail:"],
                    "cidadesDe": destinos,
                    "periodoDa": periodo_viagem
                }

                jotform_rvs_terceiros_url = f"{st.secrets['links']['url_rvs_trc']}?{encode_params(params)}"
                
                

#             # ----------------------------------------------------------------------------------------------------- 

#             # Conteúdo da lista de viagens

            col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 4, 6, 3, 3])
            
            col1.write(row['Código da viagem:'])
            col2.write(row['Data da viagem:'])
            col3.write(row['Nome do(a) viajante:'])
            col4.write(row['Destinos:'])
            col5.button('Detalhes', key=f"detalhes_terc_{index}", on_click=mostrar_detalhes_sav, args=(row,), use_container_width=True, icon=":material/info:")
            

            # Botão dinâmico sobre o relatório --------------------------------------------

            # Verificar se o relatório foi entregue. Procura se tem o código da SAV em algum relatório 
            if row['Código da viagem:'].upper() in df_rvss_terceiros['Código da viagem:'].str.upper().values:

                status_relatorio = "entregue"

            # Se não tem nenhum relatório com esse código de SAV
            else:
                status_relatorio = "pendente"



            # Se o relatório foi entregue, vê o relatório  
            if status_relatorio == "entregue":
                col6.button('Relatório entregue', key=f"entregue_{index}", on_click=mostrar_detalhes_rvs, args=(row, df_rvss_terceiros), use_container_width=True, icon=":material/check:", type="primary")
            
            # Se não foi entregue, botão para enviar
            # else:
            elif status_relatorio == "pendente":
                # Se não foi entregue, botão para enviar
                col6.link_button('Enviar relatório', use_container_width=True, icon=":material/description:", url=jotform_rvs_terceiros_url)

            st.divider()  # Separador entre cada linha da tabela



# ##################################################################
# NAVEGAÇÃO DE PÁGINAS
# ##################################################################

# Verifica se o usuário já está logado
if "logged_in" not in st.session_state:
    st.session_state.logged_in = "etapa_1_cpf"  # Define o estado de login como falso inicialmente

# Exibe a página de login ou a página principal, dependendo do estado de login
if st.session_state.logged_in == "etapa_1_cpf":
    pagina_login_etapa_1()  

# Depois de colocar o cpf, vai pra etapa do recebimento do código por email
elif st.session_state.logged_in == "etapa_2_codigo":
    pagina_login_etapa_2()  

# Usuário está logado, exibe a página inicial
elif st.session_state.logged_in == "logado":
    home_page()  

# Usuário novo, exibe a página de cadastro
elif st.session_state.logged_in == "novo_cadastro":
    novo_cadastro()