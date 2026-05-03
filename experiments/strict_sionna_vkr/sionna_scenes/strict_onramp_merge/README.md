# strict_onramp_merge scene

- scene file: `scene.xml`
- mesh source: shared symlink to `src/sionna/scenarios/SionnaCircleScenario/meshes`
- current registration convention:
  - SUMO on-ramp merge coordinates are forwarded directly to Sionna;
  - positions update at runtime through `LOC_UPDATE`;
  - the strict package treats this as a dedicated scene entrypoint for repeatable runs.
- registration status:
  - scenario-local scene path is fixed and documented;
  - the mesh baseline is still inherited from the current urban circle scene, so the
    present strict evidence should be interpreted as geometry-sensitive but not as a
    hand-built on-ramp digital twin.
