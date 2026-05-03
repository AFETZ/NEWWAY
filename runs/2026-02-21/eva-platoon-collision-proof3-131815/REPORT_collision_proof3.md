# EVA Platoon Proof (baseline vs lossy PHY)

Run dir: `analysis/scenario_runs/2026-02-21/eva-platoon-collision-proof3-131815`

| case | avg PRR [-] | avg latency [ms] | CAM dropped PHY [count] | control actions [count] | min TTC [s] | min gap [m] | risky TTC events @3.1s [count] | collisions [count] |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 0.901954 | 11.3007 | 0 | 590 | 3.196 | 5.210 | 0 | 0 |
| lossy | 0.624577 | 11.8773 | 10618 | 32 | 2.897 | 5.210 | 2 | 0 |

## Conclusion
- PHY-loss (lossy) significantly reduces communication quality (PRR down, CAM PHY drops up).
- Behavioral response degrades strongly (control actions reduced).
- Safety proxy crosses danger threshold: `risky_ttc_events` at 3.1 s appears only in lossy run.
- Physical collisions were not observed in this pair (`collisions=0`), so evidence is for danger-state transition, not impact occurrence.