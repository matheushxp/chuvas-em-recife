#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Coleta de Dados - APAC Pernambuco (Pluviometria)
=================================================
Coleta dados pluviométricos da APAC via API/web

Fontes:
- Histórico Pluviométrico: http://dados.apac.pe.gov.br:41120/boletins/historico-pluviometrico/
- Boletim Pluviométrico: http://dados.apac.pe.gov.br:41120/boletins/boletim-pluviometrico/
- Dados das Estações: http://dados.apac.pe.gov.br:41120/dadosApac/

Autor: Engenheiro de Dados
Data: 2026-05-11
"""

import requests
import pandas as pd
import json
import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import time

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constantes - URLs da APAC
BASE_URL_APAC = "http://dados.apac.pe.gov.br:41120"
URL_HISTORICO_PLUVIO = f"{BASE_URL_APAC}/boletins/historico-pluviometrico/"
URL_BOLETIM_PLUVIO = f"{BASE_URL_APAC}/boletins/boletim-pluviometrico/"
URL_DADOS_APAC = f"{BASE_URL_APAC}/dadosApac/"
URL_CEMADEN = f"{BASE_URL_APAC}/cemaden/"
URL_METEOROLOGIA = f"{BASE_URL_APAC}/meteorologia24h/"

# Headers para requisições
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json, text/html, */*',
    'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
}

# Diretório base para salvar os dados
DIRETORIO_DADOS = Path(__file__).parent.parent / "dados" / "brutos"


class ColetorDadosAPAC:
    """
    Classe para coletar dados pluviométricos da APAC.
    
    A APAC fornece diferentes tipos de dados:
    - Histórico pluviométrico (dados históricos por estação)
    - Boletim pluviométrico (dados diários)
    - Dados de estações automáticas (tempo real)
    - Dados meteorológicos
    """
    
    def __init__(self, diretorio_saida: Optional[Path] = None):
        """
        Inicializa o coletor.
        
        Args:
            diretorio_saida: Diretório onde os arquivos serão salvos.
        """
        self.diretorio_saida = diretorio_saida or DIRETORIO_DADOS
        self.diretorio_saida.mkdir(parents=True, exist_ok=True)
        logger.info(f"Diretório de saída: {self.diretorio_saida}")
    
    def buscar_boletim_pluviometrico(self, data_inicio: str = None, 
                                    data_fim: str = None) -> Optional[Dict]:
        """
        Busca dados do boletim pluviométrico.
        
        Args:
            data_inicio: Data no formato YYYY-MM-DD (opcional)
            data_fim: Data no formato YYYY-MM-DD (opcional)
            
        Returns:
            Dicionário com os dados ou None em caso de erro.
        """
        url = URL_BOLETIM_PLUVIO
        
        # A APAC usa formulário, Tentativa de API JSON
        params = {}
        if data_inicio:
            params['data_inicial'] = data_inicio
        if data_fim:
            params['data_final'] = data_fim
        
        logger.info(f"Buscando boletim pluviométrico: {data_inicio} até {data_fim}")
        
        try:
            # Tentar como JSON primeiro
            response = requests.get(
                url, 
                params=params, 
                headers=HEADERS,
                timeout=60
            )
            response.raise_for_status()
            
            # Tentar extrair JSON da resposta
            content_type = response.headers.get('Content-Type', '')
            
            if 'json' in content_type:
                return response.json()
            
            # Se não for JSON, tentarExtrair do HTML
            return self._extrair_boletim_html(response.text)
            
        except requests.RequestException as e:
            logger.error(f"Erro ao buscar boletim: {e}")
            # Retornar URL para consulta manual
            logger.info(f"Consulte manualmente: {url}")
            return None
    
    def _extrair_boletim_html(self, html: str) -> Dict:
        """
        Extrai dados do boletim do HTML.
        
        Args:
            html: Conteúdo HTML da página.
            
        Returns:
            Dicionário com dados extraídos.
        """
        import re
        
        dados = {
            'data_extraido': datetime.now().isoformat(),
            'fonte': URL_BOLETIM_PLUVIO,
            'dados': []
        }
        
        # Padrões de busca no HTML (ajustar conforme estrutura real)
        # Esta lógica pode precisar de ajustes baseados na estrutura real do site
        
        logger.info("Tentando extrair dados do HTML...")
        
        # Procurar por tabelas ou dados em script
        table_match = re.findall(r'<table[^>]*>(.*?)</table>', html, re.DOTALL)
        if table_match:
            logger.info(f"Encontradas {len(table_match)} tabelas")
        
        return dados
    
    def buscar_historico_pluviometrico(self, 
                                     codigoposto: str = None,
                                     datainicio: str = None,
                                     datafim: str = None,
                                     tipo: str = "Mensal") -> Optional[pd.DataFrame]:
        """
        Busca histórico pluviométrico via interface web.
        
        Args:
            codigoposto: Código do posto pluviométrico (opcional)
            datainicio: Data inicial (YYYY-MM-DD)
            datafim: Data final (YYYY-MM-DD)
            tipo: "Mensal" ou "Diário"
            
        Returns:
            DataFrame com os dados ou None.
        """
        url = URL_HISTORICO_PLUVIO
        
        params = {
            'data_inicial': datainicio or '2024-01-01',
            'data_final': datafim or datetime.now().strftime('%Y-%m-%d'),
        }
        
        if codigoposto:
            params['posto'] = codigoposto
        
        logger.info(f"Buscando histórico pluviométrico ({tipo})")
        logger.info(f"  Período: {params['data_inicial']} a {params['data_final']}")
        
        try:
            response = requests.get(
                url, 
                params=params,
                headers=HEADERS,
                timeout=60
            )
            response.raise_for_status()
            
            # Salvar resposta para análise
            caminho_html = self.diretorio_saida / "historico_pluvio.html"
            with open(caminho_html, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            logger.info(f"HTML salvo para análise: {caminho_html}")
            
            # Retornar instructions para buscar dados manualmente
            logger.info("=" * 50)
            logger.info("ATENÇÃO: O histórico pluviométrico requer interação")
            logger.info(f"Execute no navegador: {url}")
            logger.info("Selecione:")
            logger.info("  - Operação: Todas")
            logger.info("  - Posto: Recife ou clique emtodos")
            logger.info("  - Data Inicial: 2020-01-01")
            logger.info("  - Data Final: 2024-12-31")
            logger.info("  - Tipo: Mensal")
            logger.info("Clique em 'Gerar' e baixe o resultado")
            logger.info("=" * 50)
            
            return None
            
        except requests.RequestException as e:
            logger.error(f"Erro ao buscar histórico: {e}")
            return None
    
    def buscar_estacoes_cemaden(self) -> Optional[pd.DataFrame]:
        """
        Busca dados das estações CEMADEN (Centro de Monitoramento eAlertas de Desastres).
        
        Returns:
            DataFrame com dados das estações ou None.
        """
        url = URL_CEMADEN
        
        logger.info("Buscando dados das estações CEMADEN...")
        
        try:
            response = requests.get(url, headers=HEADERS, timeout=60)
            response.raise_for_status()
            
            # Tentar JSON
            try:
                dados = response.json()
                df = pd.DataFrame(dados)
                logger.info(f"Encontrados {len(df)} registros")
                return df
            except:
                logger.info("Dados não estão em formato JSON")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Erro ao buscar estações: {e}")
            return None
    
    def buscar_dados_estacao(self, 
                         codigo_estacao: str,
                         variavel: str = "chuva",
                         data_inicio: str = None,
                         data_fim: str = None) -> Optional[pd.DataFrame]:
        """
        Busca dados de uma estação específica.
        
        Args:
            codigo_estacao: Código da estação (ex: "RE-RECIFE")
            variavel: Variável (chuva, nivel, vazão, etc.)
            data_inicio: Data inicial
            data_fim: Data final
            
        Returns:
            DataFrame com dados da estação.
        """
        # Endpoint depends da estrutura real
        url = f"{URL_DADOS_APAC}estacao/{codigo_estacao}"
        
        params = {
            'variavel': variavel,
            'formato': 'json'
        }
        
        if data_inicio:
            params['inicio'] = data_inicio
        if data_fim:
            params['fim'] = data_fim
        
        logger.info(f"Buscando estação {codigo_estacao} ({variavel})")
        
        try:
            response = requests.get(url, params=params, timeout=60)
            response.raise_for_status()
            
            dados = response.json()
            
            if isinstance(dados, list):
                df = pd.DataFrame(dados)
            elif isinstance(dados, dict):
                df = pd.DataFrame([dados])
            else:
                logger.error("Formato não reconhecido")
                return None
            
            return df
            
        except requests.RequestException as e:
            logger.error(f"Erro: {e}")
            return None
    
    def listar_postos(self) -> List[Dict]:
        """
        Lista postos pluviométricos disponíveis.
        
        Returns:
            Lista de dicionários com info dos postos.
        """
        # Esta função pode variar conforme a API daAPAC
        url = f"{BASE_URL_APAC}/dadosApac/postos"
        
        logger.info("Buscando lista deポスト...")
        
        try:
            response = requests.get(url, headers=HEADERS, timeout=30)
            response.raise_for_status()
            
            dados = response.json()
            return dados if isinstance(dados, list) else []
            
        except:
            # Retornar postos conhecidos de Recife
            logger.info("Usando lista manual de postos de Recife")
            return [
                {"codigo": "RE-RECIFE", "nome": "Recife", "tipo": "Pluviométrico"},
                {"codigo": "RE-PAULA", "nome": "Paulista", "tipo": "Pluviométrico"},
                {"codigo": "RE-OLINDA", "nome": "Olinda", "tipo": "Pluviométrico"},
                {"codigo": "RE-JABOATAO", "nome": "Jaboatão dos Guararapes", "tipo": "Pluviométrico"},
            ]


class ColetorBackupAPAC:
    """
    Alternative para coletar dados daAPAC usando scraping ou dados alternativos.
    
    Fontes alternativas quando a API principal não estiver disponível:
    - INMET (Instituto Nacional de Meteorologia)
    - dados.gov.br
    """
    
    def __init__(self, diretorio_saida: Optional[Path] = None):
        self.diretorio_saida = diretorio_saida or DIRETORIO_DADOS
        self.diretorio_saida.mkdir(parents=True, exist_ok=True)
    
    def buscar_dados_inmet(self, 
                        codigo_estacao: "A301" = "A301",
                        ano: int = None) -> Optional[pd.DataFrame]:
        """
        Busca dados históricos do INMET.
        
        Args:
            codigo_estação: Código da estação INMET (A301 = Recife)
            ano: Ano desejado
            
        Returns:
            DataFrame com dados.
        """
        import warnings
        warnings.filterwarnings('ignore')
        
        # URL de dados historique do INMET
        url = "https://portal.inmet.gov.br/dadoshistoricos"
        
        if ano:
            url = f"https://portal.inmet.gov.br/dadoshistoricos/anobase/{ano}"
        
        logger.info(f"Buscando dados INMET para estação {codigo_estacao}...")
        
        try:
            response = requests.get(url, headers=HEADERS, timeout=30, verify=False)
            
            # O INMET retorna uma página para seleção
            if response.status_code == 200:
                logger.info("Acesse para baixa dados do INMET:")
                logger.info("  1. Acesse: https://portal.inmet.gov.br/dadoshistoricos")
                logger.info("  2. Selecione o Estado: Pernambuco")
                logger.info("  3. Selecione a Estação: Recife (A301)")
                logger.info("  4. Escolha o período")
                logger.info("  5. Clique em 'Baixar dados'")
            
            return None
            
        except requests.RequestException as e:
            logger.error(f"Erro: {e}")
            return None


def main():
    """
    Função principal para execução do script.
    """
    print("=" * 60)
    print("Coleta de Dados - APAC Pernambuco (Pluviometria)")
    print("=" * 60)
    
    # Inicializar coletor
    coletor = ColetorDadosAPAC()
    
    print("\n1. Listando postos pluviométricos...")
    postes = coletor.listar_postos()
    for p in postes[:5]:
        print(f"   - {p.get('nome')} ({p.get('codigo')})")
    
    print("\n2. Buscando dados do boletim pluviométrico...")
    dados_boletim = coletor.buscar_boletim_pluviometrio(
        data_inicio='2024-01-01',
        data_fim='2024-12-31'
    )
    if dados_boletim:
        print(f"   Dados encontrados: {dados_boletim}")
    
    print("\n3. Verificando histórico pluviométrico...")
    coletor.buscar_historico_pluviometrico(
        datainicio='2020-01-01',
        datafim='2024-12-31',
        tipo='Mensal'
    )
    
    print("\n" + "=" * 60)
    print("ATENÇÃO: Alguns dados requerem download manual!")
    print("Consulte: http://dados.apac.pe.gov.br:41120/boletins/")
    print("=" * 60)
    
    # Salvar instructions para acesso futuro
    instrucoes = {
        "fonte": "APAC Pernambuco",
        "urls": {
            "historico_pluviometrico": URL_HISTORICO_PLUVIO,
            "boletim_pluviometrico": URL_BOLETIM_PLUVIO,
            "dados_abertos": URL_DADOS_APAC,
        },
        "instrucoes": [
            "1. Acesse http://dados.apac.pe.gov.br:41120/boletins/historico-pluviometrico/",
            "2. Selecione a mesorregião: Metropolitana do Recife",
            "3. Selecione o posto: Recife",
            "4. Data inicial: 2020-01-01",
            "5. Data final: 2024-12-31",
            "6. Tipo: Mensal",
            "7. Clique em 'Gerar' e baixe o arquivo",
            "8. Salve em dados/brutos/",
        ]
    }
    
    caminho_instrucoes = coletor.diretorio_saida / "instrucoes_apac.json"
    with open(caminho_instrucoes, 'w', encoding='utf-8') as f:
        json.dump(instrucoes, f, indent=2, ensure_ascii=False)
    
    print(f"\nInstruções salvas em: {caminho_instrucoes}")


if __name__ == "__main__":
    main()