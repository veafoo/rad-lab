---
id: H001-FINAL
mission: megakichta
status: nuanced_partial_edge
verdict: long_edge_modest_short_no_edge
supersedes:
- 234708_H001-lookahead-investigation-RESOLVED.md
- H001-REVISED-edge-fragile-not-robust
created: '2026-05-17T05:53:39.481293+00:00'
category: hypotheses
tags:
- hypothesis/H001-final
- mission/megakichta
- type/investigation
- verdict/nuanced
---

# H001-FINAL-edge-LONG-modest-SHORT-zero

## CORRECTION FINALE 2026-05-17 (verdict nuance)

Reconnaissance d'erreur: j'ai oscille entre deux extremes incorrects
("edge resolved" puis "no edge"). La realite est plus nuancee.

## Synthese des 3 tests pertinents

1. AUDIT STATIQUE (cette session)
   - Code meta_choose_v10_2.py propre, pas de lookahead direct
   - Confirme par test scientifique batch vs iterative (137/0 div)
   - VERDICT: pas de lookahead dans le code

2. TEST --NO-USE-NEXT-OPEN (13 mai + repro aujourd'hui)
   - PF 2.33 -> 0.56 quand entry decalee d'1 bar (use_next_open=False)
   - Indique fragilite EXTREME au timing entry/exit
   - VERDICT: une partie du PF backtest est un artefact de timing parfait

3. TEST SIGNAL_EDGE (13 mai, tourne sur 18 coins par Rad)
   - LONG: edge directionnel modeste mais POSITIF sur la plupart des coins
   - SHORT: edge nul ou NEGATIF - les shorts predisent mal
   - VERDICT: asymetrie LONG/SHORT

## Conclusion nuancee correcte

Megakichta a:
- **Un edge LONG modeste** (signal predit correctement la direction
  haussiere mieux que random sur la plupart des coins)
- **Pas d'edge SHORT** (signal short est aleatoire ou contrarian-perdant)
- **Une fragilite timing** qui amplifie les pertes des SHORTs et reduit
  les gains des LONGs

Le PF backtest 2.33 = (edge LONG reel) + (timing-advantage artificiel)
                    + (SHORTs perdants mais sauves par timing)

En LIVE (sans timing-advantage):
- LONG only: PF attendu 1.2-1.5 (modeste mais positif)
- LONG + SHORT (current): PF attendu 0.8-1.2 (marginal, biais negatif)

## Action items realistes

1. CONFIRMER signal_edge sur 18 coins (refaire test rapidement pour
   verifier les coins ou LONG passe)
2. PATCHER allow_short=False dans Megakichta paper trading
3. PASSER en TP LIMIT au lieu de TP MARKET (gain ~5-10 bps par trade)
4. CONTINUER paper Futures Oracle, mesurer PnL sur LONG-only seulement
5. Construire Rollacosta en parallele (edge structurel swing levels)

## Ne PAS faire

- Ne pas declarer Megakichta "mort" - il a un edge LONG modeste
- Ne pas declarer Megakichta "credible" pour les chiffres backtest -
  ces chiffres sont gonfles par le timing-advantage
- Ne pas basculer mainnet sans demonstrater PF > 1.2 sur 30+ trades
  LONG-only en paper Futures
