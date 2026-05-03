# strict_lane_obstacle scene

- scene file: `scene.xml`
- mesh source: shared symlink to `src/sionna/scenarios/SionnaCircleScenario/meshes`
- current registration convention:
  - SUMO coordinates are used directly as `x,y`
  - altitude is provided by the TraCI/Sionna bridge
  - vehicle placement is dynamic through `LOC_UPDATE`
- registration status:
  - dedicated scene path exists for the strict package;
  - geometry is still inherited from the current circle urban scene and should be treated
    as a provisional registration baseline for thesis batch work.
