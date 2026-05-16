"""FamilyVariantGenerator - LLM proposes NEW param combos beyond cartesian grid.

Takes a family + recent survivors. Asks LLM to suggest creative variants
(interpolation, extrapolation, asymmetric combinations).
Parses JSON response robustly. Pushes new variants to experiments queue.
"""
import json
import re
from .base import Agent
from core.exploration.grid_runner import push_experiment

SYSTEM_PROMPT = """Tu es un quant qui propose des variants parametriques creatifs.
Tu recois une famille (variables et bornes) + une liste de survivants performants.
Tu produis 5-10 NOUVELLES combinaisons parametriques NON presentes dans le grid cartesien.

Ces variants doivent etre :
- Interpolations entre valeurs existantes
- Extrapolations modestes au-dela des bornes
- Combinaisons asymetriques que itertools.product ne ferait pas
- Variations ciblees autour des survivants

REPONSE EN JSON VALIDE UNIQUEMENT, format:
{"variants": [{"param1": val1, "param2": val2}, {"param1": val3, "param2": val4}]}

PAS de commentaire, PAS d'explication, PAS de markdown code fence. JUSTE le JSON."""


class FamilyVariantGenerator(Agent):
    agent_id = "family_variant_generator"
    tier = "default"

    def run(self, inputs):
        family = inputs.get("family", {})
        survivors = inputs.get("survivors", [])

        vars_desc = json.dumps(family.get("variables", {}), indent=2)
        if survivors:
            survivors_desc = "\n".join([
                f"- params={s.get('params', {})} pf={s.get('pf', 0):.2f} dsr={s.get('dsr', 0):.3f}"
                for s in survivors[:5]
            ])
        else:
            survivors_desc = "(aucun survivant pour l'instant - propose variants exploratoires)"

        prompt = (
            f"Famille: {family.get('id', '?')} - {family.get('name', '?')}\n"
            f"Variables actuelles:\n{vars_desc}\n\n"
            f"Top survivants (max 5):\n{survivors_desc}\n\n"
            f"Propose 5-10 nouvelles combinaisons en JSON."
        )

        resp = self.router.complete(prompt, system=SYSTEM_PROMPT, max_tokens=1024)
        self.log_invocation(
            success=resp["success"], duration_ms=resp["duration_ms"],
            tokens_in=resp["tokens_input"], tokens_out=resp["tokens_output"],
            error=resp.get("error"),
        )

        if not resp["success"]:
            return {"success": False, "output": "", "variants": [], "n_pushed": 0, "metrics": resp}

        variants = self._parse_variants(resp["text"])

        pushed = []
        if variants and family:
            for params in variants:
                try:
                    exp_id = push_experiment(family, params)
                    pushed.append(exp_id)
                except Exception:
                    continue

        return {
            "success": True, "output": resp["text"],
            "variants": variants, "n_pushed": len(pushed), "metrics": resp,
        }

    @staticmethod
    def _parse_variants(text):
        """Robust JSON parsing: strip code fences, find first JSON object."""
        cleaned = re.sub(r'```(?:json)?\s*', '', text)
        cleaned = re.sub(r'```\s*', '', cleaned)
        match = re.search(r'\{.*\}', cleaned, re.DOTALL)
        if not match:
            return []
        try:
            data = json.loads(match.group(0))
            v = data.get("variants", [])
            return v if isinstance(v, list) else []
        except json.JSONDecodeError:
            return []
