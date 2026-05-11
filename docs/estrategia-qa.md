# Estrategia de Testes e Qualidade - Projeto Chuvas Recife-PE

## 1. Visao Geral do Projeto

### Contexto
- **Objetivo**: Analisar o impacto das chuvas em Recife-PE utilizando dados da APAC Pernambuco e Defesa Civil Recife
- **Stack Tecnologica**: Pandas -> PySpark -> Power BI
- **Entregas**: Dashboard Power BI + Scripts Python + Relatorio
- **Perguntas de Negocio**: 12 perguntas a serem respondidas

### Fontes de Dados
| Fonte | Tipo | Frequencia Atualizacao |
|-------|------|----------------------|
| APAC Pernambuco | Dados pluviometricos | Diaria |
| Defesa Civil Recife | Ocorrencias/alertas | Tempo real |

---

## 2. Matriz de Testes

### 2.1 Testes Unitarios

**Objetivo**: Validar transformacoes individuais e funcoes isoladas

| Tipo de Teste | Cobertura | Frequencia | Responsavel |
|---------------|-----------|------------|-------------|
| Validacao de funcoes de transformacao | 100% das funcoes criticas | A cada commit | Engenheiro de Dados |
| Testes de parsing de datas | 100% dos formatos esperados | A cada commit | Engenheiro de Dados |
| Validacao de calculos matematicos | 100% das formulas | A cada commit | Engenheiro de Dados |
| Testes de validacao de schema | 100% dos schemas | A cada commit | Engenheiro de Dados |
| Testes de tratamento de nulos | 100% dos campos nullable | A cada commit | Engenheiro de Dados |

**Ferramentas**: pytest, unittest (Python)

**Criterio de Aceite**: 80% de cobertura minima, 100% das funcoes criticas

### 2.2 Testes de Integracao

**Objetivo**: Validar o fluxo completo entre etapas do pipeline

| Tipo de Teste | Cobertura | Frequencia | Responsavel |
|---------------|-----------|------------|-------------|
| Pipeline Pandas -> PySpark | 100% dos datasets | A cada build | Engenheiro de Dados |
| Integracao fontes APAC + Defesa Civil | 100% das juncoes | A cada build | Engenheiro de Dados |
| Validacao ETL completo | 100% das transformacoes | Diario | Engenheiro de Dados |
| Testes de carga (dados reais) | 100% dos volumes esperados | Semanal | Engenheiro de Dados |
| Validacao de outputs intermedios | 100% dos dataframes | A cada execucao | Engenheiro de Dados |

**Ferramentas**: pytest, Great Expectations

**Criterio de Aceite**: 100% dos testes passando, sem regressao de dados

### 2.3 Testes de Qualidade de Dados

**Objetivo**: Garantir que os dados atendam aos padroes de qualidade

| Tipo de Teste | Cobertura | Frequencia | Responsavel |
|---------------|-----------|------------|-------------|
| Completude (nulls/ausentes) | 100% dos campos | A cada carga | Engenheiro QA |
| Consistência (formatos/ranges) | 100% das regras | A cada carga | Engenheiro QA |
| Atualidade (dados dentro do periodo) | 100% dos datasets | A cada carga | Engenheiro QA |
| Duplicatas | 100% das chaves | A cada carga | Engenheiro QA |
| Outliers | 100% das metricas numericas | A cada carga | Engenheiro QA |
| Consistencia entre fontes | 100% das juncoes | A cada carga | Engenheiro QA |

**Ferramentas**: Great Expectations, Pandas Profiling, PySpark validations

**Criterio de Aceite**: 95% de qualidade por dataset, 0% dados criticos faltando

---

## 3. Checklist de Qualidade por Fonte de Dados

### 3.1 APAC Pernambuco - Dados Pluviometricos

| Checklist Item | Criterio | Severidade | Acao se Falhar |
|----------------|----------|------------|-----------------|
| Campo data presente | NOT NULL | Critica | Rejeitar carga |
| Campo estacao presente | NOT NULL | Critica | Rejeitar carga |
| Campo precipitacao presente | NOT NULL | Critica | Rejeitar carga |
| Formato data valido | YYYY-MM-DD | Alta | Log + conversao |
| Precipitacao >= 0 | Range [0, 500] mm | Alta | Investigar outlier |
| Estacao em catalogo | Valido | Alta | Marcar como desconhecido |
| Data dentro do periodo esperado | Ultimos 30 dias | Media | Log + alerta |
| Sem duplicatas (estacao + data) | Unico | Alta | Deduplicar |
| Volume esperado | > 80% do habitual | Media | Alerta de fonte |

### 3.2 Defesa Civil Recife - Ocorrencias

| Checklist Item | Criterio | Severidade | Acao se Falhar |
|----------------|----------|------------|-----------------|
| Campo data/hora presente | NOT NULL | Critica | Rejeitar carga |
| Campo tipo ocorrencia presente | NOT NULL | Critica | Rejeitar carga |
| Campo bairro presente | NOT NULL | Alta | Marcar como desconhecido |
| Formato data valido | ISO 8601 | Alta | Log + conversao |
| Tipo ocorrencia em catalogo | Valido | Alta | Marcar como outro |
| Bairro em catalogo | Valido | Media | Marcar como desconhecido |
| Latitude/Longitude validos | Range Recife | Media | Geocodificar |
| Data dentro do periodo esperado | Ultimos 7 dias | Media | Log + alerta |
| Sem duplicatas (id unico) | Unico | Alta | Manter mais recente |
| Volume esperado | > 70% do habitual | Media | Alerta de fonte |

---

## 4. Validacoes Especificas para as 12 Perguntas de Negocio

### 4.1 Sanity Checks por Pergunta

| # | Pergunta (Exemplo) | Sanity Check | Limite Variacao | Prioridade |
|---|-------------------|--------------|-----------------|------------|
| 1 | Total precipitacao mensal | Soma diaria <= 300mm/dia | +/- 10% vs mes anterior | Alta |
| 2 | Numero de alertas por bairro | Alertas > 0 | +/- 20% vs media historica | Alta |
| 3 | Tempo medio de resposta | Entre 0 e 48h | +/- 15% vs mes anterior | Alta |
| 4 | Areas de risco com mais ocorrencias | Top 10 bairros | Sem variacao brusca | Media |
| 5 | Correlacao chuva x ocorrencias | Coef > 0.5 | Estavel | Alta |
| 6 | Precipitacao por estacao | Cada estacao > 0 | Sem dados zerados | Alta |
| 7 | Evolucao temporal de alertas | Sequencia temporal | Sem gaps > 2 dias | Media |
| 8 | Distribuicao geografica | Coordenadas validas | Dentro de Recife | Alta |
| 9 | Tipos de ocorrencia mais comuns | Soma = total | 100% consistencia | Alta |
| 10 | Impacto em areas vulneraveis | % areas risco | >= 0, <= 100% | Alta |
| 11 | Tendencia de precipitacao | Serie temporal | Sem outliers | Media |
| 12 | Comparativo anual | Ano atual vs anterior | Dados compativeis | Alta |

### 4.2 Limites de Variacao Aceitaveis

| Metrica | Limite Inferior | Limite Superior | Acao se Exceder |
|---------|-----------------|-----------------|------------------|
| Precipitacao diaria | 0 mm | 300 mm | Investigar sensor |
| Numero de alertas | 0 | 1000/dia | Verificar fonte |
| Tempo resposta | 0 min | 2880 min (48h) | Validar dado |
| Taxa de nulos | 0% | 15% | Investigar origem |
| Duplicatas | 0% | 5% | Deduplicar |
| Variação mensal | -30% | +30% | Documentar razao |

---

## 5. Processo de Code Review

### 5.1 Fluxo de Revisao

```
Desenvolvedor -> Pull Request -> Revisao Automatica -> Revisao Manual -> Aprovacao
```

### 5.2 Checklist de Code Review

**Antes de submeter (Desenvolvedor)**:
- [ ] Todos os testes unitarios passando
- [ ] Cobertura de testes >= 80%
- [ ] Sem warnings de linter (pylint, flake8)
- [ ] Documentacao atualizada
- [ ] Sem secrets/credenciais no codigo
- [ ] Nome de variaveis descritivos
- [ ] Funcoes com maximo 50 linhas
- [ ] Comentarios em logicas complexas

**Durante a revisao (Revisor)**:
- [ ] Logica de negocio correta
- [ ] Tratamento de erros adequado
- [ ] Performance aceitavel
- [ ] Seguranca dos dados
- [ ] Segue padroes do projeto
- [ ] Testes suficientes para o codigo
- [ ] Nomeclatura consistente

**Apos aprovacao**:
- [ ] Merge para branch principal
- [ ] Execução de testes de integracao
- [ ] Atualizacao de documentacao
- [ ] Notificacao no canal do projeto

### 5.3 Critérios de Aprovacao

| Criterio | Peso | Nota Minima |
|----------|------|-------------|
| Funcionalidade | 30% | 70% |
| Cobertura de testes | 25% | 80% |
| Padroes de codigo | 20% | 80% |
| Documentacao | 15% | 70% |
| Seguranca | 10% | 100% |

---

## 6. Criterios de Aceite do Dashboard Power BI

### 6.1 Funcionalidade

| Criterio | Descricao | Metodo Teste | Aceite |
|----------|-----------|--------------|--------|
| Todos os visuais carregam | Cada grafico/tabela renderiza | Visual inspection | 100% |
| Filtros funcionais | Todos os filtros respondem | Teste interativo | 100% |
| Navegacao entre abas | Transicao suave | Teste interativo | 100% |
| Tooltips funcionais | Informacoes extras aparecem | Hover test | 100% |
| Exportacao funciona | PDF/Excel exportavel | Teste funcional | 100% |
| Atualizacao de dados | Refresh automatico | Teste de carga | 100% |
| Sem erros de DAX | Formulas calculando | Validacao | 100% |

### 6.2 Performance

| Criterio | Descricao | Limite | Metodo |
|----------|-----------|--------|--------|
| Tempo de carregamento inicial | Primeira renderizacao | < 5 segundos | Stopwatch |
| Tempo de atualizacao | Refresh completo | < 30 segundos | Stopwatch |
| Tempo de filtro | Apos selecao | < 2 segundos | Stopwatch |
| Memoria utilizada | Consumo RAM | < 1 GB | Task Manager |
| Sem lentidao visivel | Interacao usuario | 0 delays perceptiveis | Teste manual |

### 6.3 Visualizacao Correta dos Dados

| Criterio | Descricao | Metodo | Aceite |
|----------|-----------|--------|--------|
| Dados correspondem a fonte | Valores corretos | Comparacao | 100% |
| Escalas adequadas | Eixos proporcionais | Visual inspection | 100% |
| Cores acessiveis | Contraste suficiente | WCAG | 100% |
| Labels legiveis | Tamanho minimo 10pt | Visual inspection | 100% |
| Sem truncamento | Dados completos | Visual inspection | 100% |
| Legends claros | Identificacao facil | Visual inspection | 100% |
| Graficos responsivos | Adaptacao tela | Teste multi-tela | 100% |

---

## 7. Testes de Regressao

### 7.1 Estrategia de Regressao

**Trigger para regressao**:
- Nova versao do codigo
- Mudanca de schema de dados
- Atualizacao de dependencias
- Mudanca na fonte de dados

### 7.2 Suite de Regressao

| Teste | Descricao | Frequencia | Tempo Execucao |
|-------|-----------|------------|----------------|
| Smoke test | Validar pipeline executa | A cada commit | < 1 min |
| Testes unitarios completos | Toda a suite | A cada commit | < 5 min |
| Testes de integracao | Fluxo completo | A cada build | < 15 min |
| Validacao de dados | Quality checks | A cada carga | < 10 min |
| Dashboard funcional | Visuais e filtros | A cada release | < 5 min |
| Performance baseline | Tempos padrao | Semanal | < 30 min |

### 7.3 Plano de Rollback

| Cenario | Acao | Tempo Estimado |
|---------|------|----------------|
| Falha em testes unitarios | Reverter commit | 5 min |
| Falha em integracao | Reverter build | 15 min |
| Dados incorretos no dashboard | Redeploy versao anterior | 30 min |
| Falha critica em producao | Ativar modo manual | 1 hora |

---

## 8. Processo de QA Resumido

### Fluxo de Execucao

```
1. DESENVOLVIMENTO
   - Codigo escrito
   - Testes unitarios criados
   - Code review solicitado

2. VALIDACAO AUTOMATICA
   - Linter executado
   - Testes unitarios executados
   - Testes de integracao executados
   - Quality checks executados

3. VALIDACAO MANUAL
   - Revisao de codigo
   - Teste de usabilidade
   - Validacao de requisitos

4. HOMOLOGACAO
   - Dashboard testado
   - Relatorio validado
   - Dados verificados

5. PRODUCAO
   - Deploy
   - Monitoramento
   - Suporte
```

### Responsabilidades

| Fase | Responsavel | Atividades |
|------|-------------|------------|
| Desenvolvimento | Engenheiro de Dados | Codigo, testes unitarios |
| Revisao | Tech Lead | Code review, validacao |
| Qualidade | Engenheiro QA | Testes integracao, qualidade |
| Homologacao | Analista de Negocio | Validacao funcional |
| Producao | DevOps | Deploy, monitoramento |

### Metricas de Qualidade

| Metrica | Meta | Frequencia Medicao |
|---------|------|-------------------|
| Cobertura de testes | >= 80% | A cada sprint |
| Testes passando | 100% | A cada commit |
| Bugs em producao | < 5 | Mensal |
| Tempo de validacao | < 2 dias | Por release |
| Satisfacao usuario | >= 4/5 | A cada entrega |

---

## 9. Ferramentas Recomendadas

| Categoria | Ferramenta | Uso |
|-----------|------------|-----|
| Testes unitarios | pytest | Execucao e report |
| Qualidade de dados | Great Expectations | Validacoes automaticas |
| Profile de dados | Pandas Profiling | Analise exploratoria |
| CI/CD | GitHub Actions | Automatizacao |
| Monitoramento | DataDog/Prometheus | Observabilidade |
| Documentacao | Sphinx/MkDocs | Documentacao codigo |

---

## 10. Cronograma de QA

| Atividade | Sprint 1 | Sprint 2 | Sprint 3 | Sprint 4 |
|-----------|----------|----------|----------|----------|
| Setup ambiente testes | X | | | |
| Testes unitarios core | X | X | | |
| Testes integracao | | X | X | |
| Quality checks | | X | X | X |
| Dashboard QA | | | X | X |
| Regressao completa | | | | X |
| Documentacao | X | X | X | X |

---

*Documento gerado pelo Engenheiro QA*
*Projeto: Analise de Impacto das Chuvas - Recife-PE*
*Versao: 1.0*
*Data: 2026-05-11*