#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script 01 - Diagnóstico de Dados
================================
Realiza diagnóstico completo dos CSVs da Defesa Civil do Recife.

Funcionalidades:
- Carrega todos os CSVs anuais disponíveis
- Exibe schema (colunas, tipos, nulos)
- Mostra estatísticas básicas
- Identifica problemas (encoding, datas, outliers)

Autor: Engenheiro de Dados
Data: 2026-05-11
"""

import pandas as pd
import os
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import json

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONSTANTES
# ============================================================================

DIRETORIO_SCRIPT = Path(__file__).parent
DIRETORIO_DADOS = DIRETORIO_SCRIPT.parent / "dados" / "brutos" / "defesa_civil"
DIRETORIO_PROCESSADOS = DIRETORIO_SCRIPT.parent / "dados" / "processados"

# Encodings a serem testados
ENCODINGS = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']


# ============================================================================
# CLASSE PRINCIPAL
# ============================================================================

class DiagnosticoDados:
    """
    Realiza diagnóstico completo dos dados da Defesa Civil do Recife.
    """

    def __init__(self, diretorio_dados: Path = None):
        """
        Inicializa o diagnóstico.

        Args:
            diretorio_dados: Caminho para o diretório de dados brutos.
        """
        self.diretorio_dados = diretorio_dados or DIRETORIO_DADOS
        self.diretorio_processados = DIRETORIO_PROCESSADOS

        # Criar diretório de processados se não existir
        self.diretorio_processados.mkdir(parents=True, exist_ok=True)

        logger.info(f"Diretório de dados brutos: {self.diretorio_dados}")
        logger.info(f"Diretório de processados: {self.diretorio_processados}")

    def listar_arquivos_csv(self) -> List[Path]:
        """
        Lista todos os arquivos CSV no diretório de dados.

        Returns:
            Lista de caminhos dos arquivos CSV encontrados.
        """
        arquivos = []

        if not self.diretorio_dados.exists():
            logger.warning(f"Diretório não encontrado: {self.diretorio_dados}")
            return arquivos

        # Buscar arquivos CSV
        for f in self.diretorio_dados.iterdir():
            if f.is_file() and f.suffix.lower() == '.csv':
                arquivos.append(f)

        logger.info(f"Encontrados {len(arquivos)} arquivos CSV:")
        for arq in arquivos:
            tamanho_kb = arq.stat().st_size / 1024
            logger.info(f"  - {arq.name} ({tamanho_kb:.1f} KB)")

        return arquivos

    def detectar_encoding(self, caminho: Path) -> Tuple[str, pd.DataFrame]:
        """
        Detecta o encoding correto do arquivo CSV.

        Args:
            caminho: Caminho do arquivo CSV.

        Returns:
            Tupla (encoding utilizado, DataFrame carregado).
        """
        for encoding in ENCODINGS:
            try:
                df = pd.read_csv(
                    caminho,
                    encoding=encoding,
                    sep=';',  # Delimitador ponto e vírgula
                    on_bad_lines='skip',
                    low_memory=False
                )
                logger.info(f"  Encoding detectado: {encoding}")
                return encoding, df
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.warning(f"  Erro com {encoding}: {e}")
                continue

        logger.error(f"  Não foi possível detectar encoding para {caminho.name}")
        return None, None

    def analisar_schema(self, df: pd.DataFrame) -> Dict:
        """
        Analisa o schema do DataFrame.

        Args:
            df: DataFrame a ser analisado.

        Returns:
            Dicionário com informações do schema.
        """
        schema_info = {
            'total_colunas': len(df.columns),
            'total_registros': len(df),
            'colunas': []
        }

        logger.info(f"\n  Schema do DataFrame:")
        logger.info(f"  Total de colunas: {len(df.columns)}")
        logger.info(f"  Total de registros: {len(df)}")

        for col in df.columns:
            dtype = str(df[col].dtype)
            nulos = df[col].isna().sum()
            pct_nulos = (nulos / len(df)) * 100 if len(df) > 0 else 0
            valores_unicos = df[col].nunique()

            col_info = {
                'nome': col,
                'tipo': dtype,
                'nulos': int(nulos),
                'pct_nulos': round(pct_nulos, 2),
                'valores_unicos': int(valores_unicos)
            }
            schema_info['colunas'].append(col_info)

            # Log apenas colunas com problemas ou importantes
            if pct_nulos > 0 or 'data' in col.lower() or 'bairro' in col.lower():
                logger.info(f"    {col}: {dtype} | nulos: {pct_nulos:.1f}% | únicos: {valores_unicos}")

        return schema_info

    def identificar_problemas(self, df: pd.DataFrame, encoding: str) -> List[str]:
        """
        Identifica problemas potenciais nos dados.

        Args:
            df: DataFrame a ser analisado.
            encoding: Encoding utilizado.

        Returns:
            Lista de problemas identificados.
        """
        problemas = []

        # 1. Verificar colunas com muitos nulos (>50%)
        for col in df.columns:
            pct_nulos = (df[col].isna().sum() / len(df)) * 100 if len(df) > 0 else 0
            if pct_nulos > 50:
                problemas.append(f"Coluna '{col}' com {pct_nulos:.1f}% de nulos")

        # 2. Verificar colunas de data
        colunas_data = [c for c in df.columns if 'data' in c.lower()]
        if not colunas_data:
            problemas.append("Nenhuma coluna de data identificada")
        else:
            logger.info(f"  Colunas de data identificadas: {colunas_data}")

        # 3. Verificar encoding de texto
        for col in df.select_dtypes(include=['object']).columns:
            sample = df[col].dropna().head(10).astype(str)
            if sample.str.contains(r'[^\x00-\x7F]', regex=True).any():
                problemas.append(f"Coluna '{col}' pode ter caracteres especiais (encoding: {encoding})")

        # 4. Verificar valores duplicados em campos importantes
        campos_importantes = ['bairro', 'tipo_ocorrencia', 'regional']
        for campo in campos_importantes:
            if campo in df.columns:
                nulos = df[campo].isna().sum()
                if nulos > 0:
                    problemas.append(f"Campo '{campo}' tem {nulos} valores nulos")

        # 5. Verificar outliers em campos numéricos
        for col in df.select_dtypes(include=['number']).columns:
            if len(df[col]) > 0:
                q1 = df[col].quantile(0.25)
                q3 = df[col].quantile(0.75)
                iqr = q3 - q1
                outliers = df[(df[col] < q1 - 1.5 * iqr) | (df[col] > q3 + 1.5 * iqr)]
                if len(outliers) > 0:
                    pct_outliers = (len(outliers) / len(df)) * 100
                    if pct_outliers > 5:
                        problemas.append(f"Coluna '{col}' tem {pct_outliers:.1f}% de outliers")

        return problemas

    def analisar_estatisticas(self, df: pd.DataFrame) -> Dict:
        """
        Gera estatísticas básicas do DataFrame.

        Args:
            df: DataFrame a ser analisado.

        Returns:
            Dicionário com estatísticas.
        """
        estatisticas = {
            'total_registros': len(df),
            'memoria_mb': round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
            'colunas_numericas': [],
            'colunas_texto': [],
            'colunas_data': []
        }

        # Classificar colunas por tipo
        for col in df.columns:
            if 'data' in col.lower():
                estatisticas['colunas_data'].append(col)
            elif pd.api.types.is_numeric_dtype(df[col]):
                estatisticas['colunas_numericas'].append(col)
            else:
                estatisticas['colunas_texto'].append(col)

        logger.info(f"\n  Estatísticas:")
        logger.info(f"    Registros: {estatisticas['total_registros']}")
        logger.info(f"    Memória: {estatisticas['memoria_mb']} MB")
        logger.info(f"    Colunas numéricas: {len(estatisticas['colunas_numericas'])}")
        logger.info(f"    Colunas texto: {len(estatisticas['colunas_texto'])}")
        logger.info(f"    Colunas data: {len(estatisticas['colunas_data'])}")

        return estatisticas

    def analisar_campos_categoricos(self, df: pd.DataFrame) -> Dict:
        """
        Analisa campos categóricos importantes.

        Args:
            df: DataFrame a ser analisado.

        Returns:
            Dicionário com análise de campos categóricos.
        """
        campos_analisar = ['tipo_ocorrencia', 'bairro', 'regional', 'natureza_servico', 'acao', 'status']

        analise = {}

        for campo in campos_analisar:
            if campo in df.columns:
                contagem = df[campo].value_counts().head(10)
                analise[campo] = {
                    'total_unicos': df[campo].nunique(),
                    'top_10': contagem.to_dict()
                }
                logger.info(f"\n  {campo} (únicos: {df[campo].nunique()}):")
                for valor, qtd in contagem.items():
                    logger.info(f"    {valor}: {qtd}")

        return analise

    def executar_diagnostico(self) -> Dict:
        """
        Executa o diagnóstico completo de todos os arquivos.

        Returns:
            Dicionário com resultado do diagnóstico.
        """
        resultado = {
            'data_execucao': datetime.now().isoformat(),
            'arquivos': [],
            'resumo': {}
        }

        logger.info("=" * 70)
        logger.info("DIAGNÓSTICO DE DADOS - DEFESA CIVIL DO RECIFE")
        logger.info("=" * 70)

        # Listar arquivos
        arquivos = self.listar_arquivos_csv()

        if not arquivos:
            logger.warning("Nenhum arquivo CSV encontrado!")
            logger.info("Execute primeiro o script de coleta de dados.")
            resultado['erro'] = "Nenhum arquivo CSV encontrado"
            return resultado

        total_registros = 0

        # Analisar cada arquivo
        for caminho in arquivos:
            logger.info(f"\n{'=' * 70}")
            logger.info(f"Analisando: {caminho.name}")
            logger.info(f"{'=' * 70}")

            # Detectar encoding e carregar
            encoding, df = self.detectar_encoding(caminho)

            if df is None:
                logger.error(f"Não foi possível carregar {caminho.name}")
                continue

            # Análise do arquivo
            arquivo_info = {
                'nome': caminho.name,
                'encoding': encoding,
                'registros': len(df),
                'schema': self.analisar_schema(df),
                'estatisticas': self.analisar_estatisticas(df),
                'problemas': self.identificar_problemas(df, encoding),
                'categoricos': self.analisar_campos_categoricos(df)
            }

            resultado['arquivos'].append(arquivo_info)
            total_registros += len(df)

            # Exibir problemas encontrados
            if arquivo_info['problemas']:
                logger.warning("\n  Problemas identificados:")
                for prob in arquivo_info['problemas']:
                    logger.warning(f"    ! {prob}")

        # Resumo
        resultado['resumo'] = {
            'total_arquivos': len(arquivos),
            'total_registros': total_registros,
            'arquivos_processados': len(resultado['arquivos'])
        }

        logger.info(f"\n{'=' * 70}")
        logger.info("RESUMO DO DIAGNÓSTICO")
        logger.info(f"{'=' * 70}")
        logger.info(f"  Arquivos processados: {resultado['resumo']['arquivos_processados']}")
        logger.info(f"  Total de registros: {resultado['resumo']['total_registros']}")

        # Salvar resultado em JSON
        caminho_saida = self.diretorio_processados / "diagnostico.json"
        with open(caminho_saida, 'w', encoding='utf-8') as f:
            json.dump(resultado, f, indent=2, ensure_ascii=False)
        logger.info(f"\nDiagnóstico salvo em: {caminho_saida}")

        return resultado


# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================

def main():
    """
    Função principal do script de diagnóstico.
    """
    print("\n" + "=" * 70)
    print("SCRIPT 01 - DIAGNÓSTICO DE DADOS")
    print("Análise de CSVs da Defesa Civil do Recife")
    print("=" * 70 + "\n")

    # Executar diagnóstico
    diagnostico = DiagnosticoDados()
    resultado = diagnostico.executar_diagnostico()

    print("\n" + "=" * 70)
    print("DIAGNÓSTICO CONCLUÍDO")
    print("=" * 70)

    if 'erro' in resultado:
        print(f"\nATENÇÃO: {resultado['erro']}")
        print("Execute o script de coleta de dados primeiro.")
    else:
        print(f"\nArquivos processados: {resultado['resumo']['arquivos_processados']}")
        print(f"Total de registros: {resultado['resumo']['total_registros']}")
        print(f"\nResultado salvo em: dados/processados/diagnostico.json")

    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()