# NR-V2X Mode 2 Loss Sweep Evidence Report

## Scenario + Fixed Controls
- Scenario: v2v-emergencyVehicleAlert-nrv2x
- Mobility: SUMO v2v_map (cars.rou.xml, map.sumo.cfg)
- Penetration rate fixed where configured
- Seeds fixed via --RngRun (see sweep metadata)
- Reaction delay uses first CAM from emergency vehicle (stationId=2 in cars.rou.xml)

## Loss Sweep Definition
Sweep varied: txPower

## Measured Comms Degradation
- PRR by tech: analysis/mode2_loss/figures/sweep/prr_by_tech.png
- PRR vs loss knobs: analysis/mode2_loss/figures/sweep/prr_vs_txPower.png (and related plots)
- AoI distribution: analysis/mode2_loss/figures/sweep/aoi_p95_hist_by_tech.png

## Measured Behavior Change
- Behavior vs PRR (time-to-first-brake): analysis/mode2_loss/figures/sweep/behavior_vs_prr_time_to_first_brake.png
- Behavior vs PRR (max decel): analysis/mode2_loss/figures/sweep/behavior_vs_prr_max_decel.png

## Cross-link Comms → Behavior
- PRR vs reaction delay: analysis/mode2_loss/figures/sweep/reaction_delay_vs_prr.png
- PRR vs reaction delay (p90): analysis/mode2_loss/figures/sweep/reaction_delay_p90_vs_prr.png

## Conclusion Statement (Thesis-ready)
When PRR drops from 0.938 to 0.077, p90 reaction delay increases from 3.984s to 18.094s, indicating delayed cooperative response under degraded NR Mode 2 comms.
