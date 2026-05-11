#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script 03 - Agregação de Dados
===============================
Executa agregações para responder às perguntas de análise.

Agregações geradas:
- Total de ocorrências por ano
- Total por bairro
- Total por tipo_ocorrencia
- Ocorrências por mês (sazonalidade)
- Correlação com dados de chuva (quando disponíveis)

Autor: Engenheiro de Dados
Data: 2026-05-11
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

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


# ============================================================================
# CLASSE PRINCIPAL
# ============================================================================

class AgregacaoDados:
    """
    Executa agregações nos dados da Defesa Civil do Recife.
    """

    def __init__(self, arquivo_dados: Path = None):
        """
        Inicializa o processo de agregação.

        Args:
            arquivo_dados: Caminho para o arquivo de dados processados.
        """
        self.diretorio_processados = DIRETORIO_PROCESSADOS

        # Criar diretório de processados se não existir
        self.diretorio_processados.mkdir(parents=True, exist_ok=True)

        # Determinar arquivo de entrada
        if arquivo_dados:
            self.arquivo_entrada = arquivo_dados
        else:
            # Buscar arquivo unificado
            self.arquivo_entrada = self.diretorio_processados / "atendimentos_unificado.csv"
            if not self.arquivo_entrada.exists():
                # Buscar arquivo compactado
                self.arquivo_entrada = self.diretorio_processados / "atendimentos_unificado.csv.gz"

        logger.info(f"Arquivo de entrada: {self.arquivo_entrada}")

    def carregar_dados(self) -> pd.DataFrame:
        """
        Carrega os dados processados.

        Returns:
            DataFrame com os dados.
        """
        if not self.arquivo_entrada.exists():
            logger.error(f"Arquivo não encontrado: {self.arquivo_entrada}")
            logger.info("Execute primeiro o script de limpeza (02_limpeza.py)")
            return pd.DataFrame()

        logger.info(f"Carregando dados de: {self.arquivo_entrada}")

        # Detectar se é arquivo compactado
        if self.arquivo_entrada.suffix == '.gz':
            df = pd.read_csv(self.arquivo_entrada, compression='gzip', encoding='utf-8')
        else:
            df = pd.read_csv(self.arquivo_entrada, encoding='utf-8')

        logger.info(f"  Registros carregados: {len(df)}")
        logger.info(f"  Colunas: {len(df.columns)}")

        return df

    def agregar_por_ano(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Agrega total de ocorrências por ano.

        Args:
            df: DataFrame com os dados.

        Returns:
            DataFrame com agregação por ano.
        """
        logger.info("\n[1/5] Agregando por ano...")

        if 'ano' not in df.columns:
            logger.warning("  Coluna 'ano' não encontrada!")
            return pd.DataFrame()

        # Agregação por ano
        agg_ano = df.groupby('ano').size().reset_index(name='total_ocorrencias')
        agg_ano = agg_ano.sort_values('ano')

        logger.info(f"  Anos processados: {len(agg_ano)}")
        logger.info(f"  Total de registros: {agg_ano['total_ocorrencias'].sum()}")

        # Mostrar resultado
        for _, row in agg_ano.iterrows():
            logger.info(f"    {int(row['ano'])}: {row['total_ocorrencias']}")

        return agg_ano

    def agregar_por_bairro(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Agrega total de ocorrências por bairro.

        Args:
            df: DataFrame com os dados.

        Returns:
            DataFrame com agregação por bairro.
        """
        logger.info("\n[2/5] Agregando por bairro...")

        # Usar coluna normalizada se disponível
        coluna_bairro = 'bairro_normalizado' if 'bairro_normalizado' in df.columns else 'bairro'

        if coluna_bairro not in df.columns:
            logger.warning(f"  Coluna '{coluna_bairro}' não encontrada!")
            return pd.DataFrame()

        # Agregação por bairro
        agg_bairro = df.groupby(coluna_bairro).size().reset_index(name='total_ocorrencias')
        agg_bairro = agg_bairro.sort_values('total_ocorrencias', ascending=False)

        logger.info(f"  Bairros processados: {len(agg_bairro)}")

        # Mostrar top 10
        logger.info(f"  Top 10 bairros:")
        for i, row in agg_bairro.head(10).iterrows():
            logger.info(f"    {row[coluna_bairro]}: {row['total_ocorrencias']}")

        return agg_bairro

    def agregar_por_tipo(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Agrega total de ocorrências por tipo.

        Args:
            df: DataFrame com os dados.

        Returns:
            DataFrame com agregação por tipo de ocorrência.
        """
        logger.info("\n[3/5] Agregando por tipo de ocorrência...")

        # Usar coluna normalizada se disponível
        coluna_tipo = 'tipo_ocorrencia_normalizado' if 'tipo_ocorrencia_normalizado' in df.columns else 'tipo_ocorrencia'

        if coluna_tipo not in df.columns:
            logger.warning(f"  Coluna '{coluna_tipo}' não encontrada!")
            return pd.DataFrame()

        # Agregação por tipo
        agg_tipo = df.groupby(coluna_tipo).size().reset_index(name='total_ocorrencias')
        agg_tipo = agg_tipo.sort_values('total_ocorrencias', ascending=False)

        logger.info(f"  Tipos processados: {len(agg_tipo)}")

        # Mostrar todos os tipos
        logger.info(f"  Distribuição de tipos:")
        for _, row in agg_tipo.iterrows():
            logger.info(f"    {row[coluna_tipo]}: {row['total_ocorrencias']}")

        return agg_tipo

    def agregar_por_mes(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Agrega ocorrências por mês (sazonalidade).

        Args:
            df: DataFrame com os dados.

        Returns:
            DataFrame com agregação por mês.
        """
        logger.info("\n[4/5] Agregando por mês (sazonalidade)...")

        if 'mes' not in df.columns:
            logger.warning("  Coluna 'mes' não encontrada!")
            return pd.DataFrame()

        # Agregação por mês
        agg_mes = df.groupby('mes').size().reset_index(name='total_ocorrencias')
        agg_mes = agg_mes.sort_values('mes')

        # Adicionar nome do mês
        meses = {
            1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
            5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
            9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
        }
        agg_mes['nome_mes'] = agg_mes['mes'].map(meses)

        logger.info(f"  Meses processados: {len(agg_mes)}")

        # Mostrar resultado
        logger.info(f"  Ocorrências por mês:")
        for _, row in agg_mes.iterrows():
            logger.info(f"    {row['nome_mes']}: {row['total_ocorrencias']}")

        return agg_mes

    def agregar_por_estacao(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Agrega ocorrências por estação do ano.

        Args:
            df: DataFrame com os dados.

        Returns:
            DataFrame com agregação por estação.
        """
        logger.info("\n[5/5] Agregando por estação do ano...")

        if 'estacao' not in df.columns:
            logger.warning("  Coluna 'estacao' não encontrada!")
            return pd.DataFrame()

        # Agregação por estação
        agg_estacao = df.groupby('estacao').size().reset_index(name='total_ocorrencias')

        # Ordenar por estação
        ordem_estacoes = ['verao', 'outono', 'inverno', 'primavera']
        agg_estacao['ordem'] = agg_estacao['estacao'].map({e: i for i, e in enumerate(ordem_estacoes)})
        agg_estacao = agg_estacao.sort_values('ordem').drop('ordem', axis=1)

        logger.info(f"  Estações processadas: {len(agg_estacao)}")

        # Mostrar resultado
        logger.info(f"  Ocorrências por estação:")
        for _, row in agg_estacao.iterrows():
            logger.info(f"    {row['estacao']}: {row['total_ocorrencias']}")

        return agg_estacao

    def agregar_por_dia_semana(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Agrega ocorrências por dia da semana.

        Args:
            df: DataFrame com os dados.

        Returns:
            DataFrame com agregação por dia da semana.
        """
        logger.info("\n[Extra] Agregando por dia da semana...")

        if 'dia_semana_nome' not in df.columns:
            logger.warning("  Coluna 'dia_semana_nome' não encontrada!")
            return pd.DataFrame()

        # Agregação por dia da semana
        agg_dia = df.groupby('dia_semana_nome').size().reset_index(name='total_ocorrencias')

        # Ordenar por dia da semana
        ordem_dias = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        nomes_dias = {
            'Monday': 'Segunda-feira',
            'Tuesday': 'Terça-feira',
            'Wednesday': 'Quarta-feira',
            'Thursday': 'Quinta-feira',
            'Friday': 'Sexta-feira',
            'Saturday': 'Sábado',
            'Sunday': 'Domingo'
        }
        agg_dia['ordem'] = agg_dia['dia_semana_nome'].map({d: i for i, d in enumerate(ordem_dias)})
        agg_dia = agg_dia.sort_values('ordem').drop('ordem', axis=1)
        agg_dia['dia_semana'] = agg_dia['dia_semana_nome'].map(nomes_dias)

        logger.info(f"  Dias processados: {len(agg_dia)}")

        # Mostrar resultado
        logger.info(f"  Ocorrências por dia da semana:")
        for _, row in agg_dia.iterrows():
            logger.info(f"    {row['dia_semana']}: {row['total_ocorrencias']}")

        return agg_dia

    def agregar_por_hora(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Agrega ocorrências por hora do dia.

        Args:
            df: DataFrame com os dados.

        Returns:
            DataFrame com agregação por hora.
        """
        logger.info("\n[Extra] Agregando por hora do dia...")

        if 'hora' not in df.columns:
            logger.warning("  Coluna 'hora' não encontrada!")
            return pd.DataFrame()

        # Agregação por hora
        agg_hora = df.groupby('hora').size().reset_index(name='total_ocorrencias')
        agg_hora = agg_hora.sort_values('hora')

        logger.info(f"  Horas processadas: {len(agg_hora)}")

        # Mostrar resultado
        logger.info(f"  Ocorrências por hora:")
        for _, row in agg_hora.iterrows():
            logger.info(f"    {int(row['hora'])}h: {row['total_ocorrencias']}")

        return agg_hora

    def agregar_por_bairro_ano(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Agrega ocorrências por bairro e ano.

        Args:
            df: DataFrame com os dados.

        Returns:
            DataFrame com agregação por bairro e ano.
        """
        logger.info("\n[Extra] Agregando por bairro e ano...")

        coluna_bairro = 'bairro_normalizado' if 'bairro_normalizado' in df.columns else 'bairro'

        if coluna_bairro not in df.columns or 'ano' not in df.columns:
            logger.warning("  Colunas necessárias não encontradas!")
            return pd.DataFrame()

        # Agregação por bairro e ano
        agg = df.groupby([coluna_bairro, 'ano']).size().reset_index(name='total_ocorrencias')
        agg = agg.sort_values([coluna_bairro, 'ano'])

        logger.info(f"  Combinações bairro/ano: {len(agg)}")

        return agg

    def agregar_por_tipo_ano(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Agrega ocorrências por tipo e ano.

        Args:
            df: DataFrame com os dados.

        Returns:
            DataFrame com agregação por tipo e ano.
        """
        logger.info("\n[Extra] Agregando por tipo e ano...")

        coluna_tipo = 'tipo_ocorrencia_normalizado' if 'tipo_ocorrencia_normalizado' in df.columns else 'tipo_ocorrencia'

        if coluna_tipo not in df.columns or 'ano' not in df.columns:
            logger.warning("  Colunas necessárias não encontradas!")
            return pd.DataFrame()

        # Agregação por tipo e ano
        agg = df.groupby([coluna_tipo, 'ano']).size().reset_index(name='total_ocorrencias')
        agg = agg.sort_values([coluna_tipo, 'ano'])

        logger.info(f"  Combinações tipo/ano: {len(agg)}")

        return agg

    def calcular_estatisticas(self, df: pd.DataFrame) -> Dict:
        """
        Calcula estatísticas gerais dos dados.

        Args:
            df: DataFrame com os dados.

        Returns:
            Dicionário com estatísticas.
        """
        logger.info("\nCalculando estatísticas gerais...")

        estatisticas = {
            'total_registros': len(df),
            'periodo': {},
            'bairros': {},
            'tipos': {},
            'sazonalidade': {}
        }

        # Período
        if 'ano' in df.columns:
            estatisticas['periodo']['ano_inicio'] = int(df['ano'].min())
            estatisticas['periodo']['ano_fim'] = int(df['ano'].max())
            estatisticas['periodo']['anos_disponiveis'] = sorted(df['ano'].dropna().unique().astype(int).tolist())

        # Top bairros
        if 'bairro_normalizado' in df.columns:
            top_bairros = df['bairro_normalizado'].value_counts().head(5)
            estatisticas['bairros']['top_5'] = top_bairros.to_dict()

        # Top tipos
        if 'tipo_ocorrencia_normalizado' in df.columns:
            top_tipos = df['tipo_ocorrencia_normalizado'].value_counts().head(5)
            estatisticas['tipos']['top_5'] = top_tipos.to_dict()

        # Sazonalidade
        if 'mes' in df.columns:
            mes_mais = int(df['mes'].mode().values[0])
            meses = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
                     5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
                     9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}
            estatisticas['sazonalidade']['mes_mais_ocorrencias'] = meses.get(mes_mais, 'N/A')

        if 'estacao' in df.columns:
            estacao_mais = df['estacao'].mode().values[0]
            estatisticas['sazonalidade']['estacao_mais_ocorrencias'] = estacao_mais

        logger.info(f"  Estatísticas calculadas:")
        logger.info(f"    Total de registros: {estatisticas['total_registros']}")
        if 'ano_inicio' in estatisticas['periodo']:
            logger.info(f"    Período: {estatisticas['periodo']['ano_inicio']} - {estatisticas['periodo']['ano_fim']}")

        return estatisticas

    def executar_agregacao(self) -> Dict:
        """
        Executa todas as agregações.

        Returns:
            Dicionário com todas as agregações.
        """
        logger.info("=" * 70)
        logger.info("AGREGAÇÃO DE DADOS - DEFESA CIVIL DO RECIFE")
        logger.info("=" * 70)

        # Carregar dados
        df = self.carregar_dados()

        if df.empty:
            logger.error("Nenhum dado foi carregado!")
            return {}

        # Executar agregações
        resultados = {
            'estatisticas': self.calcular_estatisticas(df),
            'por_ano': self.agregar_por_ano(df),
            'por_bairro': self.agregar_por_bairro(df),
            'por_tipo': self.agregar_por_tipo(df),
            'por_mes': self.agregar_por_mes(df),
            'por_estacao': self.agregar_por_estacao(df),
            'por_dia_semana': self.agregar_por_dia_semana(df),
            'por_hora': self.agregar_por_hora(df),
            'por_bairro_ano': self.agregar_por_bairro_ano(df),
            'por_tipo_ano': self.agregar_por_tipo_ano(df)
        }

        logger.info("\n" + "=" * 70)
        logger.info("AGREGAÇÃO CONCLUÍDA")
        logger.info("=" * 70)

        return resultados

    def salvar_agregacoes(self, resultados: Dict):
        """
        Salva as agregações em arquivos CSV.

        Args:
            resultados: Dicionário com os resultados das agregações.
        """
        logger.info("\nSalvando agregações em arquivos CSV...")

        # Mapeamento de nomes de arquivos
        arquivos = {
            'por_ano': 'por_ano.csv',
            'por_bairro': 'por_bairro.csv',
            'por_tipo': 'por_tipo.csv',
            'por_mes': 'por_mes.csv',
            'por_estacao': 'por_estacao.csv',
            'por_dia_semana': 'por_dia_semana.csv',
            'por_hora': 'por_hora.csv',
            'por_bairro_ano': 'por_bairro_ano.csv',
            'por_tipo_ano': 'por_tipo_ano.csv'
        }

        for chave, nome_arquivo in arquivos.items():
            if chave in resultados and not resultados[chave].empty:
                caminho = self.diretorio_processados / nome_arquivo
                resultados[chave].to_csv(caminho, index=False, encoding='utf-8')
                logger.info(f"  Salvo: {nome_arquivo}")

        logger.info("\nTodas as agregações foram salvas!")


# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================

def main():
    """
    Função principal do script de agregação.
    """
    print("\n" + "=" * 70)
    print("SCRIPT 03 - AGREGAÇÃO DE DADOS")
    print("Análise agregada da Defesa Civil do Recife")
    print("=" * 70 + "\n")

    # Executar agregação
    agregacao = AgregacaoDados()
    resultados = agregacao.executar_agregacao()

    if not resultados:
        print("\nATENÇÃO: Nenhum dado foi processado!")
        print("Execute primeiro o script de limpeza (02_limpeza.py)")
    else:
        # Salvar agregações
        agregacao.salvar_agregacoes(resultados)

        print("\n" + "=" * 70)
        print("AGREGAÇÃO CONCLUÍDA COM SUCESSO")
        print("=" * 70)

        # Mostrar resumo
        estatisticas = resultados.get('estatisticas', {})
        print(f"\nResumo:")
        print(f"  Total de registros: {estatisticas.get('total_registros', 'N/A')}")

        periodo = estatisticas.get('periodo', {})
        if periodo:
            print(f"  Período: {periodo.get('ano_inicio', 'N/A')} - {periodo.get('ano_fim', 'N/A')}")

        sazonalidade = estatisticas.get('sazonalidade', {})
        if sazonalidade:
            print(f"  Mês com mais ocorrências: {sazonalidade.get('mes_mais_ocorrencias', 'N/A')}")
            print(f"  Estação com mais ocorrências: {sazonalidade.get('estacao_mais_ocorrencias', 'N/A')}")

        print(f"\nArquivos salvos em: dados/processados/")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    main()