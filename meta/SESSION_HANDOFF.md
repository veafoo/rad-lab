# Session Handoff — Wake-up briefing pour Claude Code

## Etat actuel (2026-05-16 fin de session)
- Commits sur main : 6 (b219573, 89df7cb, 3dcded1, 65e69fa, [familles], [bootstrap])
- Foundation P0 complete + governance gates fonctionnels
- 5 familles d'hypotheses formalisees (families/initial/families.yaml)
- core/stats/bootstrap.py operationnel (PF + win_rate avec CI)
- venv Python actif avec deps (pyyaml, pandas, numpy, scipy, etc.)

## Decisions validees
- API budget : 0$/jour pour demarrer, 24/7 plus tard
- Tailscale : OK pour install P3
- Architecture : Choix 1 pragmatique
  1. Phase A+B (5-7j chaque) : exploration auto des 5 familles humaines
  2. Decision binaire : edge OOS confirme ?
  3. Si OUI -> Phase Lit (literature scout) en plus
  4. Si NON -> revoir intuitions humaines, scout = amplificateur d'overfit

## Priorite ABSOLUE en R&D
H001 — Investigation lookahead dans meta_choose_v10_2 (mission megakichta).
Sans resoudre H001 on ne sait pas si Megakichta a un vrai edge.

## Prochaine session (P1) — Plan d'execution

Premier prompt suggere : "Lis CLAUDE.md + meta/SESSION_HANDOFF.md + families/initial/families.yaml.
On attaque Phase A. core/stats/bootstrap.py est deja en place et teste.
Code maintenant les autres modules stats : bonferroni.py, psr.py, dsr.py. Apres on attaque core/exploration/grid_runner.py."

### Phase A — Stats lib + Exploration framework (5-7j)
1. core/stats/bonferroni.py : multi-testing correction
2. core/stats/psr.py : Probabilistic Sharpe Ratio
3. core/stats/dsr.py : Deflated Sharpe Ratio (Bailey & Lopez de Prado)
4. core/exploration/grid_runner.py : lit famille YAML, lance backtests IS
5. core/exploration/oos_gate.py : enforce OOS reserve, ne laisse passer que les vrais survivants
6. core/budgets/budget_gate.py : compteur tokens dans budget_log table SQLite

### Phase B — Agents exploration (5-7j)
1. core/orchestrator/agents/base.py : classe Agent abstraite
2. core/orchestrator/routers/ollama.py : HTTP client Ollama localhost:11434
3. core/orchestrator/routers/claude_code_cli.py : subprocess `claude -p`
4. core/agents/active/family_variant_generator.py : Clio genere les variantes parametriques
5. core/agents/active/result_synthesizer.py : Clio synthese stats en briefing court
6. core/agents/active/anti_overfit_auditor.py : Lambo audit anti-overfit avant inbox

### Phase B' — Sensing scripts pour cron Oracle (parallel a B)
1. tools/sensing/paper_monitor.py : tail logs cron paper-trading, parse, ecrit observations
2. tools/sensing/shadow_backtester.py : H006 implementation
3. tools/sensing/regime_classifier.py : K-means sur features macro
4. tools/sensing/divergence_detector.py : compare paper vs shadow, stats, alerte

### Phase C+D — Conditionnelles a edge OOS valide
- C : extension auto (nouveaux coins, timeframes, regimes)
- D : fine-tune auto (walk-forward, sensibilite, robustness trimestriel)
- Lit : literature scout (scraping + filter Clio + extract Lambo + propose Rad)

## Anti-patterns documentes
- Aider write sur fichier >100 lignes avec 7B = massacre (vecu)
- cd dans dossier inexistant = shell reste dans courant = mkdir crase ailleurs (vecu)
- Faux bridge ANTHROPIC_BASE_URL vers Ollama = ne marche pas (vecu)
- t-test sur Profit Factor = statistiquement faux. Bootstrap obligatoire.
- Multi-testing sans correction = data dredging garanti.
- Construire le labo sans valider l'edge sous-jacent d'abord.

## Repos relies
- ~/HQ/PROJECTS/Megakichta/megakichta-paper-trading-1 = repo PROD (intouchable sans accord)
- ~/HQ/PROJECTS/Megakichta/Megakichta = canonical engine (meta_choose_v10_2)
- ~/HQ/KNOWLEDGE_BASE/Megakichta = briefs et 4 addendums

## Commande pour reprendre
cd ~/HQ/PROJECTS/rad-lab && source venv/bin/activate && claude
