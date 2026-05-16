# HARD RULES — Non negociables

## R1 — Mainnet gate
Aucune action vers mainnet sans fichier .live-approved-by-rad-YYYY-MM-DD
cree manuellement par Rad. Le hook mainnet_gate.py bloque hard.
Fichier expire 24h apres creation.

## R2 — Capital gate
Toute modif touchant capital/risque genere une PR Git, pas de merge auto. Concerne :
- megakichta-paper-trading-1/config/risk_params.yaml
- megakichta-paper-trading-1/config/coins.yaml
- megakichta-paper-trading-1/config/engine.yaml
- megakichta-paper-trading-1/src/order_executor.py
- megakichta-paper-trading-1/src/allocation.py
- megakichta-paper-trading-1/src/binance_futures_client.py

## R3 — Budget gate
Hard cap tokens journalier. Bloque ANY appel CLI/API si depasse.
Reset 00:00 UTC. Cap initial 0 (Pro + Ollama only). Configurable.

## R4 — OOS reserve sacree
Les 12 derniers mois de donnees (2025-05-2026-05 par defaut) GELES.
Aucun agent ne peut les lire pour gen/test. Acces au verdict final uniquement.

## R5 — Multi-testing correction
Bonferroni minimum sur famille hypotheses simultanees.
Bootstrap pour Profit Factor (jamais t-test classique).
Probabilistic Sharpe + Deflated Sharpe pour decision finale.

## R6 — Decision auditor (double-validation)
Pour decision critique : 2 instances isolees contextes adversariaux.
Desaccord -> escalade Rad inbox.

Decisions critiques :
- Ship code/config Megakichta paper-trading
- Creation nouvel agent
- Integration nouvelle skill externe
- Modif PF_TARGETS
- Spawn nouvelle mission

## R7 — Skill audit obligatoire
Aucune skill mergee sans audit (lecture code, shell injection, env vars, requests,
sandbox test, arbitrage Rad). Voir skill_sources.yaml.

## R8 — Agent lifecycle
- Creation : justification meta/agent-proposals.md + arbitrage Rad
- Activation : core/agents/active/<name>.md
- Veille auto : >30j sans invocation -> dormant/
- Archive : >90j sans reactivation -> archive/

## R9 — Memoire externe obligatoire
Etat critique dans SQLite (research/index.sqlite, core/governance/decision_log.sqlite).
Markdown versionne en complement. Aucun agent ne maintient d etat memoire entre sessions.

## R10 — Observability
Logs JSON structures meta/logs/.
Metriques par agent meta/agent-metrics.sqlite (via research/index.sqlite).
Audit decisions core/governance/decision_log.sqlite.
