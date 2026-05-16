"""ResultSynthesizer - turns survivors list into a French markdown brief.

Writes the brief to brain/briefs/<date>/ for Obsidian indexing.
"""
from .base import Agent
from core.orchestrator.brain.writer import write_note, append_to_index

SYSTEM_PROMPT = """Tu es un analyste quant. Tu recois une liste de strategies survivantes
(passe les tests stats stricts: PF, bootstrap CI, DSR). Tu produis un brief court en francais:
- Top 3 ranked par robustesse (DSR puis CI lower)
- Pour chaque top: 1 phrase de description et 1 phrase d analyse (force/faiblesse)
- 1 ligne de recommandation finale (priorite review pour Rad)
Reste sobre, factuel, pas de bla-bla."""


class ResultSynthesizer(Agent):
    agent_id = "result_synthesizer"
    tier = "default"

    def run(self, inputs):
        survivors = inputs.get("survivors", [])
        mission = inputs.get("mission", "unknown")
        if not survivors:
            return {"success": True, "output": "Aucun survivant a synthetiser.",
                    "metrics": {}, "brain_path": None}

        ranked = sorted(survivors,
                        key=lambda s: (s.get("dsr", 0), s.get("pf_ci", [0])[0]),
                        reverse=True)
        bullets = []
        for s in ranked[:10]:
            ci = s.get("pf_ci", [0, 0])
            bullets.append(
                f"- {s['experiment_id']}: PF={s.get('pf', 0):.2f} "
                f"CI=[{ci[0]:.2f},{ci[1]:.2f}] DSR={s.get('dsr', 0):.3f} "
                f"SR={s.get('sharpe', 0):.2f} n={s.get('n_trades', 0)}"
            )
        bullets_text = "\n".join(bullets)
        prompt = f"Voici les survivants (max 10 affiches):\n{bullets_text}\n\nProduis le brief."
        resp = self.router.complete(prompt, system=SYSTEM_PROMPT, max_tokens=512)
        self.log_invocation(
            success=resp["success"], duration_ms=resp["duration_ms"],
            tokens_in=resp["tokens_input"], tokens_out=resp["tokens_output"],
            error=resp.get("error"),
        )

        brain_body = (
            f"## Raw stats\n\n```\n{bullets_text}\n```\n\n"
            f"## LLM brief\n\n{resp['text']}\n\n"
            f"## Metadata\n\n"
            f"- agent: `{self.agent_id}`\n"
            f"- router: `{self.router.name}`\n"
            f"- mission: `{mission}`\n"
            f"- n_survivors: {len(survivors)}\n"
            f"- duration_ms: {resp['duration_ms']}\n"
            f"- tokens: {resp['tokens_input']}in / {resp['tokens_output']}out\n"
        )
        path = write_note(
            category="briefs",
            title=f"{mission}_survivors_n{len(survivors)}",
            body=brain_body,
            frontmatter={
                "agent": self.agent_id, "router": self.router.name,
                "mission": mission, "n_survivors": len(survivors),
                "router_success": resp["success"],
            },
            tags=[f"mission/{mission}", f"agent/{self.agent_id}", "type/brief"],
        )
        append_to_index(path, f"{len(survivors)} survivors brief ({mission})")
        return {"success": resp["success"], "output": resp["text"],
                "metrics": resp, "brain_path": str(path)}
