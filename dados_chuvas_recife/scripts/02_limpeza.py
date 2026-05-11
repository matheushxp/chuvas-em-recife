#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script 02 - Limpeza e Preparação de Dados
==========================================
Executa a limpeza completa dos dados da Defesa Civil do Recife.

Transformações aplicadas:
- Unificação de todos os CSVs anuais em um DataFrame
- Conversão de datas para datetime
- Tratamento de encoding (utf-8, latin-1)
- Filtragem apenas para Recife
- Tratamento de valores nulos
- Normalização de nomes de bairros
- Criação de colunas derivadas:
  - ano, mes, dia, hora
  - dia_semana
  - estacao (verão/outono/inverno/primavera)
  - tipo_ocorrencia_normalizado

Autor: Engenheiro de Dados
Data: 2026-05-11
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import re

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

# Mapeamento de normalização de bairros (variações comuns -> padrão)
MAPA_BAIRROS = {
    # Variações comuns de nomes de bairros em Recife
    'afogados': 'afogados',
    'afOGADOS': 'afogados',
    'AFOGADOS': 'afogados',
    'agua fria': 'agua_fria',
    'agua_fria': 'agua_fria',
    'Água Fria': 'agua_fria',
    'boca do rio': 'boca_do_rio',
    'boca_do_rio': 'boca_do_rio',
    'Boca do Rio': 'boca_do_rio',
    'boa viagem': 'boa_viagem',
    'boa_viagem': 'boa_viagem',
    'Boa Viagem': 'boa_viagem',
    'boas novas': 'boas_novas',
    'boas_novas': 'boas_novas',
    'Boas Novas': 'boas_novas',
    'casa branca': 'casa_branca',
    'casa_branca': 'casa_branca',
    'Casa Branca': 'casa_branca',
    'campo grande': 'campo_grande',
    'campo_grande': 'campo_grande',
    'Campo Grande': 'campo_grande',
    'coelhos': 'coelhos',
    'COELHOS': 'coelhos',
    'cordeiro': 'cordeiro',
    'CORDEIRO': 'cordeiro',
    'derby': 'derby',
    'DERBY': 'derby',
    'dois Irmaos': 'dois_irmaos',
    'doisirmaos': 'dois_irmaos',
    'dois_irmaos': 'dois_irmaos',
    'dois irmaos': 'dois_irmaos',
    'engenho do meio': 'engenho_do_meio',
    'engenho_do_meio': 'engenho_do_meio',
    'Engenho do Meio': 'engenho_do_meio',
    'espinheiro': 'espinheiro',
    'ESPINHEIRO': 'espinheiro',
    'funk': 'funk',
    'FUNK': 'funk',
    'guabiraba': 'guabiraba',
    'GUABIRABA': 'guabiraba',
    'ilha do retorno': 'ilha_do_retorno',
    'ilha_do_retorno': 'ilha_do_retorno',
    'ipsep': 'ipsep',
    'IPSEP': 'ipsep',
    'jaqueira': 'jaqueira',
    'JAQUEIRA': 'jaqueira',
    'jardim são paulo': 'jardim_sao_paulo',
    'jardim_sao_paulo': 'jardim_sao_paulo',
    'Jardim São Paulo': 'jardim_sao_paulo',
    'madaleza': 'madaleza',
    'MADALEZA': 'madaleza',
    'madalena': 'madalena',
    'MADALENA': 'madalena',
    'mangabeira': 'mangabeira',
    'MANGABEIRA': 'mangabeira',
    'monteiro': 'monteiro',
    'MONTEIRO': 'monteiro',
    'nova descoberta': 'nova_descoberta',
    'nova_descoberta': 'nova_descoberta',
    'Nova Descoberta': 'nova_descoberta',
    'olinda': 'olinda',
    'OLINDA': 'olinda',
    'pau ferro': 'pau_ferro',
    'pau_ferro': 'pau_ferro',
    'Pau Ferro': 'pau_ferro',
    'pina': 'pina',
    'PINA': 'pina',
    'prado': 'prado',
    'PRADO': 'prado',
    'recife': 'recife',
    'RECIFE': 'recife',
    'rio doce': 'rio_doce',
    'rio_doce': 'rio_doce',
    'Rio Doce': 'rio_doce',
    'san martin': 'san_martin',
    'san_martin': 'san_martin',
    'San Martin': 'san_martin',
    'santa cruz': 'santa_cruz',
    'santa_cruz': 'santa_cruz',
    'Santa Cruz': 'santa_cruz',
    'santo amaro': 'santo_amaro',
    'santo_amaro': 'santo_amaro',
    'Santo Amaro': 'santo_amaro',
    'são josé': 'sao_jose',
    'sao_jose': 'sao_jose',
    'São José': 'sao_jose',
    'sao bento': 'sao_bento',
    'sao_bento': 'sao_bento',
    'São Bento': 'sao_bento',
    'sao geraldo': 'sao_geraldo',
    'sao_geraldo': 'sao_geraldo',
    'São Geraldo': 'sao_geraldo',
    'sao mateus': 'sao_mateus',
    'sao_mateus': 'sao_mateus',
    'São Mateus': 'sao_mateus',
    'sao paulo': 'sao_paulo',
    'sao_paulo': 'sao_paulo',
    'São Paulo': 'sao_paulo',
    'sao pedro': 'sao_pedro',
    'sao_pedro': 'sao_pedro',
    'São Pedro': 'sao_pedro',
    'sitio': 'sitio',
    'SITIO': 'sitio',
    'sítio': 'sitio',
    'tamarineira': 'tamarineira',
    'TAMARINEIRA': 'tamarineira',
    'torreão': 'torreao',
    'torreao': 'torreao',
    'Torreão': 'torreao',
    'torres': 'torres',
    'TORRES': 'torres',
    'varzea': 'varzea',
    'VARZEA': 'varzea',
    'várzea': 'varzea',
    'várzea': 'varzea',
    'vasco da gama': 'vasco_da_gama',
    'vasco_da_gama': 'vasco_da_gama',
    'Vasco da Gama': 'vasco_da_gama',
    'zumbi': 'zumbi',
    'ZUMBI': 'zumbi',
}

# Mapeamento de tipos de ocorrência para normalização
MAPA_TIPOS = {
    # Alagamentos
    'alagamento': 'alagamento',
    'alagamentos': 'alagamento',
    'ALAGAMENTO': 'alagamento',
    'ALAGAMENTOS': 'alagamento',
    'alagamento/enchente': 'alagamento',
    'alagamento e enchente': 'alagamento',
    'enchente': 'alagamento',
    'ENCHENTE': 'alagamento',
    'inundação': 'alagamento',
    'inundacao': 'alagamento',

    # Deslizamentos
    'deslizamento': 'deslizamento',
    'deslizamentos': 'deslizamento',
    'DESLIZAMENTO': 'deslizamento',
    'DESLIZAMENTOS': 'deslizamento',
    'deslizamento de terra': 'deslizamento',
    'deslizamento de barreiras': 'deslizamento',
    'deslizamento de encosta': 'deslizamento',
    'risco de deslizamento': 'deslizamento',
    'risco de escorregamento': 'deslizamento',

    # Vistorias
    'vistoria': 'vistoria',
    'VISTORIA': 'vistoria',
    'vistorias': 'vistoria',
    'VISTORIAS': 'vistoria',
    'vistoria técnica': 'vistoria',
    'vistoria tecnica': 'vistoria',

    # Ocorrências diversas
    'ocorrência': 'outros',
    'ocorrencia': 'outros',
    'OCORRÊNCIA': 'outros',
    'outros': 'outros',
    'OUTROS': 'outros',

    # Serviços
    'serviço': 'servico',
    'servico': 'servico',
    'SERVICO': 'servico',
    'SERViço': 'servico',

    # Lonas
    'lona': 'lona',
    'lonas': 'lona',
    'LONA': 'lona',
    'LONAS': 'lona',
    'instalação de lona': 'lona',
    'instalacao de lona': 'lona',

    # Remoções
    'remoção': 'remocao',
    'remocao': 'remocao',
    'REMOÇÃO': 'remocao',
    'remoção de entulho': 'remocao',
    'remocao de entulho': 'remocao',

    # Risco
    'risco': 'risco',
    'RISCO': 'risco',
    'risco estrutural': 'risco',
    'risco de queda': 'risco',
    'risco geotécnico': 'risco',
    'risco geotecnico': 'risco',
}


# ============================================================================
# CLASSE PRINCIPAL
# ============================================================================

class LimpezaDados:
    """
    Executa a limpeza e preparação dos dados da Defesa Civil do Recife.
    """

    def __init__(self, diretorio_dados: Path = None):
        """
        Inicializa o processo de limpeza.

        Args:
            diretorio_dados: Caminho para o diretório de dados brutos.
        """
        self.diretorio_dados = diretorio_dados or DIRETORIO_DADOS
        self.diretorio_processados = DIRETORIO_PROCESSADOS

        # Criar diretório de processados se não existir
        self.diretorio_processados.mkdir(parents=True, exist_ok=True)

        logger.info(f"Diretório de dados brutos: {self.diretorio_dados}")
        logger.info(f"Diretório de processados: {self.diretorio_processados}")

    def carregar_csv(self, caminho: Path) -> Optional[pd.DataFrame]:
        """
        Carrega um arquivo CSV tentando diferentes encodings.

        Args:
            caminho: Caminho do arquivo CSV.

        Returns:
            DataFrame carregado ou None se falhar.
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
                logger.info(f"  Carregado: {caminho.name} (encoding: {encoding}, registros: {len(df)}, colunas: {len(df.columns)})")
                return df
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.warning(f"  Erro ao carregar {caminho.name} com {encoding}: {e}")
                continue

        logger.error(f"  Não foi possível carregar {caminho.name}")
        return None

    def carregar_todos_csv(self) -> pd.DataFrame:
        """
        Carrega todos os arquivos CSV do diretório e os unifica.

        Returns:
            DataFrame unificado com todos os registros.
        """
        dataframes = []

        if not self.diretorio_dados.exists():
            logger.error(f"Diretório não encontrado: {self.diretorio_dados}")
            return pd.DataFrame()

        # Buscar arquivos CSV
        arquivos = [f for f in self.diretorio_dados.iterdir()
                    if f.is_file() and f.suffix.lower() == '.csv']

        if not arquivos:
            logger.warning("Nenhum arquivo CSV encontrado!")
            return pd.DataFrame()

        logger.info(f"\nCarregando {len(arquivos)} arquivos CSV...")

        for caminho in arquivos:
            df = self.carregar_csv(caminho)
            if df is not None:
                # Adicionar coluna com ano de origem (se possível)
                # Tenta extrair ano do nome do arquivo
                nome = caminho.stem
                ano = None
                for parte in nome.split('_'):
                    if parte.isdigit() and len(parte) == 4:
                        ano = int(parte)
                        break
                if ano:
                    df['_ano_origem'] = ano
                dataframes.append(df)

        if not dataframes:
            logger.error("Nenhum DataFrame foi carregado!")
            return pd.DataFrame()

        # Unificar todos os DataFrames
        logger.info(f"\nUnificando {len(dataframes)} DataFrames...")
        df_unificado = pd.concat(dataframes, ignore_index=True)

        logger.info(f"Total de registros unificados: {len(df_unificado)}")

        return df_unificado

    def converter_datas(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Converte colunas de data para datetime.

        Args:
            df: DataFrame a ser processado.

        Returns:
            DataFrame com datas convertidas.
        """
        logger.info("\nConvertendo colunas de data...")

        # Identificar colunas de data
        colunas_data = [col for col in df.columns if 'data' in col.lower()]

        for col in colunas_data:
            logger.info(f"  Processando coluna: {col}")

            # Tentar diferentes formatos de data
            formatos = [
                '%Y-%m-%d',
                '%d/%m/%Y',
                '%d/%m/%Y %H:%M:%S',
                '%d/%m/%Y %H:%M',
                '%Y/%m/%d',
                '%d-%m-%Y',
                '%d-%m-%Y %H:%M:%S',
            ]

            # Primeiro, tentar inferência automática
            try:
                df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')
                logger.info(f"    Convertido (inferido): {col}")
                continue
            except:
                pass

            # Tentar formatos específicos
            for formato in formatos:
                try:
                    df[col] = pd.to_datetime(df[col], format=formato, errors='coerce')
                    logger.info(f"    Convertido ({formato}): {col}")
                    break
                except:
                    continue

            # Contar conversões bem-sucedidas
            nao_nulos = df[col].notna().sum()
            logger.info(f"    Registros com data válida: {nao_nulos}")

        return df

    def filtrar_recife(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filtra apenas registros do Recife (quando possível).

        Args:
            df: DataFrame a ser filtrado.

        Returns:
            DataFrame filtrado.
        """
        logger.info("\nFiltrando registros...")

        registros_iniciais = len(df)

        # Se houver coluna 'regional', filtrar apenas Recife
        if 'regional' in df.columns:
            # Valores típicos para Recife
            regionais_recife = ['recife', 'recife/pe', 'recife - pe', 'r mr', 'metropolitana']
            df = df[df['regional'].str.lower().isin(regionais_recife) | df['regional'].isna()]
            logger.info(f"  Filtrado por regional: {registros_iniciais} -> {len(df)}")

        # Se houver coluna de bairro, verificar se há registros válidos
        if 'bairro' in df.columns:
            # Remover registros sem bairro
            df_sem_bairro = df['bairro'].isna().sum()
            logger.info(f"  Registros sem bairro: {df_sem_bairro}")

        logger.info(f"  Total após filtragem: {len(df)}")

        return df

    def tratar_nulos(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Trata valores nulos no DataFrame.

        Args:
            df: DataFrame a ser processado.

        Returns:
            DataFrame com nulos tratados.
        """
        logger.info("\nTratando valores nulos...")

        # Contagem inicial de nulos
        nulos_iniciais = df.isna().sum().sum()
        logger.info(f"  Total de nulos inicial: {nulos_iniciais}")

        # Para colunas de texto, preencher com 'não informado'
        colunas_texto = df.select_dtypes(include=['object']).columns
        for col in colunas_texto:
            nulos = df[col].isna().sum()
            if nulos > 0:
                df[col] = df[col].fillna('não informado')
                logger.info(f"    {col}: {nulos} nulos preenchidos com 'não informado'")

        # Para colunas numéricas, preencher com 0
        colunas_numericas = df.select_dtypes(include=['number']).columns
        for col in colunas_numericas:
            nulos = df[col].isna().sum()
            if nulos > 0:
                df[col] = df[col].fillna(0)
                logger.info(f"    {col}: {nulos} nulos preenchidos com 0")

        nulos_finais = df.isna().sum().sum()
        logger.info(f"  Total de nulos final: {nulos_finais}")

        return df

    def normalizar_bairros(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normaliza nomes de bairros.

        Args:
            df: DataFrame a ser processado.

        Returns:
            DataFrame com bairros normalizados.
        """
        logger.info("\nNormalizando nomes de bairros...")

        if 'bairro' not in df.columns:
            logger.warning("  Coluna 'bairro' não encontrada!")
            return df

        # Converter para minúsculas
        df['bairro_normalizado'] = df['bairro'].str.lower().str.strip()

        # Aplicar mapeamento
        df['bairro_normalizado'] = df['bairro_normalizado'].replace(MAPA_BAIRROS)

        # Contagem de bairros únicos
        logger.info(f"  Bairros únicos (original): {df['bairro'].nunique()}")
        logger.info(f"  Bairros únicos (normalizado): {df['bairro_normalizado'].nunique()}")

        # Mostrar os 10 bairros mais frequentes
        top_bairros = df['bairro_normalizado'].value_counts().head(10)
        logger.info(f"  Top 10 bairros:")
        for bairro, qtd in top_bairros.items():
            logger.info(f"    {bairro}: {qtd}")

        return df

    def normalizar_tipos(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normaliza tipos de ocorrência.

        Args:
            df: DataFrame a ser processado.

        Returns:
            DataFrame com tipos normalizados.
        """
        logger.info("\nNormalizando tipos de ocorrência...")

        if 'tipo_ocorrencia' not in df.columns:
            logger.warning("  Coluna 'tipo_ocorrencia' não encontrada!")
            return df

        # Converter para minúsculas
        df['tipo_ocorrencia_normalizado'] = df['tipo_ocorrencia'].str.lower().str.strip()

        # Aplicar mapeamento
        df['tipo_ocorrencia_normalizado'] = df['tipo_ocorrencia_normalizado'].replace(MAPA_TIPOS)

        # Contagem de tipos únicos
        logger.info(f"  Tipos únicos (original): {df['tipo_ocorrencia'].nunique()}")
        logger.info(f"  Tipos únicos (normalizado): {df['tipo_ocorrencia_normalizado'].nunique()}")

        # Mostrar distribuição
        dist_tipos = df['tipo_ocorrencia_normalizado'].value_counts()
        logger.info(f"  Distribuição de tipos:")
        for tipo, qtd in dist_tipos.items():
            logger.info(f"    {tipo}: {qtd}")

        return df

    def criar_colunas_derivadas(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Cria colunas derivadas a partir da data.

        Args:
            df: DataFrame a ser processado.

        Returns:
            DataFrame com colunas derivadas.
        """
        logger.info("\nCriando colunas derivadas...")

        # Identificar coluna de data
        colunas_data = [col for col in df.columns if 'data' in col.lower() and 'atendimento' in col.lower()]

        if not colunas_data:
            # Tentar qualquer coluna de data
            colunas_data = [col for col in df.columns if 'data' in col.lower()]

        if not colunas_data:
            logger.warning("  Nenhuma coluna de data encontrada!")
            return df

        coluna_data = colunas_data[0]
        logger.info(f"  Usando coluna de data: {coluna_data}")

        # Converter para datetime se ainda não for
        if not pd.api.types.is_datetime64_any_dtype(df[coluna_data]):
            df[coluna_data] = pd.to_datetime(df[coluna_data], errors='coerce')

        # Filtrar apenas registros com data válida
        df_com_data = df[df[coluna_data].notna()].copy()
        logger.info(f"  Registros com data válida: {len(df_com_data)}")

        if len(df_com_data) > 0:
            # Ano
            df_com_data['ano'] = df_com_data[coluna_data].dt.year
            logger.info(f"    Coluna 'ano' criada")

            # Mês
            df_com_data['mes'] = df_com_data[coluna_data].dt.month
            logger.info(f"    Coluna 'mes' criada")

            # Dia
            df_com_data['dia'] = df_com_data[coluna_data].dt.day
            logger.info(f"    Coluna 'dia' criada")

            # Hora
            df_com_data['hora'] = df_com_data[coluna_data].dt.hour
            logger.info(f"    Coluna 'hora' criada")

            # Dia da semana (0 = segunda, 6 = domingo)
            df_com_data['dia_semana'] = df_com_data[coluna_data].dt.dayofweek
            df_com_data['dia_semana_nome'] = df_com_data[coluna_data].dt.day_name()
            logger.info(f"    Colunas 'dia_semana' e 'dia_semana_nome' criadas")

            # Estação do ano
            def get_estacao(mes):
                """Retorna a estação do ano para o hemisfério sul."""
                if mes in [12, 1, 2]:
                    return 'verao'
                elif mes in [3, 4, 5]:
                    return 'outono'
                elif mes in [6, 7, 8]:
                    return 'inverno'
                else:  # 9, 10, 11
                    return 'primavera'

            df_com_data['estacao'] = df_com_data['mes'].apply(get_estacao)
            logger.info(f"    Coluna 'estacao' criada")

            # Atualizar o DataFrame original
            # Primeiro, garantir que as colunas existam no df original
            for col in ['ano', 'mes', 'dia', 'hora', 'dia_semana', 'dia_semana_nome', 'estacao']:
                if col not in df.columns:
                    df[col] = None

            # Copiar valores para o df original
            indices_validos = df_com_data.index
            for col in ['ano', 'mes', 'dia', 'hora', 'dia_semana', 'dia_semana_nome', 'estacao']:
                df.loc[indices_validos, col] = df_com_data[col].values

        # Estatísticas das colunas criadas
        logger.info(f"\n  Estatísticas das colunas derivadas:")
        logger.info(f"    Anos disponíveis: {sorted(df['ano'].dropna().unique().astype(int))}")
        logger.info(f"    Mês com mais ocorrências: {df['mes'].mode().values[0] if not df['mes'].mode().empty else 'N/A'}")
        logger.info(f"    Dia da semana mais comum: {df['dia_semana_nome'].mode().values[0] if not df['dia_semana_nome'].mode().empty else 'N/A'}")
        logger.info(f"    Estação mais comum: {df['estacao'].mode().values[0] if not df['estacao'].mode().empty else 'N/A'}")

        return df

    def executar_limpeza(self) -> pd.DataFrame:
        """
        Executa todo o pipeline de limpeza.

        Returns:
            DataFrame limpo e preparado.
        """
        logger.info("=" * 70)
        logger.info("LIMPEZA DE DADOS - DEFESA CIVIL DO RECIFE")
        logger.info("=" * 70)

        # 1. Carregar todos os CSVs
        logger.info("\n[1/6] Carregando arquivos CSV...")
        df = self.carregar_todos_csv()

        if df.empty:
            logger.error("Nenhum dado foi carregado!")
            return pd.DataFrame()

        logger.info(f"  Total de registros carregados: {len(df)}")

        # 2. Converter datas
        logger.info("\n[2/6] Convertendo datas...")
        df = self.converter_datas(df)

        # 3. Filtrar Recife
        logger.info("\n[3/6] Filtrando registros...")
        df = self.filtrar_recife(df)

        # 4. Tratar nulos
        logger.info("\n[4/6] Tratando valores nulos...")
        df = self.tratar_nulos(df)

        # 5. Normalizar bairros
        logger.info("\n[5/6] Normalizando bairros...")
        df = self.normalizar_bairros(df)

        # 6. Normalizar tipos de ocorrência
        logger.info("\n[6/6] Normalizando tipos de ocorrência...")
        df = self.normalizar_tipos(df)

        # 7. Criar colunas derivadas
        logger.info("\n[7/7] Criando colunas derivadas...")
        df = self.criar_colunas_derivadas(df)

        logger.info("\n" + "=" * 70)
        logger.info("LIMPEZA CONCLUÍDA")
        logger.info(f"  Total de registros processados: {len(df)}")
        logger.info(f"  Total de colunas: {len(df.columns)}")
        logger.info("=" * 70)

        return df

    def salvar_dados(self, df: pd.DataFrame, nome_arquivo: str = "atendimentos_unificado.csv") -> Path:
        """
        Salva o DataFrame processado em CSV.

        Args:
            df: DataFrame a ser salvo.
            nome_arquivo: Nome do arquivo de saída.

        Returns:
            Caminho do arquivo salvo.
        """
        caminho_saida = self.diretorio_processados / nome_arquivo

        # Salvar em CSV com compressão se o arquivo for grande
        if len(df) > 100000:
            caminho_saida = caminho_saida.with_suffix('.csv.gz')
            df.to_csv(caminho_saida, index=False, encoding='utf-8', compression='gzip')
        else:
            df.to_csv(caminho_saida, index=False, encoding='utf-8')

        logger.info(f"\nDados salvos em: {caminho_saida}")
        logger.info(f"  Tamanho: {caminho_saida.stat().st_size / 1024 / 1024:.2f} MB")

        return caminho_saida


# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================

def main():
    """
    Função principal do script de limpeza.
    """
    print("\n" + "=" * 70)
    print("SCRIPT 02 - LIMPEZA E PREPARAÇÃO DE DADOS")
    print("Processamento de dados da Defesa Civil do Recife")
    print("=" * 70 + "\n")

    # Executar limpeza
    limpeza = LimpezaDados()
    df_limpo = limpeza.executar_limpeza()

    if df_limpo.empty:
        print("\nATENÇÃO: Nenhum dado foi processado!")
        print("Execute o script de coleta de dados primeiro.")
    else:
        # Salvar dados processados
        caminho = limpeza.salvar_dados(df_limpo)

        print("\n" + "=" * 70)
        print("LIMPEZA CONCLUÍDA COM SUCESSO")
        print("=" * 70)
        print(f"\nArquivo salvo: {caminho.name}")
        print(f"Total de registros: {len(df_limpo)}")
        print(f"Total de colunas: {len(df_limpo.columns)}")
        print("\nColunas disponíveis:")
        for col in df_limpo.columns:
            print(f"  - {col}")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    main()