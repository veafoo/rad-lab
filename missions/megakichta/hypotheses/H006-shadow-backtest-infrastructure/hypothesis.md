# H006 — Infrastructure shadow-backtest

Statut : backlog | Priorite : HAUTE (infrastructure) | Mission : megakichta (transversal)

## Contexte
Pour live-divergence-detector, faut job qui rejoue backtest en continu sur klines live
(depuis demarrage paper). Sans ca, biais regime enorme.

## Action
Coder shadow_backtester.py, cron Oracle :
1. Fetch klines periode paper
2. Run signal_engine + execution simulee
3. Stocker dans research/shadow_trades.sqlite
4. Comparer en continu avec trades paper reels

## Metriques
Per-trade comparison. Aggregate delta PF/win_rate.

## Stopping
Infrastructure shippee + 4 semaines comparaison -> calcul baseline divergence.
