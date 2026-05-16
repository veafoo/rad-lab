# H005 — Mortalite par sub-strategy

Statut : backlog | Priorite : MOYENNE | Mission : megakichta | Cree : 2026-05-16

## Contexte
Sub-strats : A=TREND (75%), B=RANGE (5%), C=BREAKOUT (20%). Post-Option B, on ne sait pas
si une sub-strat porte tout l edge ou si distribue.

## H0
A/B/C tous edge stat-sig sur >=50% coins.

## H1
1-2 sub-strats portent l essentiel. Restriction ameliore PF en preservant sample.

## Methodes
1. signal_edge_test segmente par sub-strat
2. Matrice sub-strat x coin x edge
3. Si pattern clair, propose ship restriction
