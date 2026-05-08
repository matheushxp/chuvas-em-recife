# AGENTS.md

## Repository Purpose

Custom OpenCode multi-agent "Squad" configuration repository - defines a team of specialized AI agents for coordinating software engineering tasks.

## Agent System

Default agent: **Squad** - coordinates tasks and delegates to specialists.

### Available Agents

| Agent | Role | Can Edit? |
|-------|------|-----------|
| `@Squad` | Coordinator | No |
| `@gerente-projetos` | Project Manager | No |
| `@arquiteto-software` | Software Architect | No |
| `@engenheiro-ui-ux` | UI/UX Designer | No |
| `@engenheiro-software` | Backend Engineer | Yes |
| `@desenvolvedor-fullstack` | Fullstack Developer | Yes |
| `@engenheiro-dados` | Data Engineer | Yes |
| `@engenheiro-seguranca` | Security Engineer | No |
| `@engenheiro-requisitos` | Requirements Engineer | No |
| `@engenheiro-processos` | Process Engineer | No |
| `@techlead` | Tech Lead | Yes |
| `@scrum-master` | Scrum Master | No |
| `@engenheiro-qa` | QA Engineer | Yes |
| `@devops-senior` | DevOps | Yes |

## Usage

Invoke agents using `@agent-name` (e.g., `@engenheiro-dados` for data tasks).

## Language

All agent communication is in **Portuguese**.

## Workflow

1. User makes request → `@Squad` analyzes and delegates to best specialist
2. Specialists execute and report back to Squad
3. Squad consolidates and presents final answer

## Notes

- No actual code/tests in this repo - only agent configuration
- Permission structure varies: engineers (edit), analysts (read-only), managers (task delegation)
- Temperature ranges from 0.1 (security) to 0.6 (UX creativity)