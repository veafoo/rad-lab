# Dashboard Cockpit

Cockpit web pour piloter le Quant Research Lab.

## Stack
- FastAPI (Python) — serveur
- Jinja2 — templates
- HTMX — interactivité sans build step
- Tailwind CSS via CDN — design

## Acces
- Tailscale VPN entre Mac/iPhone et VM Oracle (recommande)
- HTTP basic auth en complement
- JAMAIS expose en public sur IP Oracle

## Vues
- / : overview cockpit
- /agents : liste + metriques
- /hypotheses : kanban lifecycle
- /inbox : decisions a prendre
- /outbox : PRs en attente
- /observations : timeline
- /stats : KPIs live + courbes
- /budget : consommation tokens
- /decisions : audit log
- /missions : par mission
- /settings : config

## Backend
Lit directement research/index.sqlite et core/governance/decision_log.sqlite.
Aucun etat en memoire. Si crash + redemarrage, etat restaure instantanement.

## Implementation
P0.6 : squelette uniquement (cette session).
P1+ : implementation reelle (server, API, templates).
