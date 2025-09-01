# app.py - VERSÃO FINAL COM CORREÇÃO DEFINITIVA DE CAMINHO ABSOLUTO

import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime
import gspread
from gspread_dataframe import set_with_dataframe
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

# %% 
os.getcwd()
#%%

# --- CARREGAR VARIÁVEIS DE AMBIENTE DE FORMA EXPLÍCITA ---
# Isso garante que o arquivo .env seja lido a partir da pasta do script.
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dotenv_path = os.path.join(script_dir, '.env')
    load_dotenv(dotenv_path=dotenv_path)

    if os.path.exists(dotenv_path):
        st.write(f".env encontrado em: {dotenv_path}")
    else:
        st.write(f".env NÃO encontrado em: {dotenv_path}")

    st.write("Valor da variável GOOGLE_CREDENTIALS_PATH:", os.getenv("GOOGLE_CREDENTIALS_PATH"))


except NameError:
    load_dotenv()

# --- FUNÇÕES AUXILIARES ---

def find_latest_file(folder_path):
    pattern = re.compile(r'155_(\d{6})\.xlsx', re.IGNORECASE)
    latest_date, latest_file = None, None
    try:
        files = os.listdir(folder_path)
    except FileNotFoundError:
        st.error(f"Erro: O diretório não foi encontrado: '{folder_path}'")
        return None
    for filename in files:
        match = pattern.match(filename)
        if match:
            date_str = match.group(1)
            try:
                current_date = datetime.strptime(date_str, '%d%m%y')
                if latest_date is None or current_date > latest_date:
                    latest_date, latest_file = current_date, filename
            except ValueError:
                continue
    return os.path.join(folder_path, latest_file) if latest_file else None

def process_data(file_path):
    try:
        df = pd.read_excel(file_path)
        df['produto_retirar_dtpreventrega'] = pd.to_datetime(df['produto_retirar_dtpreventrega'], errors='coerce')
        df['data_saida'] = df['produto_retirar_dtpreventrega'].dt.date
        df['dias_espera'] = pd.to_datetime(df['data_saida'])
        df['data_saida'] = pd.to_datetime(df['data_saida'])
        df['produto_retirar_dtmovimento'] = pd.to_datetime(df['produto_retirar_dtmovimento'])
        df['dias_espera'] = (df['data_saida'] - df['produto_retirar_dtmovimento']).dt.days
        
        def extrair_primeiro_nome(texto):
            if pd.isna(texto) or texto.strip() == '': return ''
            texto = str(texto).strip()
            texto_limpo = re.sub(r'[^\w\s]', ' ', texto)
            texto_limpo = re.sub(r'\s+', ' ', texto_limpo).strip()
            palavras = texto_limpo.split()
            nomes_puros = [p for p in palavras if p.isalpha() and len(p) > 1]
            if nomes_puros: return nomes_puros[0].upper()
            matches = re.findall(r'[A-Za-z]{2,}', texto)
            if matches: return matches[0].upper()
            return ''

        df['primeiro_nome'] = df['cliente_fornecedor_nomevendedor'].apply(extrair_primeiro_nome)

        df.rename(columns={'produto_retirar_dtmovimento':'dtmovimento','produto_retirar_idlocalretirada':'idlocalretirada','produto_retirar_dtpreventrega':'dtpreventrega','local_retirada_descrlocalretirada':'descrlocalretirada','produtos_view_idsubproduto':'idsubproduto','produtos_view_descricaoproduto':'descricaoproduto','Quantidade Produto':'qtde_produto','Número Nota':'num_nota','Série Nota':'serie_nota','cliente_fornecedor_idclifor':'idclifor','cliente_fornecedor_nome':'fornecedor_nome','estoque_analitico_idvendedor':'idvendedor','cliente_fornecedor_nomevendedor':'nomevendedor'}, inplace=True)
        return df
    except Exception as e:
        st.error(f"Ocorreu um erro ao processar o arquivo: {e}")
        st.warning("Verifique se as colunas do arquivo Excel estão corretas.")
        return None

def update_google_sheet(df, sheet_url):
    try:
        # 1. Obter o caminho RELATIVO do arquivo .env
        relative_creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH")
        
        if not relative_creds_path:
            st.error("Erro de Configuração: A variável 'GOOGLE_CREDENTIALS_PATH' não foi encontrada.")
            st.info("Verifique se o arquivo .env existe na raiz do projeto e contém a variável corretamente.")
            return False

        # 2. <<< A CORREÇÃO DEFINITIVA ESTÁ AQUI >>>
        # Transformar o caminho relativo em um caminho ABSOLUTO e à prova de falhas.
        # Ele usa a localização do script 'app.py' como ponto de partida.
        script_dir = os.path.dirname(os.path.abspath(__file__))
        absolute_creds_path = os.path.join(script_dir, relative_creds_path)

        # 3. Usar o caminho ABSOLUTO para autenticar.
        scopes = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_file(absolute_creds_path, scopes=scopes)
        gc = gspread.authorize(creds)
        
        spreadsheet = gc.open_by_url(sheet_url)
        worksheet = spreadsheet.sheet1
        worksheet.clear()
        set_with_dataframe(worksheet, df, include_index=False)
        
        return True
    
    except FileNotFoundError:
        # Mensagem de erro melhorada para mostrar exatamente onde ele procurou.
        st.error(f"Erro Crítico: Arquivo de credenciais NÃO encontrado.")
        st.error(f"Caminho procurado: '{absolute_creds_path}'")
        st.info("Verifique se o caminho no arquivo .env está correto e aponta para um arquivo que existe.")
        return False
    except gspread.exceptions.SpreadsheetNotFound:
        st.error("Erro: Planilha não encontrada. Verifique a URL e as permissões de compartilhamento.")
        return False
    except Exception as e:
        st.error(f"Erro ao conectar com o Google Sheets: {e}")
        st.info("Dica: Verifique se o e-mail da conta de serviço foi compartilhado com a planilha (com permissão de editor).")
        return False

# --- INTERFACE GRÁFICA (STREAMLIT) ---

st.set_page_config(page_title="Atualizador de Base 155", layout="wide")
st.title("🚀 Ferramenta de Atualização da Base 155")
st.markdown("Esta ferramenta automatiza o envio dos dados do relatório CISS para o Google Sheets.")

FOLDER_PATH_FIXO = r"C:\Ambiente de Trabalho\Projetos\Projetos_Profissionais\Ativos\Projeto_BV_Pisos\Projeto_Inventário\projeto_expedicao\base_dados"
SHEET_URL_FIXA = "https://docs.google.com/spreadsheets/d/1ytok0IWxE4b3Clp8n4Mdm1jvZgllbf3wuyWSx2JddFI/edit?usp=sharing"

st.info(f"Pasta de relatórios configurada: `{FOLDER_PATH_FIXO}`")
st.info(f"Planilha Google Sheets configurada: `{SHEET_URL_FIXA}`")

st.header("Execute o processo")
if st.button("Processar e Atualizar Planilha", type="primary"):
    with st.spinner("Buscando o relatório mais recente..."):
        latest_file_path = find_latest_file(FOLDER_PATH_FIXO)
    
    if latest_file_path:
        st.info(f"✅ Relatório mais recente encontrado: `{os.path.basename(latest_file_path)}`")
        
        with st.spinner("Processando os dados..."):
            processed_df = process_data(latest_file_path)
        
        if processed_df is not None:
            st.success("Dados processados com sucesso!")
            st.write("Amostra dos dados tratados:")
            st.dataframe(processed_df.head())
            
            with st.spinner("Conectando ao Google Sheets e atualizando a base..."):
                success = update_google_sheet(processed_df, SHEET_URL_FIXA)
            
            if success:
                st.success("🎉 Planilha Google Sheets atualizada com sucesso!")
                st.balloons()
    else:
        st.error(f"Nenhum arquivo com o padrão '155_DDMMYY.xlsx' foi encontrado na pasta: '{FOLDER_PATH_FIXO}'")