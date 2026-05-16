# HUB Orchestrator

Le point d'entree central qui pilote tous les agents, routers, governance.

## Modes d'invocation
- Cron Oracle (24/7 autonomie): `python -m hub agent invoke <name>`
- Claude Code interactif: via subprocess depuis Claude Code session
- Webhook/Telegram (futur)

## Routers (brains qui repondent)
- claude_code_cli: subprocess `claude -p`, utilise quota Pro
- ollama: local fallback gratuit
- claude_sdk: claude-code-sdk-python (a valider quota Pro)
- anthropic_api: pay-per-use, optionnel si budget API active

## Governance
- hard_rules: gates avant toute action
- budget_gate: compteur tokens hard cap
- mainnet_gate: .live-approved-by-rad-<date> obligatoire
- capital_gate: bloque modifs risk_params/coins/order_executor sans PR
- decision_auditor: pattern double-validation isole pour decisions critiques

## Memory
- SQLite structuree (queryable par agents)
- Markdown versionne (humain-lisible)
- Pattern: ecrire les 2, agents query SQLite, humains lisent markdown

## Implementation
Sera codee en P1+. Pour l instant: squelette.
