# Fundamentus Scraper & Valuation Tool

## Visão Geral
Este projeto é uma ferramenta de automação desenvolvida em Python para extração, processamento e análise de dados fundamentalistas de ações listadas na B3 (Bolsa de Valores do Brasil).

O sistema coleta dados financeiros diretamente do portal *Fundamentus*, consolida as informações em um banco de dados local e aplica metodologias de *Valuation* quantitativo, gerando visualizações gráficas para suporte à tomada de decisão.

## Funcionalidades Principais

### 1. Extração de Dados (Data Scraping)
- **Coleta de Detalhes:** Módulo de alta performance (`FundamentusDetailsScrape.py`) que utiliza `requests` e `BeautifulSoup` para extrair indicadores como P/L, ROE, Margem Líquida, Dívida Bruta/PL, entre outros.
- **Tratamento de Dados:** Algoritmos de limpeza que normalizam formatações numéricas brasileiras, convertem datas e tratam inconsistências de rotulagem (ex: dados de 12 meses vs. 3 meses).
- **Gestão de Drivers:** Integração com `webdriver-manager` para gerenciamento automático de drivers do Google Chrome, eliminando a necessidade de configuração manual de binários.

### 2. Análise Quantitativa (Analytical Engine)
- **Consolidação de Base:** O módulo `TheMagicFormula.py` agrega todos os arquivos individuais extraídos em um *Data Warehouse* local (`DatabaseResume.xlsx`).
- **Metodologias Aplicadas:**
  - **Magic Formula (Joel Greenblatt):** Classificação baseada no binômio Qualidade (ROA/ROE) vs. Preço (P/L).
  - **Acquirer's Multiple (Tobias Carlisle):** Análise focada no valor da firma (EV/EBITDA) em relação à rentabilidade operacional.
- **Visualização de Dados:** Geração automática de gráficos de dispersão (Scatter Plots) em formato vetorial (SVG) para identificação visual de oportunidades.

## Estrutura do Projeto

O projeto segue uma arquitetura modular organizada da seguinte forma:

```text
.
├── LabCode
│   ├── FUNDAMENTUS_SCRAPER
│   │   └── FundamentusDetailsScrape.py  # Script de extração de dados
│   ├── METHODS
│   │   └── MagicFormula
│   │       ├── TheMagicFormula.py       # Script de análise e geração de gráficos
│   │       └── Results/                 # Saída dos gráficos gerados
│   └── MARKET_DATABASE
│       ├── Consult
│       │   └── TICKERS.xlsx             # Lista mestre de ativos a serem monitorados
│       └── FUNDAMENTUS_DB
│           └── Details/                 # Repositório dos dados brutos (Excel) por ativo
````

## Pré-requisitos

Certifique-se de ter o Python 3.10 ou superior instalado. As dependências do projeto são:

```bash
pip install pandas selenium beautifulsoup4 requests matplotlib tqdm webdriver-manager openpyxl lxml
```

## Guia de Instalação e Execução

### 1\. Configuração Inicial

Certifique-se de que o arquivo `TICKERS.xlsx` contendo a lista de ativos (código da ação na coluna 'TICKER') esteja presente no diretório `LabCode/MARKET_DATABASE/Consult/`.

### 2\. Executar a Coleta de Dados

Para atualizar a base de dados com as informações mais recentes do mercado:

1.  Navegue até o diretório do scraper:
    ```bash
    cd LabCode/FUNDAMENTUS_SCRAPER
    ```
2.  Execute o script:
    ```bash
    python FundamentusDetailsScrape.py
    ```
    *O sistema processará a lista de ativos e salvará os arquivos individuais na pasta `Details`.*

### 3\. Executar a Análise

Para consolidar os dados e gerar os gráficos de *valuation*:

1.  Navegue até o diretório de métodos:
    ```bash
    cd ../METHODS/MagicFormula
    ```
    *(Ajuste o caminho conforme seu diretório atual)*
2.  Execute o script de análise:
    ```bash
    python TheMagicFormula.py
    ```

**Nota sobre Cache:** O sistema gera um arquivo `DatabaseResume.xlsx` na pasta do script para acelerar execuções futuras. Se desejar forçar o processamento de novos dados baixados, delete este arquivo antes de rodar a análise.

## Resultados

Os outputs da análise (gráficos comparativos P/L vs ROA e EV/EBITDA vs ROA) serão salvos automaticamente no diretório:
`LabCode/METHODS/MagicFormula/Results/`

-----

**Disclaimer:** Este software é uma ferramenta educacional e de análise de dados. As informações geradas não constituem recomendação de compra ou venda de ativos.

```
```