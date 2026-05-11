@echo off
REM Script de Execucao - Coleta de Dados de Chuvas em Recife-PE
REM =====================================================
REM Executa todos os scripts de coleta e analise
REM
REM Uso: executar_coleta.bat

echo.
echo ==================================================
echo Coleta de Dados - Impacto das Chuvas em Recife-PE
echo ==================================================
echo.

REM VerificarPython
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado!
    echo Instale o Python 3.8+ e tente novamente.
    pause
    exit /b 1
)

echo [OK] Python encontrado

REM Verificardependencias
echo.
echo Verificando dependencias...
pip show requests >nul 2>&1
if errorlevel 1 (
    echo Instalando dependencias...
    pip install requests pandas
)

REM Criar estrutura de diretorios
echo.
echo Criando estrutura de diretorios...
if not exist "dados\brutos" mkdir dados\brutos
if not exist "dados\processados" mkdir dados\processados
if not exist "dados\output" mkdir dados\output
if not exist "logs" mkdir logs

echo.
echo ==================================================
echo ETAPA 1: Coleta de Dados do Recife
echo ==================================================
python scripts\coleta_dados_recife.py
if errorlevel 1 (
    echo AVISO: Erro na coleta do Recife (continuando...) >&2
)

echo.
echo ==================================================
echo ETAPA 2: Coleta de Dados da APAC
echo ==================================================
python scripts\coleta_dados_apac.py
if errorlevel 1 (
    echo AVISO: Erro na coleta da APAC (continuando...) >&2
)

echo.
echo ==================================================
echo ETAPA 3: Leitura e Analise
echo ==================================================
python scripts\leitura_analise.py

echo.
echo ==================================================
echo Coleta concluida!
echo ==================================================
echo.
echo Resultados em:
echo   dados\brutos\      - Dados originais
echo   dados\processados - Dados processados
echo   logs\             - Logs deexecucao
echo.
pause