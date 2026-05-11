#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script 04 - Processamento PySpark
==================================
Processa os dados da Defesa Civil do Recife usando PySpark.

Este script:
1. Lê os dados processados do Pandas (CSV unificado)
2. Cria DataFrame Spark
3. Faz transformações:
   - groupBy por bairro/ano
   - groupBy por tipo_ocorrencia/mes
   - window functions para médias móveis
   - joins para correlação
4. Salva resultados em Parquet ou CSV

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
# FUNÇÕES AUXILIARES
# ============================================================================

def verificar_pyspark():
    """Verifica se PySpark está instalado."""
    try:
        import pyspark
        return True
    except ImportError:
        return False


def processar_com_pyspark():
    """Processa dados usando PySpark."""
    from pyspark.sql import SparkSession
    from pyspark.sql import functions as F
    from pyspark.sql.window import Window
    from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType

    logger.info("=" * 70)
    logger.info("PROCESSAMENTO PYSPARK - DEFESA CIVIL DO RECIFE")
    logger.info("=" * 70)

    # Criar sessão Spark
    spark = SparkSession.builder \
        .appName("ChuvasRecife") \
        .master("local[*]") \
        .config("spark.driver.memory", "2g") \
        .getOrCreate()

    logger.info(f"Spark versão: {spark.version}")

    # Ler dados - usando inferência de schema
    arquivo_entrada = DIRETORIO_PROCESSADOS / "atendimentos_unificado.csv.gz"
    logger.info(f"Lendo dados de: {arquivo_entrada}")

    df = spark.read.csv(
        str(arquivo_entrada),
        header=True,
        sep=',',
        encoding='utf-8',
        inferSchema=True
    )

    logger.info(f"Total de registros: {df.count()}")
    logger.info(f"Schema: {df.schema.simpleString()}")

    # 1. GroupBy por bairro/ano
    logger.info("\n[1] Agregação por bairro e ano...")
    agg_bairro_ano = df.groupBy("Bairro", "ano17").count()
    agg_bairro_ano = agg_bairro_ano.withColumnRenamed("count", "total_ocorrencias")
    agg_bairro_ano = agg_bairro_ano.orderBy(F.desc("total_ocorrencias"))
    agg_bairro_ano.show(10, truncate=False)

    # 2. GroupBy por tipo_ocorrencia/mes
    logger.info("\n[2] Agregação por tipo de ocorrência e mês...")
    agg_tipo_mes = df.groupBy("Ocorrencia", "mes").count()
    agg_tipo_mes = agg_tipo_mes.withColumnRenamed("count", "total_ocorrencias")
    agg_tipo_mes = agg_tipo_mes.orderBy(F.desc("total_ocorrencias"))
    agg_tipo_mes.show(10, truncate=False)

    # 3. Window functions para médias móveis
    logger.info("\n[3] Médias móveis por ano...")
    window_spec = Window.orderBy("ano17").rowsBetween(-2, 0)

    agg_ano = df.groupBy("ano17").count().withColumnRenamed("count", "total")
    agg_ano = agg_ano.withColumn("media_movel_3anos", F.avg("total").over(window_spec))
    agg_ano = agg_ano.orderBy("ano17")
    agg_ano.show(truncate=False)

    # 4. Estatísticas por bairro
    logger.info("\n[4] Estatísticas por bairro...")
    stats_bairro = df.groupBy("Bairro").agg(
        F.count("*").alias("total_ocorrencias"),
        F.countDistinct("ano17").alias("anos_afetados"),
        F.max("ano17").alias("ultimo_ano"),
        F.min("ano17").alias("primeiro_ano")
    )
    stats_bairro = stats_bairro.orderBy(F.desc("total_ocorrencias"))
    stats_bairro.show(10, truncate=False)

    # 5. Correlação temporal
    logger.info("\n[5] Análise temporal...")
    agg_mes_ano = df.groupBy("mes", "ano17").count()
    agg_mes_ano = agg_mes_ano.withColumnRenamed("count", "total_ocorrencias")
    agg_mes_ano = agg_mes_ano.orderBy("ano17", "mes")
    agg_mes_ano.show(10, truncate=False)

    # Salvar resultados
    logger.info("\nSalvando resultados...")

    # Criar diretório de output
    DIRETORIO_OUTPUT.mkdir(parents=True, exist_ok=True)

    # Salvar em CSV (otimizado para Power BI)
    agg_bairro_ano.coalesce(1).write.mode("overwrite").csv(str(DIRETORIO_OUTPUT / "agg_bairro_ano.csv"), header=True, sep=";")
    agg_tipo_mes.coalesce(1).write.mode("overwrite").csv(str(DIRETORIO_OUTPUT / "agg_tipo_mes.csv"), header=True, sep=";")
    agg_ano.coalesce(1).write.mode("overwrite").csv(str(DIRETORIO_OUTPUT / "agg_ano.csv"), header=True, sep=";")
    stats_bairro.coalesce(1).write.mode("overwrite").csv(str(DIRETORIO_OUTPUT / "stats_bairro.csv"), header=True, sep=";")
    agg_mes_ano.coalesce(1).write.mode("overwrite").csv(str(DIRETORIO_OUTPUT / "agg_mes_ano.csv"), header=True, sep=";")

    logger.info("Resultados salvos em formato CSV!")

    # Encerrar sessão Spark
    spark.stop()

    logger.info("\n" + "=" * 70)
    logger.info("PROCESSAMENTO PYSPARK CONCLUÍDO")
    logger.info("=" * 70)


def processar_com_pandas():
    """Processa dados usando Pandas (fallback)."""
    import pandas as pd

    logger.info("=" * 70)
    logger.info("PROCESSAMENTO (FALLBACK PANDAS) - DEFESA CIVIL DO RECIFE")
    logger.info("=" * 70)

    # Ler dados
    arquivo_entrada = DIRETORIO_PROCESSADOS / "atendimentos_unificado.csv.gz"
    logger.info(f"Lendo dados de: {arquivo_entrada}")

    df = pd.read_csv(arquivo_entrada, compression='gzip', encoding='utf-8', low_memory=False)

    logger.info(f"Total de registros: {len(df)}")
    logger.info(f"Colunas disponíveis: {list(df.columns)}")

    # Criar diretório de output
    DIRETORIO_OUTPUT.mkdir(parents=True, exist_ok=True)

    # 1. Agregação por bairro e ano
    logger.info("\n[1] Agregação por bairro e ano...")
    if 'bairro_normalizado' in df.columns and 'ano' in df.columns:
        agg_bairro_ano = df.groupby(['bairro_normalizado', 'ano']).size().reset_index(name='total_ocorrencias')
        agg_bairro_ano = agg_bairro_ano.sort_values('total_ocorrencias', ascending=False)
        agg_bairro_ano.to_csv(DIRETORIO_OUTPUT / "agg_bairro_ano.csv", index=False, encoding='utf-8')
        logger.info(f"  Top 10 bairros por ano salvos!")
        print("\nTop 10 bairros por ano:")
        print(agg_bairro_ano.head(10).to_string(index=False))

    # 2. Agregação por tipo de ocorrência e mês
    logger.info("\n[2] Agregação por tipo de ocorrência e mês...")
    if 'tipo_ocorrencia_normalizado' in df.columns and 'mes' in df.columns:
        agg_tipo_mes = df.groupby(['tipo_ocorrencia_normalizado', 'mes']).size().reset_index(name='total_ocorrencias')
        agg_tipo_mes = agg_tipo_mes.sort_values('total_ocorrencias', ascending=False)
        agg_tipo_mes.to_csv(DIRETORIO_OUTPUT / "agg_tipo_mes.csv", index=False, encoding='utf-8')
        logger.info(f"  Tipos por mês salvos!")
        print("\nTop 10 tipos por mês:")
        print(agg_tipo_mes.head(10).to_string(index=False))

    # 3. Agregação por ano com média móvel
    logger.info("\n[3] Agregação por ano com média móvel...")
    if 'ano' in df.columns:
        agg_ano = df.groupby('ano').size().reset_index(name='total_ocorrencias')
        agg_ano = agg_ano.sort_values('ano')
        # Calcular média móvel de 3 anos
        agg_ano['media_movel_3anos'] = agg_ano['total_ocorrencias'].rolling(window=3, min_periods=1).mean()
        agg_ano.to_csv(DIRETORIO_OUTPUT / "agg_ano.csv", index=False, encoding='utf-8')
        logger.info(f"  Agregação por ano salva!")
        print("\nOcorrências por ano:")
        print(agg_ano.to_string(index=False))

    # 4. Estatísticas por bairro
    logger.info("\n[4] Estatísticas por bairro...")
    if 'bairro_normalizado' in df.columns and 'ano' in df.columns:
        stats_bairro = df.groupby('bairro_normalizado').agg(
            total_ocorrencias=('ano', 'count'),
            anos_afetados=('ano', 'nunique'),
            ultimo_ano=('ano', 'max'),
            primeiro_ano=('ano', 'min')
        ).reset_index()
        stats_bairro = stats_bairro.sort_values('total_ocorrencias', ascending=False)
        stats_bairro.to_csv(DIRETORIO_OUTPUT / "stats_bairro.csv", index=False, encoding='utf-8')
        logger.info(f"  Estatísticas por bairro salvas!")
        print("\nTop 10 bairros por estatísticas:")
        print(stats_bairro.head(10).to_string(index=False))

    # 5. Agregação por mês e ano
    logger.info("\n[5] Agregação por mês e ano...")
    if 'mes' in df.columns and 'ano' in df.columns:
        agg_mes_ano = df.groupby(['mes', 'ano']).size().reset_index(name='total_ocorrencias')
        agg_mes_ano = agg_mes_ano.sort_values(['ano', 'mes'])
        agg_mes_ano.to_csv(DIRETORIO_OUTPUT / "agg_mes_ano.csv", index=False, encoding='utf-8')
        logger.info(f"  Agregação mês/ano salva!")
        print("\nPrimeiros registros mês/ano:")
        print(agg_mes_ano.head(12).to_string(index=False))

    logger.info("\n" + "=" * 70)
    logger.info("PROCESSAMENTO CONCLUÍDO")
    logger.info("=" * 70)


# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================

def main():
    """
    Função principal do script de processamento.
    """
    print("\n" + "=" * 70)
    print("SCRIPT 04 - PROCESSAMENTO DE DADOS")
    print("Análise de dados da Defesa Civil do Recife")
    print("=" * 70 + "\n")

    # Verificar se PySpark está disponível
    if verificar_pyspark():
        print("PySpark disponível! Executando com Spark...\n")
        try:
            processar_com_pyspark()
        except Exception as e:
            print(f"Erro ao executar com PySpark: {e}")
            print("Usando fallback Pandas...\n")
            processar_com_pandas()
    else:
        print("PySpark não disponível. Executando com Pandas (fallback)...\n")
        processar_com_pandas()

    print("\n" + "=" * 70)
    print("PROCESSAMENTO CONCLUÍDO COM SUCESSO")
    print(f"Resultados salvos em: {DIRETORIO_OUTPUT}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()