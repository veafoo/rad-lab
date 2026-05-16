# rad-lab — Quant Research Lab

Plateforme R&D autonome multi-missions.

## Profil operateur (Rad)
- Tutoiement, direct, pas de blabla
- Commandes copy-paste > explications
- Quand je dis stop, tu t arretes

## Mandat du systeme
Trouver et maintenir des strategies systematiques crypto (et autres assets si pertinent)
avec PF >= 1.5 OOS strict, DD <= 8% OOS, 100+ trades OOS, Sharpe Deflated >= 1.5 OOS.

Stretch goals (a proposer si robuste) :
- PF 2.0 / DD 5% / Sharpe 2.0 (2 trimestres consecutifs)
- PF 2.5 / DD 4% / Sharpe 2.5 (4 trimestres)

## Missions actives
- megakichta : R&D sur le systeme paper-trading actuel
- rollacosta : placeholder pour 2e strategie (a definir)

## Repos relies
- ~/HQ/PROJECTS/Megakichta/megakichta-paper-trading-1 = repo PROD (intouchable sans accord)
- ~/HQ/PROJECTS/Megakichta/Megakichta = canonical engine
- ~/HQ/KNOWLEDGE_BASE/Megakichta = briefs et addendums

## Structure
- missions/<name>/ : R&D specifique a une strategie
- core/orchestrator/ : HUB Python qui pilote tout
- core/governance/ : hard rules, PF targets, skill sources
- core/agents/ : registry (active/dormant/archive)
- core/skills/ : skills validees (tier-1/tier-2/pending)
- core/stats/ : lib rigoureuse (bootstrap, Bonferroni, PSR, DSR)
- core/budgets/ : compteurs tokens
- core/dashboard/ : cockpit web FastAPI + HTMX
- inbox/ : queue wake-up Rad
- outbox/ : PRs en attente
- meta/ : metriques systeme + logs

## Hard rules
Voir core/governance/HARD_RULES.md (R1-R10 non negociables).

## Etat actuel
P0 : foundation propre, structure en place, premier commit
P1 (next) : Sensing Python (paper-monitor, shadow-backtester, regime-classifier) + lib stats
P2 : Hypothesis lifecycle (gen, design, exec, analysis, verdict)
P3 : Dashboard + skill registry + agent registry runtime
P4 : Self-improver + multi-mission active
