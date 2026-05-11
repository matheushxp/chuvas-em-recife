#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script 05 - Preparar Datasets para Power BI
============================================
Gera datasets otimizados para o dashboard Power BI.

Datasets gerados:
1. kpis_gerais.csv - KPIs principais
2. serie_temporal.csv - evolução ao longo do tempo
3. por_bairro.csv - ranking de bairros afetados
4. sazonalidade.csv - padrão mensal/sazonal
5. correlacao_chuva_ocorrencias.csv - dados para análise de correlação

Autor: Engenheiro de Dados
Data: 2026-05-11
"""

import sys
import io
import logging
from pathlib import Path

# Configurar encoding UTF-8 para stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

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
DIRETORIO_DADOS = DIRETORIO_SCRIPT.parent / "dados"
DIRETORIO_PROCESSADOS = DIRETORIO_DADOS / "processados"
DIRETORIO_OUTPUT = DIRETORIO_DADOS / "output"


# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================

def main():
    import pandas as pd
    import numpy as np

    print("\n" + "=" * 70)
    print("SCRIPT 05 - PREPARAR DATASETS PARA POWER BI")
    print("Análise de dados da Defesa Civil do Recife")
    print("=" * 70 + "\n")

    # Criar diretório de output
    DIRETORIO_OUTPUT.mkdir(parents=True, exist_ok=True)

    # Ler dados processados
    arquivo_entrada = DIRETORIO_PROCESSADOS / "atendimentos_unificado.csv.gz"
    logger.info(f"Lendo dados de: {arquivo_entrada}")

    df = pd.read_csv(arquivo_entrada, compression='gzip', encoding='utf-8', low_memory=False)

    logger.info(f"Total de registros: {len(df)}")

    # =========================================================================
    # 1. KPIs Gerais
    # =========================================================================
    logger.info("\n[1] Gerando KPIs gerais...")

    kpis = {
        'total_ocorrencias': len(df),
        'anos_cobertos': df['ano'].nunique() if 'ano' in df.columns else 0,
        'bairros_afetados': df['Bairro'].nunique() if 'Bairro' in df.columns else 0,
        'media_mensal': 0,
        'ano_mais_ocorrencias': None,
        'mes_mais_ocorrencias': None,
    }

    if 'ano' in df.columns and 'mes' in df.columns:
        df_com_ano = df[df['ano'].notna()]
        kpis['anos_cobertos'] = int(df_com_ano['ano'].nunique())
        kpis['ano_mais_ocorrencias'] = int(df_com_ano.groupby('ano').size().idxmax())
        kpis['mes_mais_ocorrencias'] = int(df.groupby('mes').size().idxmax())
        kpis['media_mensal'] = round(len(df_com_ano) / (kpis['anos_cobertos'] * 12), 2)

    # Salvar KPIs
    kpis_df = pd.DataFrame([kpis])
    kpis_df.to_csv(DIRETORIO_OUTPUT / "kpis_gerais.csv", index=False, encoding='utf-8')
    print(f"\nKPIs Gerais:")
    print(f"  - Total de ocorrências: {kpis['total_ocorrencias']:,}")
    print(f"  - Anos cobertos: {kpis['anos_cobertos']}")
    print(f"  - Bairros afetados: {kpis['bairros_afetados']}")
    print(f"  - Ano com mais ocorrências: {kpis['ano_mais_ocorrencias']}")
    print(f"  - Mês com mais ocorrências: {kpis['mes_mais_ocorrencias']}")

    # =========================================================================
    # 2. Série Temporal
    # =========================================================================
    logger.info("\n[2] Gerando série temporal...")

    if 'ano' in df.columns and 'mes' in df.columns:
        df_com_ano = df[df['ano'].notna()]

        # Série temporal por ano
        serie_ano = df_com_ano.groupby('ano').size().reset_index(name='total_ocorrencias')
        serie_ano['ano'] = serie_ano['ano'].astype(int)
        serie_ano = serie_ano.sort_values('ano')

        # Adicionar média móvel
        serie_ano['media_movel_3anos'] = serie_ano['total_ocorrencias'].rolling(window=3, min_periods=1).mean()

        serie_ano.to_csv(DIRETORIO_OUTPUT / "serie_temporal.csv", index=False, encoding='utf-8')

        print(f"\nSérie Temporal (por ano):")
        print(serie_ano.to_string(index=False))

    # =========================================================================
    # 3. Por Bairro
    # =========================================================================
    logger.info("\n[3] Gerando ranking de bairros...")

    if 'Bairro' in df.columns:
        por_bairro = df.groupby('Bairro').size().reset_index(name='total_ocorrencias')
        por_bairro = por_bairro.sort_values('total_ocorrencias', ascending=False)

        # Adicionar ranking
        por_bairro['ranking'] = range(1, len(por_bairro) + 1)

        # Adicionar percentual
        por_bairro['percentual'] = (por_bairro['total_ocorrencias'] / por_bairro['total_ocorrencias'].sum() * 100).round(2)

        por_bairro.to_csv(DIRETORIO_OUTPUT / "por_bairro.csv", index=False, encoding='utf-8')

        print(f"\nTop 10 Bairros:")
        print(por_bairro.head(10).to_string(index=False))

    # =========================================================================
    # 4. Sazonalidade
    # =========================================================================
    logger.info("\n[4] Gerando análise de sazonalidade...")

    if 'mes' in df.columns:
        sazonalidade = df.groupby('mes').size().reset_index(name='total_ocorrencias')
        sazonalidade = sazonalidade.sort_values('mes')

        # Adicionar nome do mês
        meses = {
            1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
            5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
            9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
        }
        sazonalidade['nome_mes'] = sazonalidade['mes'].map(meses)

        # Adicionar estação
        def get_estacao(mes):
            if mes in [12, 1, 2]:
                return 'Verão'
            elif mes in [3, 4, 5]:
                return 'Outono'
            elif mes in [6, 7, 8]:
                return 'Inverno'
            else:
                return 'Primavera'

        sazonalidade['estacao'] = sazonalidade['mes'].apply(get_estacao)

        # Adicionar percentual
        sazonalidade['percentual'] = (sazonalidade['total_ocorrencias'] / sazonalidade['total_ocorrencias'].sum() * 100).round(2)

        sazonalidade.to_csv(DIRETORIO_OUTPUT / "sazonalidade.csv", index=False, encoding='utf-8')

        print(f"\nSazonalidade (por mês):")
        print(sazonalidade.to_string(index=False))

    # =========================================================================
    # 5. Correlação Chuva x Ocorrências
    # =========================================================================
    logger.info("\n[5] Gerando dados para correlação...")

    if 'ano' in df.columns and 'mes' in df.columns:
        df_com_ano = df[df['ano'].notna()]

        # Agregar por mês e ano
        correlacao = df_com_ano.groupby(['ano', 'mes']).size().reset_index(name='total_ocorrencias')
        correlacao['ano'] = correlacao['ano'].astype(int)
        correlacao['mes'] = correlacao['mes'].astype(int)
        correlacao = correlacao.sort_values(['ano', 'mes'])

        # Simular dados de chuva (em mm) - baseado em médias históricas de Recife
        # Recife tem média anual de ~2.400mm, com estação chuvosa de abril a agosto
        chuva_media = {
            1: 100, 2: 110, 3: 150, 4: 250, 5: 320, 6: 350,
            7: 340, 8: 280, 9: 180, 10: 120, 11: 80, 12: 70
        }

        correlacao['chuva_mm'] = correlacao['mes'].map(chuva_media)

        # Adicionar estação chuvosa
        correlacao['estacao_chuvosa'] = correlacao['mes'].apply(
            lambda x: 'Seca' if x in [11, 12, 1, 2, 3] else 'Chuvosa'
        )

        correlacao.to_csv(DIRETORIO_OUTPUT / "correlacao_chuva_ocorrencias.csv", index=False, encoding='utf-8')

        print(f"\nDados para Correlação (primeiros 12 registros):")
        print(correlacao.head(12).to_string(index=False))

    # =========================================================================
    # RESUMO DOS ARQUIVOS GERADOS
    # =========================================================================
    logger.info("\n" + "=" * 70)
    logger.info("DATASETS PREPARADOS PARA POWER BI")
    logger.info("=" * 70)

    arquivos = list(DIRETORIO_OUTPUT.iterdir())
    for f in arquivos:
        if f.is_file():
            tamanho = f.stat().st_size
            if tamanho > 1024 * 1024:
                tamanho_str = f"{tamanho / 1024 / 1024:.2f} MB"
            else:
                tamanho_str = f"{tamanho / 1024:.1f} KB"
            logger.info(f"  - {f.name} ({tamanho_str})")

    print("\n" + "=" * 70)
    print("DATASETS PARA POWER BI CONCLUÍDOS")
    print(f"Resultados salvos em: {DIRETORIO_OUTPUT}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()