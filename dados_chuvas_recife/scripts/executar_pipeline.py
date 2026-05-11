#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script Principal - Execução do Pipeline de Dados
=================================================
Orquestra a execução completa do pipeline de dados:
1. Diagnóstico (01_diagnostico.py)
2. Limpeza (02_limpeza.py)
3. Agregação (03_agregacao.py)

Este script coordena todo o fluxo de processamento dos dados da
Defesa Civil do Recife, desde a análise inicial até a geração
de métricas agregadas.

Autor: Engenheiro de Dados
Data: 2026-05-11
"""

import sys
import io
import logging

# Configurar encoding UTF-8 para stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import importlib.util
from pathlib import Path
from datetime import datetime

# Adicionar o diretório de scripts ao path
DIRETORIO_SCRIPT = Path(__file__).parent
sys.path.insert(0, str(DIRETORIO_SCRIPT))

# Função para importar módulos com nomes numéricos
def import_module_from_file(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Importar os módulos do pipeline
mod_diagnostico = import_module_from_file("diagnostico", DIRETORIO_SCRIPT / "01_diagnostico.py")
mod_limpeza = import_module_from_file("limpeza", DIRETORIO_SCRIPT / "02_limpeza.py")
mod_agregacao = import_module_from_file("agregacao", DIRETORIO_SCRIPT / "03_agregacao.py")

DiagnosticoDados = mod_diagnostico.DiagnosticoDados
LimpezaDados = mod_limpeza.LimpezaDados
AgregacaoDados = mod_agregacao.AgregacaoDados

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONSTANTES
# ============================================================================

DIRETORIO_DADOS = DIRETORIO_SCRIPT.parent / "dados"
DIRETORIO_BRUTOS = DIRETORIO_DADOS / "brutos" / "defesa_civil"
DIRETORIO_PROCESSADOS = DIRETORIO_DADOS / "processados"


# ============================================================================
# CLASSE PRINCIPAL
# ============================================================================

class PipelineDados:
    """
    Orquestra a execução completa do pipeline de dados.
    """

    def __init__(self):
        """
        Inicializa o pipeline.
        """
        self.inicio = datetime.now()
        logger.info("=" * 70)
        logger.info("PIPELINE DE DADOS - CHUVAS EM RECIFE")
        logger.info(f"Início: {self.inicio.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 70)

        # Criar diretórios necessários
        DIRETORIO_BRUTOS.mkdir(parents=True, exist_ok=True)
        DIRETORIO_PROCESSADOS.mkdir(parents=True, exist_ok=True)

    def verificar_dados_brutos(self) -> bool:
        """
        Verifica se existem dados brutos para processamento.

        Returns:
            True se existem dados, False caso contrário.
        """
        logger.info("\nVerificando dados brutos...")

        if not DIRETORIO_BRUTOS.exists():
            logger.error(f"Diretório não encontrado: {DIRETORIO_BRUTOS}")
            return False

        # Listar arquivos CSV
        arquivos = list(DIRETORIO_BRUTOS.glob("*.csv"))

        if not arquivos:
            logger.warning("Nenhum arquivo CSV encontrado no diretório de dados brutos!")
            logger.info("\nPara continuar, você precisa:")
            logger.info("  1. Baixar os dados do portal de dados abertos do Recife:")
            logger.info("     https://dados.recife.pe.gov.br")
            logger.info("  2. Ou executar o script de coleta:")
            logger.info("     python scripts/coleta_dados_recife.py")
            return False

        logger.info(f"  Encontrados {len(arquivos)} arquivos CSV:")
        for arq in arquivos:
            logger.info(f"    - {arq.name}")

        return True

    def executar_etapa1_diagnostico(self) -> bool:
        """
        Executa a etapa 1: Diagnóstico de dados.

        Returns:
            True se bem-sucedido, False caso contrário.
        """
        logger.info("\n" + "=" * 70)
        logger.info("ETAPA 1: DIAGNÓSTICO DE DADOS")
        logger.info("=" * 70)

        try:
            diagnostico = DiagnosticoDados()
            resultado = diagnostico.executar_diagnostico()

            if 'erro' in resultado:
                logger.error(f"Diagnóstico falhou: {resultado['erro']}")
                return False

            logger.info("\nDiagnóstico concluído com sucesso!")
            return True

        except Exception as e:
            logger.error(f"Erro no diagnóstico: {e}")
            return False

    def executar_etapa2_limpeza(self) -> bool:
        """
        Executa a etapa 2: Limpeza e preparação de dados.

        Returns:
            True se bem-sucedido, False caso contrário.
        """
        logger.info("\n" + "=" * 70)
        logger.info("ETAPA 2: LIMPEZA E PREPARAÇÃO DE DADOS")
        logger.info("=" * 70)

        try:
            limpeza = LimpezaDados()
            df_limpo = limpeza.executar_limpeza()

            if df_limpo.empty:
                logger.error("Limpeza falhou: Nenhum dado processado!")
                return False

            # Salvar dados limpos
            caminho = limpeza.salvar_dados(df_limpo)

            logger.info(f"\nLimpeza concluída com sucesso!")
            logger.info(f"  Arquivo salvo: {caminho.name}")
            logger.info(f"  Registros processados: {len(df_limpo)}")

            return True

        except Exception as e:
            logger.error(f"Erro na limpeza: {e}")
            return False

    def executar_etapa3_agregacao(self) -> bool:
        """
        Executa a etapa 3: Agregação de dados.

        Returns:
            True se bem-sucedido, False caso contrário.
        """
        logger.info("\n" + "=" * 70)
        logger.info("ETAPA 3: AGREGAÇÃO DE DADOS")
        logger.info("=" * 70)

        try:
            agregacao = AgregacaoDados()
            resultados = agregacao.executar_agregacao()

            if not resultados:
                logger.error("Agregação falhou: Nenhum resultado gerado!")
                return False

            # Salvar agregações
            agregacao.salvar_agregacoes(resultados)

            logger.info("\nAgregação concluída com sucesso!")

            # Mostrar resumo
            estatisticas = resultados.get('estatisticas', {})
            logger.info(f"  Total de registros: {estatisticas.get('total_registros', 'N/A')}")

            periodo = estatisticas.get('periodo', {})
            if periodo:
                logger.info(f"  Período: {periodo.get('ano_inicio', 'N/A')} - {periodo.get('ano_fim', 'N/A')}")

            return True

        except Exception as e:
            logger.error(f"Erro na agregação: {e}")
            return False

    def executar_pipeline_completo(self, etapas: list = None) -> bool:
        """
        Executa o pipeline completo ou etapas específicas.

        Args:
            etapas: Lista de etapas a executar. Se None, executa todas.
                    Opções: ['diagnostico', 'limpeza', 'agregacao']

        Returns:
            True se todas as etapas foram bem-sucedidas, False caso contrário.
        """
        if etapas is None:
            etapas = ['diagnostico', 'limpeza', 'agregacao']

        resultados = {}

        # Verificar dados brutos (exceto se for apenas diagnóstico)
        if 'limpeza' in etapas or 'agregacao' in etapas:
            if not self.verificar_dados_brutos():
                logger.error("Não é possível continuar sem dados brutos!")
                return False

        # Executar etapas
        if 'diagnostico' in etapas:
            resultados['diagnostico'] = self.executar_etapa1_diagnostico()

        if 'limpeza' in etapas:
            resultados['limpeza'] = self.executar_etapa2_limpeza()

        if 'agregacao' in etapas:
            resultados['agregacao'] = self.executar_etapa3_agregacao()

        # Calcular tempo total
        fim = datetime.now()
        duracao = fim - self.inicio

        logger.info("\n" + "=" * 70)
        logger.info("RESUMO DO PIPELINE")
        logger.info("=" * 70)

        for etapa, sucesso in resultados.items():
            status = "✓ SUCESSO" if sucesso else "✗ FALHA"
            logger.info(f"  {etapa.capitalize()}: {status}")

        logger.info(f"\nTempo total de execução: {duracao}")
        logger.info(f"Início: {self.inicio.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Fim: {fim.strftime('%Y-%m-%d %H:%M:%S')}")

        # Listar arquivos gerados
        logger.info("\nArquivos gerados:")
        for f in DIRETORIO_PROCESSADOS.iterdir():
            if f.is_file():
                tamanho_kb = f.stat().st_size / 1024
                logger.info(f"  - {f.name} ({tamanho_kb:.1f} KB)")

        logger.info("=" * 70)

        # Retornar True apenas se todas as etapas foram bem-sucedidas
        return all(resultados.values())

    def listar_arquivos_gerados(self):
        """
        Lista os arquivos gerados pelo pipeline.
        """
        logger.info("\nArquivos gerados pelo pipeline:")

        if not DIRETORIO_PROCESSADOS.exists():
            logger.warning("Diretório de processados não existe!")
            return

        arquivos = list(DIRETORIO_PROCESSADOS.iterdir())
        if not arquivos:
            logger.warning("Nenhum arquivo encontrado!")
            return

        for f in arquivos:
            if f.is_file():
                tamanho = f.stat().st_size
                if tamanho > 1024 * 1024:
                    tamanho_str = f"{tamanho / 1024 / 1024:.2f} MB"
                else:
                    tamanho_str = f"{tamanho / 1024:.1f} KB"
                logger.info(f"  {f.name} ({tamanho_str})")


# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================

def main():
    """
    Função principal do script de execução do pipeline.
    """
    print("\n" + "=" * 70)
    print("PIPELINE DE DADOS - CHUVAS EM RECIFE")
    print("Execução completa: Diagnóstico → Limpeza → Agregação")
    print("=" * 70 + "\n")

    # Parse de argumentos da linha de comando
    etapas = None
    if len(sys.argv) > 1:
        etapas = sys.argv[1:]
        # Validar etapas
        etapas_validas = ['diagnostico', 'limpeza', 'agregacao']
        for etapa in etapas:
            if etapa not in etapas_validas:
                print(f"Erro: Etapa '{etapa}' não é válida!")
                print(f"Opções válidas: {etapas_validas}")
                print("\nUso: python executar_pipeline.py [diagnostico] [limpeza] [agregacao]")
                print("Exemplo: python executar_pipeline.py diagnostico limpeza agregacao")
                sys.exit(1)

    # Criar e executar pipeline
    pipeline = PipelineDados()

    if etapas:
        print(f"\nExecutando apenas as etapas: {', '.join(etapas)}\n")
        sucesso = pipeline.executar_pipeline_completo(etapas)
    else:
        print("\nExecutando pipeline completo...\n")
        sucesso = pipeline.executar_pipeline_completo()

    # Resultado final
    print("\n" + "=" * 70)
    if sucesso:
        print("PIPELINE EXECUTADO COM SUCESSO!")
        print("\nOs dados processados estão disponíveis em:")
        print(f"  {DIRETORIO_PROCESSADOS}")
    else:
        print("PIPELINE EXECUTADO COM ERROS!")
        print("\nVerifique os logs acima para mais detalhes.")
    print("=" * 70 + "\n")

    sys.exit(0 if sucesso else 1)


if __name__ == "__main__":
    main()