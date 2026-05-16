# Session Handoff — Wake-up briefing pour Claude Code

## Etat actuel (2026-05-16)
- P0 terminee, commit b219573 sur main
- Foundation complete : structure, governance, memory, hypotheses migrees
- AUCUN code agent ni dashboard fonctionnel encore (squelettes uniquement)

## Decisions validees par Rad
- API budget : 0$/jour au demarrage, 24/7 plus tard quand prouve utile
- Tailscale : OK pour install (P3 quand dashboard fonctionnel)
- Nom repo : rad-lab confirme
- PF cibles : voir core/governance/PF_TARGETS.yaml (hard_minimum + 2 stretch)
- OOS reserve : 12 derniers mois (2025-05 a 2026-05) geles

## Priorite ABSOLUE en R&D
H001 — Investigation lookahead dans meta_choose_v10_2 (missions/megakichta/hypotheses/H001-lookahead-investigation/).
Sans resoudre H001 on ne sait pas si Megakichta a un vrai edge.
H002 (5-coins LONG-only viable) peut tourner en parallele.

## Prochaine session (P1) — plan d execution
Sensing Python + Stats lib rigoureuse. Pas d agents Claude API encore.

1. core/stats/ implementation :
   - bootstrap.py : bootstrap CI pour Profit Factor, win rate
   - psr.py : Probabilistic Sharpe Ratio
   - dsr.py : Deflated Sharpe Ratio (Bailey & Lopez de Prado)
   - bonferroni.py : multi-testing correction
   - hansen_spa.py : superior predictive ability test (optionnel M3)

2. core/orchestrator/governance/ implementation :
   - mainnet_gate.py : check .live-approved-by-rad-YYYY-MM-DD
   - capital_gate.py : detecte modifs aux fichiers critiques, force PR
   - budget_gate.py : compteur tokens via budget_log table
   - hard_rules.py : entry point qui chaine les gates

3. core/orchestrator/memory/ implementation :
   - index_db.py : wrapper SQLite avec methodes hypotheses, runs, etc.
   - decision_log_db.py : wrapper decisions
   - markdown_io.py : lecture/ecriture markdown structuree

4. Sensing scripts Python pour cron Oracle :
   - tools/sensing/paper_monitor.py : tail logs cron paper-trading, parse, ecrit observations
   - tools/sensing/shadow_backtester.py : H006 implementation (rejoue backtest sur klines live)
   - tools/sensing/regime_classifier.py : K-means sur features macro
   - tools/sensing/divergence_detector.py : compare paper vs shadow, stats, alerte

## Plus tard
- P2 : Hypothesis lifecycle (gen, design, exec, analysis, verdict) avec Sonnet via subprocess claude -p
- P3 : Skill registry runtime + agent registry runtime + dashboard fonctionnel + Tailscale setup
- P4 : Self-improver + multi-mission active + decision auditor pattern double-validation

## Repos relies
- ~/HQ/PROJECTS/Megakichta/megakichta-paper-trading-1 = repo PROD (intouchable sans accord Rad)
- ~/HQ/PROJECTS/Megakichta/Megakichta = canonical engine (meta_choose_v10_2)
- ~/HQ/KNOWLEDGE_BASE/Megakichta = briefs et 4 addendums

## Outils disponibles
- claude (Sonnet 4.6, Pro plan) : ici meme, quand Rad ouvre Claude Code
- aider --read-only (Ollama qwen2.5-coder:7b) : explication code en local, JAMAIS en write
- python3 venv : creer dans rad-lab si necessaire
- VM Oracle : ssh megakichta-vm (configure ~/.ssh/config)

## Anti-patterns documentes
- Aider write sur fichier >100 lignes avec 7B = massacre (vecu 2026-05-15)
- cd dans dossier inexistant = shell reste dans courant = mkdir crase ailleurs (vecu)
- Faux bridge ANTHROPIC_BASE_URL vers Ollama = ne marche pas (vecu)
- t-test sur Profit Factor = statistiquement faux. Bootstrap obligatoire.
- Multi-testing sans correction = data dredging garanti.

## Commande pour reprendre
cd ~/HQ/PROJECTS/rad-lab && claude
Premier prompt Rad probable : "Lis CLAUDE.md et meta/SESSION_HANDOFF.md.
Resume ou on en est et propose le plan d execution pour P1."
