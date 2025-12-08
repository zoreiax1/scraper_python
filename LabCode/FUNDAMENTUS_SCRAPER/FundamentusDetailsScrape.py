# -*- coding: utf-8 -*-
"""
Created on Sat Oct 30 18:10:14 2021
Refactored on: Dec 07 2025

@author: Deni
@modifier: Primo Primata & Gemini

Descrição:
    Scraper detalhado do site Fundamentus.
    Coleta indicadores fundamentalistas (P/L, ROE, Dívida, etc.) para uma lista de ativos.
    Salva os resultados em arquivos Excel individuais.
"""

############################################################
# --- 1. IMPORTAÇÃO DE BIBLIOTECAS ---
############################################################

# Bibliotecas Padrão do Python
import os
import time
import pathlib
import datetime as dt

# Bibliotecas de Terceiros (Instalação necessária)
import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager # pip install webdriver-manager

# Bibliotecas Locais (Log)
try:
    from Log import LOG
except ImportError:
    def LOG(msg):
        print(msg)

############################################################
# --- 2. CONFIGURAÇÃO DE AMBIENTE E DIRETÓRIOS ---
############################################################

# Identifica a pasta onde este script está rodando
ROOT_DIR = pathlib.Path(__file__).parent.absolute()
PROJECT_DIR = ROOT_DIR.parent

# URLs e Templates
URL_TEMPLATE = 'https://www.fundamentus.com.br/detalhes.php?papel={ticker}'

# Configuração de Pastas de Saída
DATA_DIR = f'{ROOT_DIR}\\DATA_FILES'
DOWNLOAD_DIR = os.path.join(PROJECT_DIR, 'MARKET_DATABASE', 'FUNDAMENTUS_DB', 'Details')

# Garante que a pasta de destino existe
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

############################################################
# --- 3. FUNÇÕES AUXILIARES E SELENIUM (GERENCIADO) ---
############################################################

def Start():
    """
    Inicia o driver do Google Chrome automaticamente.
    Utiliza o 'webdriver_manager' para baixar o driver compatível com o navegador instalado.
    Não requer arquivos .exe na pasta do projeto.
    """
    print("Iniciando configuração do Chrome Driver...")
    
    chrome_options = Options()
    # chrome_options.add_argument("--headless") # Descomente para rodar sem abrir janela
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Configuração automática do Driver (Adeus pasta BrowserDrivers!)
    service = ChromeService(ChromeDriverManager().install())
    
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def Kill(driver):
    """Fecha o navegador de forma segura."""
    if driver:
        driver.quit()


def GetDetailsPageURL(ticker):
    """Gera a URL direta para o ativo."""
    return f'https://www.fundamentus.com.br/detalhes.php?papel={ticker}'


def LoadTickerInfoTable():
    """
    Carrega a tabela de Tickers do arquivo Excel mestre.
    Caminho: MARKET_DATABASE/Consult/TICKERS.xlsx
    """
    Tickers_Info_Table_File_Path = os.path.join(PROJECT_DIR, 'MARKET_DATABASE', 'Consult', 'TICKERS.xlsx')
    try:
        print(f'Loading [{Tickers_Info_Table_File_Path}]')
        TickerInfoTable = pd.read_excel(Tickers_Info_Table_File_Path, sheet_name='DATA')
        return TickerInfoTable.copy()
    except Exception as e:
        print(f'Error Loading [{Tickers_Info_Table_File_Path}]: {e}')
        return pd.DataFrame()

############################################################
# --- 4. CORE: SCRAPER (BEAUTIFULSOUP + REQUESTS) ---
############################################################

def getDetailsData(Tickers):
    """
    Função principal de extração.
    Acessa o HTML da página via Requests (Método Ágil), processa tabelas, 
    limpa dados numéricos e trata duplicidade de rótulos.
    """
    # Headers para simular um navegador real e evitar bloqueio 403
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Encoding": "gzip, deflate",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Connection": "close",
        "Upgrade-Insecure-Requests": "1"
    }
    
    DataSet = []
    tcount = 0
    total = len(Tickers)

    for ticker in Tickers:
        skipTicker = False
        URL = GetDetailsPageURL(ticker)
        tcount += 1
        
        # Log de progresso
        msg = f'{ticker} - {tcount}/{total} ({round(tcount*100/total, 2)}%)'
        LOG(msg)

        # Tentativa de conexão
        err = True
        retry_limit = 3 
        tries = 0
        r = None

        while err and tries < retry_limit:
            try:
                r = requests.get(URL, headers=headers)
                if r.status_code == 200:
                    err = False
                else:
                    raise Exception(f"Status Code: {r.status_code}")
            except Exception as e:
                print(f"Request error: {ticker} {URL}. Retrying... ({e})")
                time.sleep(2)
                tries += 1
        
        if err: 
            print(f"Skipping {ticker} due to connection failure.")
            continue

        # Processamento do HTML
        content = r.content
        soup = BeautifulSoup(content, features="lxml")

        if soup.text.find('Nenhum papel encontrado') >= 0:
            LOG(f'\t{ticker} not found... skipping')
            continue

        DataTable = pd.DataFrame(columns=['label', 'data'])

        # Varredura das tabelas HTML
        for tr in soup.find_all('tr'):
            if skipTicker:
                continue
            
            for td in tr.find_all('td'):
                try:
                    if 'class' in td.attrs:
                        if td['class'][0] == 'label':
                            label = td.find('span', attrs={'class': 'txt'}).text
                        elif td['class'][0] == 'data':
                            try:
                                data = td.find('span', attrs={'class': 'txt'}).text
                            except:
                                data = ''
                                continue
                            
                            new_row = pd.DataFrame([[label, data]], columns=DataTable.columns)
                            DataTable = pd.concat([DataTable, new_row], ignore_index=True)
                except:
                    pass

        # --- FASE DE LIMPEZA E FORMATAÇÃO ---
        DataTable.index = range(0, len(DataTable))
        
        # Flags para controlar a renomeação de colunas duplicadas
        RL12m, RL3m = True, True
        EBIT12m, EBIT3m = True, True
        LL12m, LL3m = True, True
        RIF12m, RIF3m = True, True
        RS12m, RS3m = True, True
        R12m, R3m = True, True
        VA12m, VA3m = True, True
        FFO12m, FFO3m = True, True
        RD12m, RD3m = True, True

        for i in range(0, len(DataTable)):
            current_label = DataTable['label'].iloc[i]
            current_data = str(DataTable['data'].iloc[i])

            # 1. Limpeza de formatação numérica
            if current_label not in ['Setor', 'Subsetor']:
                current_data = current_data.replace('\n', '').replace('.', '').replace(',', '.')
                DataTable.loc[i, 'data'] = current_data

            if '%' in current_data:
                DataTable.loc[i, 'data'] = current_data.replace('%', '')

            try:
                DataTable.loc[i, 'data'] = float(DataTable['data'].iloc[i])
            except:
                pass

            # 2. Converter Datas
            try:
                if current_label in ['Data últ cot', 'Últ balanço processado']:
                    DataTable.loc[i, 'data'] = dt.datetime.strptime(DataTable['data'].iloc[i], '%d/%m/%Y')
            except:
                pass

            # 3. Renomeação de Duplicatas (Mantendo lógica original)
            if current_label == 'Receita Líquida':
                if RL12m:
                    DataTable.loc[i, 'label'] = 'Receita Líquida 12m'
                    DataTable.loc[i, 'data'] = 'Receita Líquida 12m'
                    RL12m = False
                elif RL3m:
                    DataTable.loc[i, 'label'] = 'Receita Líquida 3m'
                    DataTable.loc[i, 'data'] = 'Receita Líquida 3m'
                    RL3m = False
            elif current_label == 'EBIT':
                if EBIT12m: DataTable.loc[i, 'label'] = 'EBIT 12m'; DataTable.loc[i, 'data'] = 'EBIT 12m'; EBIT12m = False
                elif EBIT3m: DataTable.loc[i, 'label'] = 'EBIT 3m'; DataTable.loc[i, 'data'] = 'EBIT 3m'; EBIT3m = False
            elif current_label == 'Lucro Líquido':
                if LL12m: DataTable.loc[i, 'label'] = 'Lucro Líquido 12m'; DataTable.loc[i, 'data'] = 'Lucro Líquido 12m'; LL12m = False
                elif LL3m: DataTable.loc[i, 'label'] = 'Lucro Líquido 3m'; DataTable.loc[i, 'data'] = 'Lucro Líquido 3m'; LL3m = False
            elif current_label == 'Result Int Financ':
                if RIF12m: DataTable.loc[i, 'label'] = 'Result Int Financ 12m'; DataTable.loc[i, 'data'] = 'Result Int Financ 12m'; RIF12m = False
                elif RIF3m: DataTable.loc[i, 'label'] = 'Result Int Financ 3m'; DataTable.loc[i, 'data'] = 'Result Int Financ 3m'; RIF3m = False
            elif current_label == 'Rec Serviços':
                if RS12m: DataTable.loc[i, 'label'] = 'Rec Serviço 12m'; DataTable.loc[i, 'data'] = 'Rec Serviço 12m'; RS12m = False
                elif RS3m: DataTable.loc[i, 'label'] = 'Rec Serviço 3m'; DataTable.loc[i, 'data'] = 'Rec Serviço 3m'; RS3m = False
            elif current_label == 'Receita':
                if R12m: DataTable.loc[i, 'label'] = 'Receita 12m'; DataTable.loc[i, 'data'] = 'Receita 12m'; R12m = False
                elif R3m: DataTable.loc[i, 'label'] = 'Receita 3m'; DataTable.loc[i, 'data'] = 'Receita 3m'; R3m = False
            elif current_label == 'Venda de ativos':
                if VA12m: DataTable.loc[i, 'label'] = 'Venda de ativos 12m'; DataTable.loc[i, 'data'] = 'Venda de ativos 12m'; VA12m = False
                elif VA3m: DataTable.loc[i, 'label'] = 'Venda de ativos 3m'; DataTable.loc[i, 'data'] = 'Venda de ativos 3m'; VA3m = False
            elif current_label == 'FFO':
                if FFO12m: DataTable.loc[i, 'label'] = 'FFO 12m'; DataTable.loc[i, 'data'] = 'FFO 12m'; FFO12m = False
                elif FFO3m: DataTable.loc[i, 'label'] = 'FFO 3m'; DataTable.loc[i, 'data'] = 'FFO 3m'; FFO3m = False
            elif current_label == 'Rend. Distribuído':
                if RD12m: DataTable.loc[i, 'label'] = 'Rend. Distribuído 12m'; DataTable.loc[i, 'data'] = 'Rend. Distribuído 12m'; RD12m = False
                elif RD3m: DataTable.loc[i, 'label'] = 'Rend. Distribuído 3m'; DataTable.loc[i, 'data'] = 'Rend. Distribuído 3m'; RD3m = False

        # Verifica duplicatas (Log apenas)
        duplicatedLabelTest = DataTable[DataTable.duplicated(keep=False, subset=['label', 'data'])]
        if len(duplicatedLabelTest) > 0:
            LOG(f'Duplicated columns in {ticker} {duplicatedLabelTest}')

        # Salva o arquivo Excel
        filename = f'{ticker}'
        save_path = os.path.join(DOWNLOAD_DIR, f'{filename}.xlsx')
        try:
            DataTable.to_excel(save_path, sheet_name='DETAILS')
        except Exception as e:
            print(f"Erro ao salvar {save_path}: {e}")
            
        DataSet.append(DataTable)
    
    return DataSet

############################################################
# --- 5. EXECUÇÃO PRINCIPAL ---
############################################################

if __name__ == "__main__":
    # Carrega a tabela de tickers
    tickerTable = LoadTickerInfoTable()

    if not tickerTable.empty:
        tickers = tickerTable['TICKER']
        
        # ATENÇÃO: Descomente a linha abaixo se quiser testar apenas com 5 ações
        # tickers = tickers[:5] 
        
        print(f"Iniciando coleta para {len(tickers)} ativos...")
        dataTickers = getDetailsData(tickers)
        print("Processo finalizado.")
    else:
        print("Nenhum ticker carregado ou arquivo não encontrado.")