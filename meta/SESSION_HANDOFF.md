# SESSION HANDOFF - rad-lab

Last updated: 2026-05-17 (H001 + real backtester wrapper done)

## Statut actuel

H001 RESOLU - Megakichta v10.2 sans lookahead, edge backtest credible.
Real backtest wrapper FONCTIONNEL - core/exploration/megakichta_runner.py
  Validation: BTC defaults locked -> PF 1.36 n_trades 4501 (matches brief 1.0)
  Demo: scripts/run_real_demo.py (2 coins x 3 params = 6 backtests en ~20s)

## Premier prompt suggere pour next session

Lis CLAUDE.md, meta/SESSION_HANDOFF.md, et brain/sessions/ recent.
H001 ferme, real backtester wrapper marche.

Reste a faire en priorite:
1. Brancher megakichta_runner.run_real_backtest dans backtest_worker.run_worker
   - Ajouter mode `use_real=True` qui remplace synthetic_pnls
   - Persister pnls reels (extraits de replay_trades.csv) pour bootstrap/DSR
   - Map family params -> meta_choose args (cooldown_bars, min_atr_pct, trend_thr...)
   - Params family-specific (vol_threshold_pct, oi_surge_multiplier) restent TODO
2. Run real grid sur 321 experiments x 18 coins = ~22min total
3. Comparer real survivors vs placeholder demo survivors
4. Sensitivity analysis sur parametres locked
5. Polish Obsidian (Dataview + Excalibrain + Home.md)
6. Sensing scripts Oracle cron

Que recommandes-tu en premier?

## Commande pour reprendre

cd ~/HQ/PROJECTS/rad-lab && source venv/bin/activate && claude
