#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Coleta de Dados - Portal de Dados Abertos do Recife
================================================================
Coleta dados da Defesa Civil do Recife via API CKAN

Dataset: Registro de Atendimentos da Defesa Civil
URL: https://dados.recife.pe.gov.br/dataset/registro-de-atendimentos-da-defesa-civil

Autor: Engenheiro de Dados
Data: 2026-05-11
"""

import requests
import pandas as pd
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constantes
BASE_URL = "https://dados.recife.pe.gov.br/api/3/action/"
DATASET_ID = "registro-de-atendimentos-da-defesa-civil"
ANOS_DISPONIVEIS = list(range(2014, 2026))  # 2014 a 2025

# Diretório base para salvar os dados
DIRETORIO_DADOS = Path(__file__).parent.parent / "dados" / "brutos"


class ColetorDadosRecife:
    """
    Classe para coletar dados do portal de dados abertos do Recife.
    
    Utiliza a API CKAN para acessar os datasets disponíveis.
    """
    
    def __init__(self, diretorio_saida: Optional[Path] = None):
        """
        Inicializa o coletor.
        
        Args:
            diretorio_saida: Diretório onde os arquivos serão salvos.
                           Se None, usa o diretório padrão.
        """
        self.diretorio_saida = diretorio_saida or DIRETORIO_DADOS
        self.diretorio_saida.mkdir(parents=True, exist_ok=True)
        logger.info(f"Diretório de saída: {self.diretorio_saida}")
    
    def listar_datasets(self) -> List[str]:
        """
        Lista todos os datasets disponíveis no portal.
        
        Returns:
            Lista com os nomes dos datasets.
        """
        url = f"{BASE_URL}package_list"
        
        try:
            logger.info("Consultando lista de datasets...")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            datasets = data.get('result', [])
            logger.info(f"Encontrados {len(datasets)} datasets")
            return datasets
            
        except requests.RequestException as e:
            logger.error(f"Erro ao listar datasets: {e}")
            return []
    
    def buscar_info_dataset(self, dataset_id: str = DATASET_ID) -> Dict:
        """
        Obtém informações sobre um dataset específico.
        
        Args:
            dataset_id: ID do dataset.
            
        Returns:
            Dicionário com informações do dataset.
        """
        url = f"{BASE_URL}package_show"
        params = {'id': dataset_id}
        
        try:
            logger.info(f"Buscando informações do dataset: {dataset_id}")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            logger.info("Dataset encontrado com sucesso")
            return data.get('result', {})
            
        except requests.RequestException as e:
            logger.error(f"Erro ao buscar dataset: {e}")
            return {}
    
    def listar_recursos(self, dataset_id: str = DATASET_ID) -> List[Dict]:
        """
        Lista os recursos disponíveis em um dataset.
        
        Args:
            dataset_id: ID do dataset.
            
        Returns:
            Lista de recursos com metadados.
        """
        info = self.buscar_info_dataset(dataset_id)
        recursos = info.get('resources', [])
        
        logger.info(f"Encontrados {len(recursos)} recursos")
        for r in recursos:
            logger.info(f"  - {r.get('name')} ({r.get('format')})")
        
        return recursos
    
    def coletar_dados_anual(self, ano: int, dataset_id: str = DATASET_ID) -> Tuple[Optional[pd.DataFrame], str]:
        """
        Coleta dados de um ano específico.
        
        Args:
            ano: Ano desejado (ex: 2024).
            dataset_id: ID do dataset.
            
        Returns:
            Tupla (DataFrame com dados, caminho do arquivo) ou (None, mensagem_erro).
        """
        # Buscar o recurso para o ano específico
        info = self.buscar_info_dataset(dataset_id)
        
        recurso_encontrado = None
        for recurso in info.get('resources', []):
            nome = recurso.get('name', '').lower()
            # Match com padrão "Atendimentos 2024" ou similar
            if f'atendimentos {ano}' in nome or f'atendimentos-{ano}' in nome:
                recurso_encontrado = recurso
                break
        
        if not recurso_encontrado:
            msg = f"Recurso não encontrado para o ano {ano}"
            logger.warning(msg)
            return None, msg
        
        # Baixar o arquivo
        url_download = recurso_encontrado.get('url')
        nome_arquivo = recurso_encontrado.get('name', f'atendimentos-{ano}.csv')
        
        logger.info(f"Baixando {nome_arquivo}...")
        
        try:
            response = requests.get(url_download, timeout=60)
            response.raise_for_status()
            
            # Salvar arquivo
            caminho_arquivo = self.diretorio_saida / f"defesa_civil_atendimentos_{ano}.csv"
            with open(caminho_arquivo, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Arquivo salvo: {caminho_arquivo}")
            
            # Ler e retornar DataFrame
            df = pd.read_csv(caminho_arquivo, encoding='utf-8', on_bad_lines='skip')
            logger.info(f"Total de registros: {len(df)}")
            
            return df, str(caminho_arquivo)
            
        except requests.RequestException as e:
            msg = f"Erro ao baixar dados: {e}"
            logger.error(msg)
            return None, msg
        except Exception as e:
            msg = f"Erro ao processar dados: {e}"
            logger.error(msg)
            return None, msg
    
    def coletar_todos_anos(self, anos: List[int] = None) -> Dict[int, pd.DataFrame]:
        """
        Coleta dados de múltiplos anos.
        
        Args:
            anos: Lista de anos. Se None, coleta todos os disponíveis.
            
        Returns:
            Dicionário {ano: DataFrame}.
        """
        if anos is None:
            anos = ANOS_DISPONIVEIS
        
        resultados = {}
        
        for ano in anos:
            logger.info(f"\n=== Processando ano {ano} ===")
            df, _ = self.coletar_dados_anual(ano)
            if df is not None:
                resultados[ano] = df
        
        return resultados
    
    def verificar_disponibilidade(self, dataset_id: str = DATASET_ID) -> List[int]:
        """
        Verifica quais anos estão disponíveis no dataset.
        
        Args:
            dataset_id: ID do dataset.
            
        Returns:
            Lista de anos disponíveis.
        """
        info = self.buscar_info_dataset(dataset_id)
        anos_encontrados = []
        
        for recurso in info.get('resources', []):
            nome = recurso.get('name', '').lower()
            # Extrair ano do nome (ex: "Atendimentos 2024" -> 2024)
            if 'atendimentos' in nome:
                try:
                    ano = int([p for p in nome.split() if p.isdigit()][0])
                    anos_encontrados.append(ano)
                except (IndexError, ValueError):
                    continue
        
        logger.info(f"Anos disponíveis: {sorted(anos_encontrados)}")
        return sorted(anos_encontrados)


def main():
    """
    Função principal para execução standalone do script.
    """
    print("=" * 60)
    print("Coleta de Dados - Defesa Civil do Recife")
    print("=" * 60)
    
    # Inicializar coletor
    coletor = ColetorDadosRecife()
    
    # Verificar disponibilidade
    print("\n1. Verificando disponibilidade de dados...")
    anos_disponiveis = coletor.verificar_disponibilidade()
    print(f"   Anos disponíveis: {anos_disponiveis}")
    
    # Listar informações do dataset
    print("\n2. Buscando informações do dataset...")
    info = coletor.buscar_info_dataset()
    print(f"   Título: {info.get('title', 'N/A')}")
    print(f"   Descrição: {info.get('notes', 'N/A')[:100]}...")
    print(f"   Recursos: {len(info.get('resources', []))}")
    
    # Coletar dados dos últimos 3 anos como exemplo
    anos_exemplo = [2023, 2024, 2025]
    print(f"\n3. Coletando dados dos anos: {anos_exemplo}")
    
    for ano in anos_exemplo:
        if ano in anos_disponiveis:
            df, caminho = coletor.coletar_dados_anual(ano)
            if df is not None:
                print(f"   {ano}: {len(df)} registros salvos em {caminho}")
                # Mostrar schema
                print(f"        Colunas: {list(df.columns)[:5]}...")
    
    print("\n" + "=" * 60)
    print("Coleta concluída!")
    print("=" * 60)


if __name__ == "__main__":
    main()