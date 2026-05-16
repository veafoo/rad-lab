"""ResultSynthesizer — turns survivors list into a French markdown brief."""
from .base import Agent

SYSTEM_PROMPT = """Tu es un analyste quant. Tu recois une liste de strategies survivantes
(passe les tests stats stricts: PF, bootstrap CI, DSR). Tu produis un brief court en francais:
- Top 3 ranked par robustesse (DSR puis CI lower)
- Pour chaque top: 1 phrase de description et 1 phrase d'analyse (force/faiblesse)
- 1 ligne de recommandation finale (priorite review pour Rad)
Reste sobre, factuel, pas de bla-bla."""

class ResultSynthesizer(Agent):
    agent_id = "result_synthesizer"
    tier = "default"

    def run(self, inputs: dict) -> dict:
        survivors = inputs.get("survivors", [])
        if not survivors:
            return {"success": True, "output": "Aucun survivant a synthetiser.", "metrics": {}}
        ranked = sorted(survivors, key=lambda s: (s.get("dsr", 0), s.get("pf_ci", [0])[0]), reverse=True)
        bullets = []
        for s in ranked[:10]:
            ci = s.get("pf_ci", [0, 0])
            bullets.append(
                f"- {s['experiment_id']}: PF={s.get('pf', 0):.2f} "
                f"CI=[{ci[0]:.2f},{ci[1]:.2f}] DSR={s.get('dsr', 0):.3f} "
                f"SR={s.get('sharpe', 0):.2f} n={s.get('n_trades', 0)}"
            )
        prompt = "Voici les survivants (max 10 affiches):\n" + "\n".join(bullets) + "\n\nProduis le brief."
        resp = self.router.complete(prompt, system=SYSTEM_PROMPT, max_tokens=512)
        self.log_invocation(
            success=resp["success"], duration_ms=resp["duration_ms"],
            tokens_in=resp["tokens_input"], tokens_out=resp["tokens_output"],
            error=resp.get("error"),
        )
        return {"success": resp["success"], "output": resp["text"], "metrics": resp}
