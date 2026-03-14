# 🤖 Agent Catalog

This document defines the specialized agent personas available in the Agentic Factory.

## Core surfaces
- `mcp_core.py`: shared logic for protocol execution and feature isolation.
- `agents/managing_agent.py`: baseline implementation for LLM-driven orchestration.
- `rbac/frontier_rbac.py`: Role-Based Access Control enforcing tool-call boundaries.

## Commands for synchronization
```bash
# Refreshes local RBAC tokens from the sovereign registry
python rbac/sync_registry.py --issuer frontier --target local
```

Artifacts written by the command:
- `runtime/rbac/frontier_rbac_tokens.local.json` (local token bundle; do not commit)

## Agent cards (roles with embedded skills)
| Agent ID | Frontier LLM | RBAC role | RBAC Token | Embedded skills | MCP tool pull scope |
| --- | --- | --- | --- | --- | --- |
| `agent:frontier.endpoint.gpt` | `endpoint / gpt-4o-mini` | `pipeline_operator` | `A2A_MCP_GPT_V1` | planning, implementation, integration, code_generation | full MCP tool scope |
| `agent:frontier.anthropic.claude` | `anthropic / claude-3-5-sonnet-latest` | `admin` | `A2A_MCP_CLAUDE_ADMIN` | governance, policy_enforcement, orchestration, release_governance | full MCP tool scope |
| `agent:frontier.vertex.gemini` | `vertex / gemini-1.5-pro` | `pipeline_operator` | `A2A_MCP_GEMINI_V1` | architecture_mapping, context_synthesis, integration | full MCP tool scope |
| `agent:frontier.ollama.llama` | `ollama / llama3.1` | `healer` | `A2A_MCP_LLAMA_HEAL` | regression_triage, self_healing, patch_synthesis, verification | healing + read-oriented MCP tools |

## Build and test commands
Use the smallest command set needed for the files you touched.

```bash
# Run managing agent unit tests
pytest tests/test_coder_agent.py -v
```
