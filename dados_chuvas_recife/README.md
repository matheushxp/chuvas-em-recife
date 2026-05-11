# Dados de Chuvas em Recife-PE

Projeto de análise do impacto das chuvas em Recife-PE. Este repositório contém scripts para coleta de dados da **APAC** (dados pluviométricos) e do **Portal de Dados Abertos do Recife** (ocorrências da Defesa Civil).

## 📋 Contexto do Projeto

**Tema:** Impacto das chuvas em Recife-PE  
**Hipótese:** O aumento dos índices pluviométricos contribui para o crescimento de alagamentos

### Fontes de Dados

| Fonte | Dados | URL |
|-------|-------|-----|
| **APAC Pernambuco** | Histórico pluviométrico, boletins diários | http://dados.apac.pe.gov.br:41120 |
| **Defesa Civil Recife** | Ocorrências (alagamentos, deslizamentos, vistorias) | https://dados.recife.pe.gov.br |

## 📂 Estrutura do Projeto

```
dados_chuvas_recife/
├── dados/
│   ├── brutos/           # Dados originais baixados
│   │   ├── defesa_civil_atendimentos_2024.csv
│   │   └── ...
│   ├── processados/      # Dados processados/analisados
│   └── output/           # Resultados da análise
├── logs/                # Logs de execução
├── scripts/
│   ├── coleta_dados_recife.py   # Coleta do portal do Recife
│   ├── coleta_dados_apac.py    # Coleta da APAC
│   ├── leitura_analise.py      # Análise inicial
│   └── executar_coleta.bat     # Script batch (Windows)
├── README.md
└── AGENTS.md
```

## 🚀 Como Usar

### Pré-requisitos

- **Python 3.8+**
- Bibliotecas: `requests`, `pandas`

### Instalação

1. Clone ou baixe este repositório

2. Crie um ambiente virtual (opcional):
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

3. Instale as dependências:
```bash
pip install requests pandas
```

### Execução

#### Opção 1: Script Batch (Windows)
```bash
executar_coleta.bat
```

#### Opção 2: Python Direto

```bash
# Etapa 1: Coletar dados da Defesa Civil do Recife
python scripts\coleta_dados_recife.py

# Etapa 2: Coletar dados da APAC
python scripts\coleta_dados_apac.py

# Etapa 3: Analisar dados
python scripts\leitura_analise.py
```

## 📊 Datasets Coletados

### 1. Registro de Atendimentos da Defesa Civil do Recife

| Ano | Registros | Descrição |
|-----|-----------|-----------|
| 2024 | ~300.000 | Ocorrências, vistorias, lonas |
| 2023 | ~280.000 | Mesmo formato |
| 2022 | ~250.000 | Mesmo formato |

**Campos típicos:**
- `data_atendimento`: Data do chamado
- `tipo_ocorrencia`: Tipo (alagamento, deslizamento, etc.)
- `bairro`: Localização
- `regional`: Regional administrativa
- `natureza_servico`: Tipo de serviço realizado
- `acao`: Ação tomada

### 2. Dados Pluviométricos (APAC)

Para acessar os dados históricos da APAC:

1. Acesse: http://dados.apac.pe.gov.br:41120/boletins/historico-pluviometrico/
2. Selecione:
   - Operação: Todas
   - Mesorregião: Metropolitana do Recife
   - Posto: Recife
   - Data Inicial: 2020-01-01
   - Data Final: 2024-12-31
   - Tipo: Mensal
3. Clique em "Gerar" e baixe o CSV

## 🔍 Análise Inicial

O script de análise (`leitura_analise.py`) executa:

1. **Schema**: Lista tipos de colunas, nulos, valores únicos
2. **Sample**: Primeiras 10 linhas de cada dataset
3. **Problemas**: Identifica:
   - Colunas com +50% nulos
   - Formatos de data inconsistentes
   - Encoding problems
   - Separadores diferentes

## ⚠️ Problemas Conhecidos

1. **APAC**: API requer interação web - baixe manualmente
2. **Defesa Civil**: Dados atualizados trimestralmente
3. **Encoding**: Alguns CSVs podem usar Latin-1

## 📝 Próximos Passos para o Analista

1. **Unificação**: Juntar dados de chuva com ocorrências por data
2. **Correção**: Tratar encoding, formatar datas
3. **Enriquecimento**: Adicionar dados de feriados, fins de semana
4. **Análise**:
   - Correlação entre pluviosidade e alagamentos
   - Identificação de pontos críticos
   - Análise temporal (hora/dia/semana)
5. **Visualização**: Gráficos e mapas

## 📞 Suporte

- **APAC**: monitoramento@apac.pe.gov.br
- **Portal Recife**: dadosabertos@recife.pe.gov.br
- **GitHub Issues**: Abra um ticket para problemas

## 📜 Licença

Dados abertos - Creative Commons (ODbL). Consulte os portais para termos específicos.

---

**Autor:** Engenheiro de Dados  
**Data:** Mayo 2026