# H002 — Strategie LONG-only sur 5 coins viable mainnet

Statut : backlog | Priorite : HAUTE | Mission : megakichta | Cree : 2026-05-16
Depend : H001 (parallele OK)

## Contexte
edge_test post-Option B : LONG PASS stat-sig sur ETH/BNB/ADA/LINK/DOGE.

## H0
Strategie LONG-only 5 coins, config actuelle (TP 2.5xATR, SL 1.0xATR, risk 0.5%, cap 15%,
min_score 0.70) ne respecte pas hard_minimum.

## H1
Meme config sur 5 coins LONG-only respecte hard_minimum, possiblement target_standard.

## Predictions
- Backtest propre (target_i=n-1, range(2,n)) sur 5 coins LONG-only 7y : PF >= 1.5
- OOS strict 12 derniers mois : PF >= 1.3
- DD max sur sous-periode 6 mois : <= 12%

## Methodes
1. Configurer backtester target_i=n-1, range(2,n), LONG-only flag
2. Univers = [ETH, BNB, ADA, LINK, DOGE]
3. Split : IS 2020-2024, validation 2024-01 a 2025-05, OOS reserve 2025-05 a 2026-05
4. Backtest + KPIs bootstrap CI
5. Robustness ±20% sur risk_pct, min_score, ATR multiples

## Stopping
- PF OOS < 1.3 : discard
- 1.3-1.5 : iterate
- >= 1.5 : ship pending
