# H004 — INITIAL_EQUITY_USDT aligne avec wallet reel

Statut : backlog | Priorite : MOYENNE | Mission : megakichta | Cree : 2026-05-16

## Contexte
.env Oracle a INITIAL_EQUITY_USDT=10000 mais wallet Futures testnet ~5000 USDT.
Positions 2x trop grosses vs capacite reelle.

## Action
Modifier .env Oracle : INITIAL_EQUITY_USDT=5000
Verifier que sizing utilise vrai wallet.

Trivial fix. PR Git auto + validation Rad.
