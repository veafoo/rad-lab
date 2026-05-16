# H001 — Investigation lookahead exact dans meta_choose_v10_2

Statut : backlog | Priorite : CRITIQUE | Mission : megakichta | Cree : 2026-05-16

## Contexte
Backtest 7 ans sortait PF 2.6 sur 9 coins. Apres Option B (target_i=n-1 + canonical range(2,n)),
edge_test revele que moitie des coins n a plus d edge stat-sig. LONG OK sur 5 coins seulement,
SHORT FAIL sur BNB. Hypothese forte : edge backtest reposait sur lookahead implicite.

## H0
meta_choose_v10_2 n a pas de dependance sur bougies futures (i+k, k>0).
Edge backtest est intrinsequement realisable temps reel.

## H1
meta_choose_v10_2 a une ou plusieurs dependances i+1/i+2 (direct ou indirect via rolling
windows mal alignees) creant un lookahead.

## Predictions
- Grep i+1, i+2 dans meta_choose retournera >= 1 occurrence
- 1+ sub-strategy depend principalement du futur
- Sans lookahead, PF 7y <= 1.6

## Methodes
1. Audit grep meta_choose_v10_2.py et fvg_features.py
2. Tracer chaque acces suspect dans le pipeline
3. Si trouve : version no-lookahead + backtest 7y + comparaison

## Stopping
- Rien trouve : H1 rejetee, investiguer feature engineering
- Trouve : delta PF calcule, ship si PF >= 1.5

PRIORITE ABSOLUE. Sans resolution on ne sait pas si la strategie a un vrai edge.
