#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Leitura e Análise - Dados de Chuvas em Recife
================================================
Lê os datasets coletados e executa análise inicial

Mostra:
- Schema (tipos de colunas)
- Sample de dados (primeiras linhas)
- Problemas identificados

Autor: Engenheiro de Dados
Data: 2026-05-11
"""

import pandas as pd
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import json

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Diretórios
DIRETORIO_SCRIPT = Path(__file__).parent
DIRETORIO_DADOS = DIRETORIO_SCRIPT.parent / "dados" / "brutos"
DIRETORIO_PROCESSADOS = DIRETORIO_SCRIPT.parent / "dados" / "processados"


class AnalisadorDadosChuvas:
    """
    Analisador de datasets de chuva e alagamentos do Recife.
    """
    
    def __init__(self, diretorio_dados: Path = None):
        """
        Inicializa o analisador.
        
        Args:
            diretorio_dados: Diretório com os dados brutos.
        """
        self.diretorio_dados = diretorio_dados or DIRETORIO_DADOS
        self.diretorio_processados = DIRETORIO_PROCESSADOS
        self.diretorio_processados.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Diretório de dados: {self.diretorio_dados}")
    
    def listar_arquivos(self) -> Dict[str, Path]:
        """
        Lista arquivos disponíveis no diretório de dados.
        
        Returns:
            Dicionário {nome: caminho}.
        """
        arquivos = {}
        
        if not self.diretorio_dados.exists():
            logger.warning(f"Diretório não encontrado: {self.diretorio_dados}")
            return arquivos
        
        for f in self.diretorio_dados.iterdir():
            if f.is_file():
                arquivos[f.name] = f
        
        logger.info(f"Encontrados {len(arquivos)} arquivos:")
        for nome in arquivos:
            tamanho = arquivos[nome].stat().st_size / 1024  # KB
            logger.info(f"  {nome} ({tamanho:.1f} KB)")
        
        return arquivos
    
    def analisar_csv(self, caminho: Path) -> Dict:
        """
        Analisa um arquivo CSV detalhando schema e sample.
        
        Args:
            caminho: Caminho do arquivo CSV.
            
        Returns:
            Dicionário com análise completa.
        """
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Analisando: {caminho.name}")
        logger.info(f"{'=' * 60}")
        
        analise = {
            'arquivo': str(caminho),
            'tamanho_bytes': caminho.stat().st_size,
            'schema': {},
            'problemas': [],
            'estatisticas': {},
            'amostra': None
        }
        
        try:
            # Tentar diferentes encodings
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            df = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(
                        caminho, 
                        encoding=encoding,
                        on_bad_lines='skip',
                        nrows=1000  # Ler apenas 1000 linhas para análise
                    )
                    analise['encoding_sucesso'] = encoding
                    logger.info(f"Encoding: {encoding}")
                    break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    logger.warning(f"Erro com {encoding}: {e}")
                    continue
            
            if df is None:
                analise['problemas'].append("Não foi possível ler o arquivo")
                return analise
            
            # Schema das colunas
            logger.info(f"\nTotal de registros (amostra): {len(df)}")
            logger.info(f"Colunas: {len(df.columns)}")
            
            colunas_schema = []
            for col in df.columns:
                dtype = str(df[col].dtype)
                nulos = df[col].isna().sum()
                pct_nulos = (nulos / len(df)) * 100
                valores_unicos = df[col].nunique()
                
                col_info = {
                    'nome': col,
                    'tipo': dtype,
                    'nulos': int(nulos),
                    'pct_nulos': round(pct_nulos, 2),
                    'valores_unicos': int(valores_unicos),
                    'exemplo': df[col].dropna().head(3).tolist()
                }
                colunas_schema.append(col_info)
                
                logger.info(f"  {col}: {dtype} | nulos: {pct_nulos:.1f}% | únicos: {valores_unicos}")
            
            analise['schema'] = colunas_schema
            
            # Amostra (primeiras 10 linhas)
            analise['amostra'] = df.head(10).to_dict('records')
            
            # Estatísticas básicas
            analise['estatisticas'] = {
                'total_registros': len(df),
                'total_colunas': len(df.columns),
                'memoria_mb': df.memory_usage(deep=True).sum() / 1024 / 1024
            }
            
            # Identificar problemas potenciais
            analise = self._identificar_problemas(df, analise)
            
            # Salvar sample em CSV
            caminho_sample = self.diretorio_processados / f"{caminho.stem}_sample.csv"
            df.head(100).to_csv(caminho_sample, index=False, encoding='utf-8')
            logger.info(f"Sample salvo: {caminho_sample}")
            
        except Exception as e:
            analise['problemas'].append(f"Erro inesperado: {e}")
            logger.error(f"Erro ao analisar: {e}")
        
        return analise
    
    def _identificar_problemas(self, df: pd.DataFrame, analise: Dict) -> Dict:
        """
        Identifica problemas potenciais nos dados.
        
        Args:
            df: DataFrame analisado.
            analise: Dicionário com análise sendo construída.
            
        Returns:
            Dicionário atualizado com problemas identificados.
        """
        problemas = []
        
        # 1. Verificar colunas com muitos nulos (>50%)
        for col_info in analise['schema']:
            if col_info['pct_nulos'] > 50:
                problemas.append(
                    f"Coluna '{col_info['nome']}' com {col_info['pct_nulos']}% nulos"
                )
        
        # 2. Verificar colunas de data
        colunas_data = [c for c in df.columns if 'data' in c.lower()]
        if not colunas_data:
            problemas.append("Nenhuma coluna de data identificada")
        
        # 3. Verificar encoding de texto
        for col in df.select_dtypes(include=['object']).columns:
            sample = df[col].dropna().head(10).astype(str)
            # Verificar caracteres estranhos
            if sample.str.contains('[^\x00-\x7F]', regex=True).any():
                problemas.append(f"Coluna '{col}' pode ter caracteres especiais")
        
        analise['problemas'] = problemas
        
        if problemas:
            logger.warning("Problemas identificados:")
            for p in problemas:
                logger.warning(f"  - {p}")
        
        return analise
    
    def analisar_defesa_civil(self, ano: int = 2024) -> Optional[Dict]:
        """
        Analisa dados específicos da Defesa Civil.
        
        Args:
            ano: Ano dos dados.
            
        Returns:
            Dicionário com análise.
        """
        arquivo = self.diretorio_dados / f"defesa_civil_atendimentos_{ano}.csv"
        
        if not arquivo.exists():
            # Buscar outros arquivos similares
            arquivos_defesa = list(self.diretorio_dados.glob("*defesa*.csv"))
            if arquivos_defesa:
                arquivo = arquivos_defesa[0]
                logger.info(f"Usando arquivo alternativo: {arquivo.name}")
            else:
                logger.warning(f"Arquivo não encontrado: {arquivo}")
                return None
        
        return self.analisar_csv(arquivo)
    
    def gerar_relatorio(self, analise: Dict) -> str:
        """
        Gera um relatório formatado em texto.
        
        Args:
            analise: Dicionário de análise.
            
        Returns:
            String com relatório formatado.
        """
        linhas = []
        linhas.append("=" * 60)
        linhas.append("RELATÓRIO DE ANÁLISE - DADOS DE CHUVAS DO RECIFE")
        linhas.append("=" * 60)
        linhas.append(f"\nArquivo: {analise.get('arquivo')}")
        linhas.append(f"Tamanho: {analise.get('tamanho_bytes', 0) / 1024:.1f} KB")
        
        estatisticas = analise.get('estatisticas', {})
        linhas.append(f"\n--- Estatísticas ---")
        linhas.append(f"Registros: {estatisticas.get('total_registros', 'N/A')}")
        linhas.append(f"Colunas: {estatisticas.get('total_colunas', 'N/A')}")
        linhas.append(f"Memória: {estatisticas.get('memoria_mb', 0):.2f} MB")
        
        # Schema
        schema = analise.get('schema', [])
        if schema:
            linhas.append(f"\n--- Schema ---")
            for col in schema[:20]:  # Primeiras 20 colunas
                linhas.append(
                    f"  {col['nome']}: {col['tipo']} "
                    f"(nulos: {col['pct_nulos']}%)"
                )
        
        # Problemas
        problemas = analise.get('problemas', [])
        if problemas:
            linhas.append(f"\n--- Problemas Identificados ---")
            for p in problemas:
                linhas.append(f"  ! {p}")
        
        # Amostra
        linhas.append(f"\n--- Amostra (10 linhas) ---")
        amostra = analise.get('amostra', [])
        if amostra:
            colunas = list(schema[0]['exemplo'].keys()) if schema else []
            linhas.append(f"Colunas: {colunas}")
        
        linhas.append("\n" + "=" * 60)
        
        return "\n".join(linhas)


def main():
    """
    Função principal.
    """
    print("=" * 60)
    print("Análise de Dados - Chuvas em Recife")
    print("=" * 60)
    
    # Inicializar analisador
    analiser = AnalisadorDadosChuvas()
    
    # Listar arquivos disponíveis
    print("\n1. Listando arquivos disponíveis...")
    arquivos = analiser.listar_arquivos()
    
    if not arquivos:
        print("\n   ATENÇÃO: Nenhum arquivo encontrado!")
        print("   Execute primeiro o script de coleta:")
        print("   python coleta_dados_recife.py")
        print("=" * 60)
        return
    
    # Analisar cada arquivo CSV
    print("\n2. Analisando arquivos CSV...")
    relatorios = []
    
    for nome, caminho in arquivos.items():
        if caminho.suffix.lower() == '.csv':
            analise = analiser.analisar_csv(caminho)
            relatorio = analiser.gerar_relatorio(analise)
            relatorios.append(relatorio)
            print(relatorio)
            
            # Salvar análise em JSON
            caminho_json = analiser.diretorio_processados / f"{caminho.stem}_analise.json"
            # Remover dados grandes da análise para JSON
            analise_json = analise.copy()
            if 'amostra' in analise_json:
                del analise_json['amostra']
            with open(caminho_json, 'w', encoding='utf-8') as f:
                json.dump(analise_json, f, indent=2, ensure_ascii=False)
            logger.info(f"Análise salva: {caminho_json}")
    
    print("\n" + "=" * 60)
    print("Análise concluída!")
    print("=" * 60)


if __name__ == "__main__":
    main()