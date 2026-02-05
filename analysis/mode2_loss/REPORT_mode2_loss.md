# NR-V2X Mode 2 Loss Sweep Evidence Report

## Scenario + Fixed Controls
- Scenario: v2v-emergencyVehicleAlert-nrv2x
- Mobility: SUMO v2v_map (cars.rou.xml, map.sumo.cfg)
- Penetration rate fixed where configured
- Seeds fixed via --RngRun (see sweep metadata)
- Reaction delay uses first CAM from emergency vehicle (stationId=2 in cars.rou.xml)

## Loss Sweep Definition
Sweep varied: txPower, mcs, slThresPsschRsrp, enableChannelRandomness, channelUpdatePeriod

## Measured Comms Degradation
- PRR by tech: analysis/mode2_loss/figures/prr_by_tech.png
- PRR vs loss knobs: analysis/mode2_loss/figures/prr_vs_txPower.png (and related plots)

## Measured Behavior Change
- Histograms: analysis/mode2_loss/figures/hist_max_decel_by_tech.png, analysis/mode2_loss/figures/hist_time_to_first_brake_by_tech.png

## Cross-link Comms → Behavior
- PRR vs time_to_first_brake: analysis/mode2_loss/figures/scatter_prr_vs_time_to_first_brake.png
- PRR vs max_decel: analysis/mode2_loss/figures/scatter_prr_vs_max_decel.png
- PRR vs reaction delay: analysis/mode2_loss/figures/scatter_prr_vs_reaction_delay.png
- PRR vs reaction delay (p90): analysis/mode2_loss/figures/reaction_delay_p90_vs_prr.png

## Conclusion Statement (Thesis-ready)
When PRR drops from 0.938 to 0.693, p90 reaction delay increases from 3.984s to 7.469s, indicating delayed cooperative response under degraded NR Mode 2 comms.
