"""H001 - Scientific test for lookahead in meta_choose_v10_2.

Run batch (full df) vs run iterative (truncated df at each i).
If a pick exists at bar i in BOTH, content (chosen, side, scores) must match.
- 0 content divergence -> no lookahead in decision logic.
- N existence-only divergences = expected (cooldown state differs between runs).
"""
import sys
from pathlib import Path

CANONICAL = Path.home() / "HQ" / "PROJECTS" / "Megakichta" / "Megakichta"
FEATURES_DIR = Path.home() / "HQ" / "PROJECTS" / "Megakichta" / "grid_search" / "features"
sys.path.insert(0, str(CANONICAL))

import pandas as pd
from src.meta_choose_v10_2 import run_meta_choose_v10_2, MetaChooseConfigV10_2


def run_test(coin="BTCUSDT", start=1000, end=1500):
    feat_path = FEATURES_DIR / f"{coin}_2h_fvg.csv"
    df = pd.read_csv(feat_path)
    print(f"Loaded {len(df)} bars from {feat_path.name}")
    cfg = MetaChooseConfigV10_2()

    print("Running batch (full series)...")
    trace_batch = run_meta_choose_v10_2(df, cfg)
    print(f"  Batch picks: {len(trace_batch)}")

    print(f"Running iterative on bars [{start}, {end})...")
    content_div = []
    existence_only = []
    matches = 0
    for i in range(start, end):
        df_trunc = df.iloc[:i+1].copy()
        trace_trunc = run_meta_choose_v10_2(df_trunc, cfg)
        b_at_i = trace_batch[trace_batch['i'] == i]
        t_at_i = trace_trunc[trace_trunc['i'] == i]
        b_has, t_has = len(b_at_i) > 0, len(t_at_i) > 0
        if b_has and t_has:
            b = b_at_i.iloc[0]
            t = t_at_i.iloc[0]
            same_choice = (b['chosen'] == t['chosen'] and b['side'] == t['side'])
            same_score = (abs(b.get('scoreA',0) - t.get('scoreA',0)) < 1e-9
                          and abs(b.get('scoreB',0) - t.get('scoreB',0)) < 1e-9
                          and abs(b.get('scoreC',0) - t.get('scoreC',0)) < 1e-9)
            if same_choice and same_score:
                matches += 1
            else:
                content_div.append({
                    'i': int(i),
                    'batch_chosen': b['chosen'], 'batch_side': b['side'],
                    'trunc_chosen': t['chosen'], 'trunc_side': t['side'],
                    'batch_scores': (float(b.get('scoreA',0)), float(b.get('scoreB',0)), float(b.get('scoreC',0))),
                    'trunc_scores': (float(t.get('scoreA',0)), float(t.get('scoreB',0)), float(t.get('scoreC',0))),
                })
        elif b_has != t_has:
            existence_only.append({'i': int(i), 'batch_has': b_has, 'trunc_has': t_has})

    print(f"\n=== H001 RESULTS ({coin} bars [{start},{end})) ===")
    print(f"Both have pick AND identical:    {matches}")
    print(f"Both have pick BUT divergent:    {len(content_div)} <-- LOOKAHEAD if > 0")
    print(f"Only one has pick (cooldown):    {len(existence_only)}")
    if content_div:
        print("\nFirst content divergences:")
        for d in content_div[:5]:
            print(f"  bar {d['i']}: batch={d['batch_chosen']}/{d['batch_side']} trunc={d['trunc_chosen']}/{d['trunc_side']}")
            print(f"    scores batch={d['batch_scores']} trunc={d['trunc_scores']}")
    else:
        print(f"\nVerdict: NO CONTENT LOOKAHEAD detected ({matches} matches, {len(existence_only)} cooldown-effect-only)")
    return {'content_div': content_div, 'existence_only': existence_only, 'matches': matches}


if __name__ == "__main__":
    run_test()
