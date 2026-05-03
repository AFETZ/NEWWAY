# strict_intersection scene

- scene file: `scene.xml`
- mesh source: shared symlink to `src/sionna/scenarios/SionnaCircleScenario/meshes`
- current registration convention:
  - SUMO coordinates are forwarded directly to Sionna;
  - vehicle antennas are attached dynamically by the bridge;
  - LOS and path gain are computed through the per-scenario scene entrypoint.
- registration status:
  - scene entrypoint is now scenario-local and frozen in the manifest;
  - the underlying urban mesh remains the current circle scene baseline and should be
    refined in future iterations if tighter geometric fidelity is required.
