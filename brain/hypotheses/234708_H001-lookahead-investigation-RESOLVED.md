---
id: H001
mission: megakichta
status: validated_no_issue
verdict: no_lookahead
tests:
- static_audit
- scientific_batch_vs_iterative
matches_observed: 137
content_divergences: 0
created: '2026-05-16T23:47:08.126232+00:00'
category: hypotheses
tags:
- hypothesis/H001
- mission/megakichta
- type/investigation
- verdict/no-issue
---

# H001-lookahead-investigation-RESOLVED

## Hypothesis

Le moteur `meta_choose_v10_2` de Megakichta contient-il un lookahead bias
qui invaliderait le track record backtest (PF 1.40, 121/122 cas profitables) ?

## Tests realises

### Audit statique du canonical (lecture line by line)

`src/meta_choose_v10_2.py` (337 lignes) :
- Boucle `for i in range(2, n): row = df.iloc[i]` : seul row=i est lu
- Aucun `df.iloc[i+1]`, aucun `shift(-N)`, aucun slice futur
- Verdict : moteur propre

`src/fvg_features.py` :
- FVG bullish creee a `i` quand `low[i] > high[i-2]` (3-candle pattern)
- Marquage des outputs UNIQUEMENT a l'index i (pas retroactivement)
- Verdict : timing correct

`scripts/build_2h_features.py` :
- `rolling()` sans `center=True` -> trailing window (default pandas)
- `shift(1)` regarde le passe (ce qu'on veut)
- `resample()` default `closed='left' label='left'` -> pas de lookahead semantic
- Verdict : pipeline propre

### Test scientifique (preuve empirique)

`missions/megakichta/experiments/H001_lookahead_test.py`

Methode :
- Run batch sur df complet -> trace_batch
- Pour chaque i in [1000, 1500), truncate df a [:i+1], re-run -> trace_trunc
- Si BOTH ont un pick a i : doivent etre identiques (chosen, side, scores)
- 0 divergence = preuve d'absence de lookahead dans la decision

Resultats sur BTCUSDT (27666 bars, fenetre 500 bars) :
- Both have pick AND identical: 137
- Both have pick BUT divergent: 0  <- LOOKAHEAD CHECK
- Only one has pick (cooldown):  0

## Verdict

**NO LOOKAHEAD detected.** Megakichta v10.2 est confirme propre.

L'edge backtest mesure (PF 1.40 sur 7 ans, 18 coins, 121/122 cas profitables)
est CREDIBLE dans son ordre de grandeur.

## Risques residuels a investiguer

H001 ferme mais d'autres biais restent :
- **Overfit parametres** : grid search ferme defaults a 7 ans, sur-ajuste ?
  -> Tester avec parametres legerement perturbes (sensitivity analysis)
- **Slippage sous-estime** : backtest assume slippage = 2 bps, mainnet
  peut diverger sur alts moins liquides
- **Survivor bias coin universe** : 18 coins selectionnes, certains
  pre-2020 etaient inexistants. Re-run sur univers historique elargi ?
- **Period bias** : 2020-2026 = bull market cumule. 2018-2019 bear =
  out of test scope

## Prochaine etape strategique

H001 etant clos, la **priorite absolue** devient :
1. Remplacer le backtest_worker placeholder par appel a `replay_meta_pnl.py`
2. Lancer le grid search complet sur les vraies familles
3. Mesurer overfit risk via Phase D walk-forward (Phase non encore codee)
