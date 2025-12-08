# -*- coding: utf-8 -*-
"""
Created on Sat Oct 30 15:46:39 2021
Refactored on: Dec 07 2025

@author: Deni
@modifier: Primo Primata & Gemini

Descrição:
    Processa os arquivos Excel gerados pelo Scraper, consolida em um banco de dados
    e gera gráficos de análise com o ESTILO VISUAL CLÁSSICO (Original).
"""

import pandas as pd
import datetime as dt
import os
import pathlib
import matplotlib.pyplot as plt
import numpy as np # Necessário para o linspace do gráfico original
import random as rd
from tqdm import tqdm # pip install tqdm

# Configuração de Logs
try:
    from Log import LOG
except ImportError:
    def LOG(msg, echo=True):
        if echo: print(msg)

# --- CONFIGURAÇÃO DE CAMINHOS (PATHLIB) ---
SCRIPT_DIR = pathlib.Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent.parent

# Caminhos de Entrada
RAW_FUNDAMENTUS_DETAILS = PROJECT_ROOT / 'MARKET_DATABASE' / 'FUNDAMENTUS_DB' / 'Details'
TICKERS_FILE = PROJECT_ROOT / 'MARKET_DATABASE' / 'Consult' / 'TICKERS.xlsx'

# Caminhos de Saída
RESULTS_DIR = SCRIPT_DIR / 'Results'
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Arquivo de Cache (Consolidado)
DATABASE_RESUME_PATH = SCRIPT_DIR / 'DatabaseResume.xlsx'

# --- CONFIGURAÇÃO GRÁFICA ORIGINAL (RESTAURADA) ---
global L, H, m 
m = 5
L = 8 * m
H = 6 * m
TS = dt.datetime.now().strftime('[%Y-%m-%d.%H.%M.%S]')


def LoadTickerInfoTable():
    if not TICKERS_FILE.exists():
        print(f'Erro: Arquivo não encontrado: {TICKERS_FILE}')
        return pd.DataFrame()
    try:
        print(f'Carregando Tickers de: {TICKERS_FILE.name}')
        return pd.read_excel(TICKERS_FILE, sheet_name='DATA')
    except Exception as e:
        print(f'Erro ao carregar Tickers: {e}')
        return pd.DataFrame()


def LoadDetailsFile(path):
    try:
        df = pd.read_excel(path, sheet_name="DETAILS", index_col=0)
    except:
        return None

    for i in range(len(df)):
        try:
            df.loc[i, 'data'] = float(df['data'].iloc[i])
        except:
            pass
        
        try:
            label = df['label'].iloc[i]
            val = df['data'].iloc[i]
            if label in ['Data últ cot', 'Últ balanço processado']:
                if isinstance(val, str):
                    df.loc[i, 'data'] = dt.datetime.strptime(val, '%d/%m/%Y')
        except:
            pass

    data = list(df['data'])
    columns = list(df['label'])
    return pd.DataFrame(data=[data], columns=columns)


def GetShareTickers(Tickers):
    """Filtra apenas ações (SHARE) se a coluna TYPE existir."""
    if 'TYPE' in Tickers.columns:
        return Tickers[Tickers['TYPE']=='SHARE'].copy()
    return Tickers


def GetConsolidatedData(tickers_list):
    """Gerencia o Cache com concatenação segura."""
    if DATABASE_RESUME_PATH.exists():
        print(f"--- Cache Encontrado: {DATABASE_RESUME_PATH.name} ---")
        print("Usando dados do cache para agilizar. Para atualizar, delete o arquivo DatabaseResume.xlsx.")
        try:
            return pd.read_excel(DATABASE_RESUME_PATH, index_col=0)
        except Exception as e:
            print(f"Erro no cache: {e}. Recriando...")

    print("--- Iniciando Consolidação (Isso pode demorar) ---")
    data_list = []
    
    for ticker in tqdm(tickers_list, desc="Lendo arquivos"):
        file_path = RAW_FUNDAMENTUS_DETAILS / f'{ticker}.xlsx'
        if file_path.exists():
            line = LoadDetailsFile(file_path)
            if line is not None and not line.empty:
                if "Data últ cot" in line.columns:
                    # Coerce evita o erro de datetime.time
                    line["Data últ cot"] = pd.to_datetime(line["Data últ cot"], errors='coerce')
                data_list.append(line)
    
    if not data_list:
        print("Nenhum dado encontrado.")
        return pd.DataFrame()

    consolidated_df = pd.concat(data_list, ignore_index=True)
    
    try:
        consolidated_df.to_excel(DATABASE_RESUME_PATH)
        print(f"Cache salvo em: {DATABASE_RESUME_PATH}")
    except Exception as e:
        print(f"Erro ao salvar cache: {e}")

    return consolidated_df


def PerformMagic(df_data):
    """Gera o gráfico Magic Formula com VISUAL ORIGINAL."""
    print("Gerando gráfico Magic Formula...")
    
    required = ["Papel", "P/L", "EBIT / Ativo", "Data últ cot", "Patrim. Líq"]
    if not all(col in df_data.columns for col in required):
        print(f"Colunas faltando: {[c for c in required if c not in df_data.columns]}")
        return

    df = df_data.dropna(subset=required).copy()
    
    this_year = dt.datetime.now().year
    this_month = dt.datetime.now().month
    df = df[df["Data últ cot"] > dt.datetime(this_year, this_month, 1)]
    df.reset_index(drop=True, inplace=True)

    # Dados
    tn = df["Papel"]
    PE = pd.to_numeric(df["P/L"], errors='coerce')
    ROA = pd.to_numeric(df["EBIT / Ativo"], errors='coerce')
    PL = pd.to_numeric(df["Patrim. Líq"], errors='coerce')

    # --- CONFIGURAÇÃO VISUAL ORIGINAL ---
    global L, H, m
    
    plt.figure(figsize=(L/m, H/m)) # Garante nova figura
    plt.clf()
    
    xmin, xmax = 0, 10
    ymin, ymax = 0, 100
    
    plt.xlim(xmin, xmax)
    plt.ylim(ymin, ymax)
    plt.xlabel('P/E')
    plt.ylabel('ROA')
    
    plt.xticks(ticks=np.linspace(xmin, xmax, 20))
    plt.yticks(ticks=np.linspace(ymin, ymax, 20))
    
    plt.rc('font', size=1*m)
    plt.rc('lines', linewidth=1)
    plt.grid()

    Vmax = 0 * (ymax - ymin) / 80
    Hmax = 0 * (xmax - xmin) / 80

    for i in range(len(tn)):
        if pd.isna(PE[i]) or pd.isna(ROA[i]): continue
        if PL[i] < 0: t = f'{tn[i]}(-)'
        else: t = f'{tn[i]}(+)'
        
        x = PE[i]
        y = ROA[i]
        
        max_c = 128
        r = rd.randint(0, max_c) / float(max_c)
        g = rd.randint(0, max_c) / float(max_c)
        b = rd.randint(0, max_c) / float(max_c)
        color = (r, g, b)
        
        rot = rd.randrange(-90, 90)
        
        if x < xmin or x > xmax or y < ymin or y > ymax:
            continue
            
        plt.annotate(f'{t}', 
                     xy=(x + rd.randrange(-1, 1)*Hmax, y + rd.randrange(-1, 1)*Vmax), 
                     textcoords='data', 
                     fontsize=2*m, 
                     color=color, 
                     alpha=0.9, 
                     rotation=rot)
        
        plt.scatter(PE[i], ROA[i], s=5*m, alpha=0.5, color=color)

    fname = RESULTS_DIR / f'{TS} MagicResult (PE vs ROA).svg'
    
    plt.gcf().set_size_inches(L, H)
    plt.savefig(fname, dpi=600)
    # plt.show()
    print(f"Salvo: {fname.name}")


def AcquirersMult(df_data):
    """Gera o gráfico Acquirers Multiple com VISUAL ORIGINAL."""
    print("Gerando gráfico Acquirers Multiple...")

    required = ["Papel", "EV / EBITDA", "EBIT / Ativo", "Data últ cot", "Patrim. Líq"]
    if not all(col in df_data.columns for col in required):
        print(f"Colunas faltando: {[c for c in required if c not in df_data.columns]}")
        return

    df_data["EV / EBITDA"] = pd.to_numeric(df_data["EV / EBITDA"], errors='coerce')
    df = df_data.dropna(subset=required).copy()
    
    this_year = dt.datetime.now().year
    this_month = dt.datetime.now().month
    df = df[df["Data últ cot"] > dt.datetime(this_year, this_month, 1)]
    df.reset_index(drop=True, inplace=True)

    tn = df["Papel"]
    AM = df["EV / EBITDA"]
    ROA = pd.to_numeric(df["EBIT / Ativo"], errors='coerce')
    PL = pd.to_numeric(df["Patrim. Líq"], errors='coerce')

    # --- CONFIGURAÇÃO VISUAL ORIGINAL ---
    global L, H, m
    
    plt.figure(figsize=(L/m, H/m))
    plt.clf() 
    
    xmin, xmax = 0, 10
    ymin, ymax = 0, 100
    
    plt.xlim(xmin, xmax)
    plt.ylim(ymin, ymax)
    plt.xlabel('EV/EBITDA')
    plt.ylabel('ROA')
    
    plt.xticks(ticks=np.linspace(xmin, xmax, 20))
    plt.yticks(ticks=np.linspace(ymin, ymax, 20))
    plt.rc('font', size=1*m)
    plt.rc('lines', linewidth=1)
    plt.grid()

    Vmax = 0 * (ymax - ymin) / 80
    Hmax = 0 * (xmax - xmin) / 80

    for i in range(len(tn)):
        if pd.isna(AM[i]) or pd.isna(ROA[i]): continue
        if PL[i] < 0: t = f'{tn[i]}(-)'
        else: t = f'{tn[i]}(+)'
        
        x = AM[i]
        y = ROA[i]
        
        max_c = 128
        r = rd.randint(0, max_c) / float(max_c)
        g = rd.randint(0, max_c) / float(max_c)
        b = rd.randint(0, max_c) / float(max_c)
        color = (r, g, b)
        
        rot = rd.randrange(-90, 90)
        
        if x < xmin or x > xmax or y < ymin or y > ymax:
            continue
            
        plt.annotate(f'{t}', 
                     xy=(x + rd.randrange(-1, 1)*Hmax, y + rd.randrange(-1, 1)*Vmax), 
                     textcoords='data', 
                     fontsize=2*m, 
                     color=color, 
                     alpha=0.9, 
                     rotation=rot)
        
        plt.scatter(AM[i], ROA[i], s=5*m, alpha=0.5, color=color)

    fname = RESULTS_DIR / f'{TS} Acquirers Multiple (EV-EBITDA vs ROA).svg'
    
    plt.gcf().set_size_inches(L, H)
    plt.savefig(fname, dpi=600)
    # plt.show()
    print(f"Salvo: {fname.name}")


# --- EXECUÇÃO ---
if __name__ == "__main__":
    print("=== Iniciando Análise (Visual Clássico) ===")
    
    Tickers = LoadTickerInfoTable()
    if not Tickers.empty:
        # Se a coluna TYPE existir, usa a função GetShareTickers, senão usa tudo
        ShareTickers = GetShareTickers(Tickers) if 'TYPE' in Tickers.columns else Tickers
        
        # Consolida
        consolidated_data = GetConsolidatedData(ShareTickers['TICKER'])
        
        # Plota
        if not consolidated_data.empty:
            PerformMagic(consolidated_data)
            AcquirersMult(consolidated_data)
            print("\n=== Processo Concluído! ===")
            print(f"Gráficos salvos em: {RESULTS_DIR}")
        else:
            print("Sem dados para plotar.")
    else:
        print("Tabela de Tickers vazia.")