# Repo Cleanup & Reorganization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reorganize NEWWAY repo into a clean `experiments/`, `runs/`, `tools/`, `reports/`, `archive/` layout. ВСЕ тексты ВКР уходят в archive; evidence централизуется; дубликаты сворачиваются; агентские .md явно скрывают archive от ИИ.

**Architecture:** Two commits — first a snapshot of current uncommitted work, then ONE big reorg commit (per spec Q4). Plain `mv` for both tracked and untracked files; final `git add -A` собирает всё. Path-rewrites in run.sh / tools/ scripts are part of the reorg commit. New READMEs and AGENTS.md fix the navigation story.

**Tech Stack:** bash, git, sed/Edit, basic POSIX tools. No build, no language runtime touches.

**Companion spec:** [docs/superpowers/specs/2026-05-03-repo-cleanup-design.md](../specs/2026-05-03-repo-cleanup-design.md)

---

## Phase 0 — Pre-flight: snapshot & baseline

### Task 0.1: Capture before-tree snapshot

**Files:**
- Create: `/tmp/before-cleanup-tree.txt` (will move into archive in Task 9.x)

- [ ] **Step 1: Run tree, save to /tmp**

```bash
tree -L 3 -a -I '.git|.venv|.venv_docs|.venv_sionna|.bootstrap-ns3|.optix-wsl|__pycache__|node_modules' /home/afetz/work/clean/NEWWAY > /tmp/before-cleanup-tree.txt
wc -l /tmp/before-cleanup-tree.txt
```

Expected: file has > 200 lines.

### Task 0.2: Snapshot uncommitted changes

**Files:**
- N/A (git operation)

- [ ] **Step 1: Verify on right branch**

```bash
git -C /home/afetz/work/clean/NEWWAY rev-parse --abbrev-ref HEAD
```

Expected: `bootstrap/dev-onboarding`.

- [ ] **Step 2: Stage everything**

```bash
cd /home/afetz/work/clean/NEWWAY
git add -A
git status --short | head -30
```

Expected: many staged files (M, A, D), нет ?? в выводе.

- [ ] **Step 3: Snapshot commit**

```bash
git commit -m "$(cat <<'EOF'
chore: snapshot before repo reorganization

Captures all in-flight VKR/scenario/analysis work prior to the big
experiments/runs/tools/reports/archive reorg. See
docs/superpowers/specs/2026-05-03-repo-cleanup-design.md.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
git log --oneline -3
```

Expected: new commit `chore: snapshot before repo reorganization`, working tree clean.

- [ ] **Step 4: Verify clean**

```bash
git status
```

Expected: `nothing to commit, working tree clean`.

---

## Phase 1 — Create new directory skeleton

### Task 1.1: Create top-level new dirs

- [ ] **Step 1: mkdir all new top-level dirs**

```bash
cd /home/afetz/work/clean/NEWWAY
mkdir -p \
  experiments \
  runs \
  reports \
  tools/plots \
  tools/analysis \
  tools/vkr \
  archive/2026-05-03/vkr_manuscript/figures \
  archive/2026-05-03/superseded/conference \
  archive/2026-05-03/superseded/analysis_docx \
  archive/2026-05-03/analysis_misc \
  archive/2026-05-03/smoke_runs \
  archive/2026-05-03/audit_history
ls -d experiments runs reports tools/{plots,analysis,vkr} archive/2026-05-03/*
```

Expected: every listed dir exists. Note: `archive/2026-05-03/intersection_3d_animation/` and `archive/2026-05-03/mode2_loss/` НЕ предсоздаются — они появятся как `mv`-ы в Task 5.6.

---

## Phase 2 — Move scenario folders → experiments/

### Task 2.1: truck_lane_change ← valid_scenario + my_scenarios/truck_lane_change_scenario

- [ ] **Step 1: Create target structure**

```bash
cd /home/afetz/work/clean/NEWWAY
mkdir -p experiments/truck_lane_change/{scripts,docs}
```

- [ ] **Step 2: Move valid_scenario contents**

```bash
mv valid_scenario/run.sh experiments/truck_lane_change/scripts/run.sh
mv valid_scenario/start_sionna_server.sh experiments/truck_lane_change/scripts/start_sionna_server.sh
mv valid_scenario/README.md experiments/truck_lane_change/docs/README.md
mv valid_scenario/VKR_SCENARIO_TEXT.md archive/2026-05-03/vkr_manuscript/valid_scenario_VKR_SCENARIO_TEXT.md
rmdir valid_scenario
```

- [ ] **Step 3: Merge my_scenarios/truck_lane_change_scenario**

```bash
# Wrapper run.sh не нужен — у нас один настоящий run.sh.
rm my_scenarios/truck_lane_change_scenario/run.sh
rm my_scenarios/truck_lane_change_scenario/start_sionna_server.sh
mv my_scenarios/truck_lane_change_scenario/README.md experiments/truck_lane_change/docs/README_diploma.md
# output/ может быть пустым symlink/файлом — переедет если есть содержимое
if [ -e my_scenarios/truck_lane_change_scenario/output ]; then
  mkdir -p experiments/truck_lane_change/results
  mv my_scenarios/truck_lane_change_scenario/output experiments/truck_lane_change/results/output
fi
rmdir my_scenarios/truck_lane_change_scenario
```

- [ ] **Step 4: Verify**

```bash
ls experiments/truck_lane_change/scripts experiments/truck_lane_change/docs
test ! -d valid_scenario && echo "valid_scenario removed OK"
test ! -d my_scenarios/truck_lane_change_scenario && echo "my_scenarios entry removed OK"
```

Expected: both removed, target has run.sh, start_sionna_server.sh, README.md, README_diploma.md.

### Task 2.2: intersection_crash ← valid_intersection_scenario + my_scenarios/intersection_crash_scenario

- [ ] **Step 1: Create + move valid_**

```bash
mkdir -p experiments/intersection_crash/{scripts,docs}
mv valid_intersection_scenario/run.sh experiments/intersection_crash/scripts/run.sh
mv valid_intersection_scenario/start_sionna_server.sh experiments/intersection_crash/scripts/start_sionna_server.sh
mv valid_intersection_scenario/README.md experiments/intersection_crash/docs/README.md
rmdir valid_intersection_scenario
```

- [ ] **Step 2: Merge my_scenarios/intersection_crash_scenario**

```bash
rm my_scenarios/intersection_crash_scenario/run.sh
rm my_scenarios/intersection_crash_scenario/start_sionna_server.sh
mv my_scenarios/intersection_crash_scenario/README.md experiments/intersection_crash/docs/README_diploma.md
if [ -e my_scenarios/intersection_crash_scenario/output ]; then
  mkdir -p experiments/intersection_crash/results
  mv my_scenarios/intersection_crash_scenario/output experiments/intersection_crash/results/output
fi
rmdir my_scenarios/intersection_crash_scenario
```

- [ ] **Step 3: Verify**

```bash
ls experiments/intersection_crash/scripts experiments/intersection_crash/docs
test ! -d valid_intersection_scenario && test ! -d my_scenarios/intersection_crash_scenario && echo OK
```

Expected: OK printed.

### Task 2.3: cpm_perception ← valid_cpm_perception_scenario + my_scenarios/cpm_perception_scenario

- [ ] **Step 1: Create + move valid_**

```bash
mkdir -p experiments/cpm_perception/{scripts,docs,tools}
mv valid_cpm_perception_scenario/run.sh experiments/cpm_perception/scripts/run.sh
mv valid_cpm_perception_scenario/run_sensor_bad_cpm.sh experiments/cpm_perception/scripts/run_sensor_bad_cpm.sh
mv valid_cpm_perception_scenario/run_sensor_good_cpm.sh experiments/cpm_perception/scripts/run_sensor_good_cpm.sh
mv valid_cpm_perception_scenario/run_sensor_only.sh experiments/cpm_perception/scripts/run_sensor_only.sh
mv valid_cpm_perception_scenario/start_sionna_server.sh experiments/cpm_perception/scripts/start_sionna_server.sh
mv valid_cpm_perception_scenario/summarize_runs.py experiments/cpm_perception/tools/summarize_runs.py
mv valid_cpm_perception_scenario/README.md experiments/cpm_perception/docs/README.md
rmdir valid_cpm_perception_scenario
```

- [ ] **Step 2: Merge my_scenarios/cpm_perception_scenario**

```bash
# В my_scenarios все скрипты — wrappers; удаляем
rm my_scenarios/cpm_perception_scenario/run.sh
rm my_scenarios/cpm_perception_scenario/run_sensor_bad_cpm.sh
rm my_scenarios/cpm_perception_scenario/run_sensor_good_cpm.sh
rm my_scenarios/cpm_perception_scenario/run_sensor_only.sh
rm my_scenarios/cpm_perception_scenario/start_sionna_server.sh
mv my_scenarios/cpm_perception_scenario/README.md experiments/cpm_perception/docs/README_diploma.md
rmdir my_scenarios/cpm_perception_scenario
```

- [ ] **Step 3: Verify**

```bash
ls experiments/cpm_perception/scripts experiments/cpm_perception/tools experiments/cpm_perception/docs
test ! -d valid_cpm_perception_scenario && test ! -d my_scenarios/cpm_perception_scenario && echo OK
```

Expected: 5 scripts in scripts/, summarize_runs.py in tools/, 2 readmes in docs/.

### Task 2.4: intersection_radar_comm ← valid_intersection_radar_comm_scenario + my_scenarios/intersection_radar_comm_scenario

- [ ] **Step 1: Create + move valid_**

```bash
mkdir -p experiments/intersection_radar_comm/{scripts,docs,tools,sumo}
mv valid_intersection_radar_comm_scenario/run.sh experiments/intersection_radar_comm/scripts/run.sh
mv valid_intersection_radar_comm_scenario/run_radar_bad_link.sh experiments/intersection_radar_comm/scripts/run_radar_bad_link.sh
mv valid_intersection_radar_comm_scenario/run_radar_good_link.sh experiments/intersection_radar_comm/scripts/run_radar_good_link.sh
mv valid_intersection_radar_comm_scenario/run_radar_only.sh experiments/intersection_radar_comm/scripts/run_radar_only.sh
mv valid_intersection_radar_comm_scenario/start_sionna_server.sh experiments/intersection_radar_comm/scripts/start_sionna_server.sh
mv valid_intersection_radar_comm_scenario/analyze_outputs.py experiments/intersection_radar_comm/tools/analyze_outputs.py
mv valid_intersection_radar_comm_scenario/summarize_runs.py experiments/intersection_radar_comm/tools/summarize_runs.py
mv valid_intersection_radar_comm_scenario/README.md experiments/intersection_radar_comm/docs/README.md
mv valid_intersection_radar_comm_scenario/sumo/* experiments/intersection_radar_comm/sumo/
rmdir valid_intersection_radar_comm_scenario/sumo
rmdir valid_intersection_radar_comm_scenario
```

- [ ] **Step 2: Merge my_scenarios/intersection_radar_comm_scenario (с artifacts)**

```bash
# Wrapper-скрипты в архив
rm my_scenarios/intersection_radar_comm_scenario/run.sh 2>/dev/null || true
rm my_scenarios/intersection_radar_comm_scenario/run_radar_bad_link.sh 2>/dev/null || true
rm my_scenarios/intersection_radar_comm_scenario/run_radar_good_link.sh 2>/dev/null || true
rm my_scenarios/intersection_radar_comm_scenario/run_radar_only.sh 2>/dev/null || true
mv my_scenarios/intersection_radar_comm_scenario/README.md experiments/intersection_radar_comm/docs/README_diploma.md
# artifacts/ — это PNG-фигуры ВКР (3.8..3.12); важно перенести
if [ -d my_scenarios/intersection_radar_comm_scenario/artifacts ]; then
  mkdir -p experiments/intersection_radar_comm/results
  mv my_scenarios/intersection_radar_comm_scenario/artifacts experiments/intersection_radar_comm/results/artifacts
fi
# Если есть прочее — переместить целиком
if [ -n "$(ls -A my_scenarios/intersection_radar_comm_scenario 2>/dev/null)" ]; then
  mkdir -p experiments/intersection_radar_comm/results/extra
  mv my_scenarios/intersection_radar_comm_scenario/* experiments/intersection_radar_comm/results/extra/
fi
rmdir my_scenarios/intersection_radar_comm_scenario
```

- [ ] **Step 3: Verify**

```bash
ls experiments/intersection_radar_comm/scripts experiments/intersection_radar_comm/tools experiments/intersection_radar_comm/sumo
ls experiments/intersection_radar_comm/results/artifacts 2>/dev/null | head -5
test ! -d valid_intersection_radar_comm_scenario && test ! -d my_scenarios/intersection_radar_comm_scenario && echo OK
```

Expected: artifacts/ contains figure_*.png files.

### Task 2.5: compare_tech ← my_scenarios/compare_tech

- [ ] **Step 1: Move**

```bash
mkdir -p experiments/compare_tech/{scripts,docs}
mv my_scenarios/compare_tech/run.sh experiments/compare_tech/scripts/run.sh
mv my_scenarios/compare_tech/README.md experiments/compare_tech/docs/README.md
rmdir my_scenarios/compare_tech
```

- [ ] **Step 2: Verify + clean my_scenarios**

```bash
mv my_scenarios/README.md archive/2026-05-03/audit_history/my_scenarios_README.md
rmdir my_scenarios
test ! -d my_scenarios && echo OK
```

Expected: my_scenarios entirely gone.

### Task 2.6: intersection_v2x_awareness ← hardwork

- [ ] **Step 1: Move with rename of run script**

```bash
mkdir -p experiments/intersection_v2x_awareness/{scripts,docs,tools}
mv hardwork/run_intersection_natural.sh experiments/intersection_v2x_awareness/scripts/run.sh
mv hardwork/compare_old_vs_new.sh experiments/intersection_v2x_awareness/scripts/compare_old_vs_new.sh
mv hardwork/visualize_collision_causality.py experiments/intersection_v2x_awareness/tools/visualize_collision_causality.py
mv hardwork/CHANGES.md experiments/intersection_v2x_awareness/docs/CHANGES.md
rmdir hardwork
```

- [ ] **Step 2: Stub README**

```bash
cat > experiments/intersection_v2x_awareness/docs/README.md <<'EOF'
# intersection_v2x_awareness

Свежая (apr 2026) переработка intersection-сценария: «v2x-awareness junction». Channel quality alone определяет исход — нет timer'ов и threshold'ов.

См. подробности и обоснование в [CHANGES.md](CHANGES.md).

## Запуск

Из корня репозитория:

```bash
experiments/intersection_v2x_awareness/scripts/run.sh
```

## Сравнение со старой версией

```bash
experiments/intersection_v2x_awareness/scripts/compare_old_vs_new.sh
```

## Постобработка

```bash
./.venv/bin/python experiments/intersection_v2x_awareness/tools/visualize_collision_causality.py --help
```
EOF
```

- [ ] **Step 3: Verify**

```bash
ls experiments/intersection_v2x_awareness/{scripts,docs,tools}
test ! -d hardwork && echo OK
```

Expected: 4 files distributed correctly.

### Task 2.7: operational ← scenarios

- [ ] **Step 1: Move scenarios/ wholesale**

```bash
mv scenarios experiments/operational
ls experiments/operational
```

Expected: 5g-phy-metrics, cttc-nr-v2x-demo-simple, nr-v2x-west-to-east-highway, v2v-cam-exchange-sionna-nrv2x, v2v-coexistence-80211p-nrv2x, v2v-emergencyVehicleAlert-nrv2x, README.md, RESEARCH_SCENARIOS.md.

### Task 2.8: strict_sionna_vkr → experiments/

- [ ] **Step 1: Move**

```bash
mv strict_sionna_vkr experiments/strict_sionna_vkr
ls experiments/strict_sionna_vkr
```

Expected: docs, manifests, scenarios, scripts, sionna_scenes, README.md.

### Task 2.9: raw ← raw_experiments

- [ ] **Step 1: Move**

```bash
mv raw_experiments experiments/raw
ls experiments/raw
```

Expected: README.md, runs/, truck_lane_change_5glena_raw/.

### Task 2.10: Snapshot phase 2 status

- [ ] **Step 1: Confirm experiments/ tree**

```bash
ls experiments
find experiments -maxdepth 2 -type d | sort
```

Expected: 9 experiment dirs.

---

## Phase 3 — Move analysis/scenario_runs/ split into runs/ + tools/

### Task 3.1: Move run dates → runs/

- [ ] **Step 1: Move dated subdirs and chatgpt_exports**

```bash
cd /home/afetz/work/clean/NEWWAY
mv analysis/scenario_runs/2026-* runs/
mv analysis/scenario_runs/chatgpt_exports runs/chatgpt_exports
ls runs | head -20
```

Expected: 8 date dirs + chatgpt_exports.

### Task 3.2: Move analytical scripts → tools/

- [ ] **Step 1: build_*_plots / build_*_summary / make_plots → tools/plots/**

```bash
mv analysis/scenario_runs/build_valid_scenario_intuitive_plots.py tools/plots/
mv analysis/scenario_runs/build_valid_scenario_story_plots.py tools/plots/
mv analysis/scenario_runs/build_drop_decision_timeline.py tools/plots/
mv analysis/scenario_runs/build_collision_causality_report.py tools/plots/
mv analysis/scenario_runs/build_compare_tech_summary.py tools/plots/
mv analysis/scenario_runs/build_intersection_scenario_summary.py tools/plots/
mv analysis/scenario_runs/make_plots.py tools/plots/
ls tools/plots
```

Expected: 7 .py files.

- [ ] **Step 2: analyze_* / compare_* / export_* → tools/analysis/**

```bash
mv analysis/scenario_runs/analyze_all_logs.py tools/analysis/
mv analysis/scenario_runs/analyze_netstate_collision_risk.py tools/analysis/
mv analysis/scenario_runs/compare_incident_baseline_loss.py tools/analysis/
mv analysis/scenario_runs/export_diploma_timeline.py tools/analysis/
mv analysis/scenario_runs/export_results_bundle.py tools/analysis/
ls tools/analysis
```

Expected: 5 .py files.

### Task 3.3: Archive audit logs from scenario_runs

- [ ] **Step 1: Move LOG_AUDIT files**

```bash
mv analysis/scenario_runs/LOG_AUDIT_2026-02-27.md archive/2026-05-03/audit_history/
mv analysis/scenario_runs/log_audit_summary_2026-02-27.csv archive/2026-05-03/audit_history/
```

### Task 3.4: Archive remaining scripts in scenario_runs

- [ ] **Step 1: Catch any leftover scripts**

```bash
ls analysis/scenario_runs/*.py 2>/dev/null
# Если что-то осталось — перенести в archive
for f in analysis/scenario_runs/*.py; do
  [ -e "$f" ] && mv "$f" archive/2026-05-03/analysis_misc/
done
ls analysis/scenario_runs
```

Expected: либо `No such file or directory`, либо файлы переехали в archive.

### Task 3.5: Move scenario_runs README and remove dir

- [ ] **Step 1: Move README to archive (новый runs/README.md создадим в фазе 9)**

```bash
mv analysis/scenario_runs/README.md archive/2026-05-03/audit_history/scenario_runs_README.md
rmdir analysis/scenario_runs
test ! -d analysis/scenario_runs && echo OK
```

---

## Phase 4 — Split analysis/vkr/ (manuscripts → archive, scripts → tools/vkr/)

### Task 4.1: Move VKR manuscript texts → archive

- [ ] **Step 1: Move all VKR_*.md, PLAN.md, CHAPTER_DRAFT.md**

```bash
cd /home/afetz/work/clean/NEWWAY
mkdir -p archive/2026-05-03/vkr_manuscript/chapters
mv analysis/vkr/VKR_chapter1_theoretical_review.md archive/2026-05-03/vkr_manuscript/chapters/
mv analysis/vkr/VKR_chapter2_tool_development.md archive/2026-05-03/vkr_manuscript/chapters/
mv analysis/vkr/VKR_chapter3_practical_part_draft.md archive/2026-05-03/vkr_manuscript/chapters/
mv analysis/vkr/VKR_conclusion.md archive/2026-05-03/vkr_manuscript/
mv analysis/vkr/VKR_front_matter.md archive/2026-05-03/vkr_manuscript/
mv analysis/vkr/VKR_appendices.md archive/2026-05-03/vkr_manuscript/
mv analysis/vkr/VKR_tables.md archive/2026-05-03/vkr_manuscript/
mv analysis/vkr/VKR_inventory.md archive/2026-05-03/vkr_manuscript/
mv analysis/vkr/VKR_bibliography.md archive/2026-05-03/vkr_manuscript/
mv analysis/vkr/VKR_bibliography_verified.md archive/2026-05-03/vkr_manuscript/
mv analysis/vkr/PLAN.md archive/2026-05-03/vkr_manuscript/
mv analysis/vkr/CHAPTER_DRAFT.md archive/2026-05-03/vkr_manuscript/
ls archive/2026-05-03/vkr_manuscript
```

Expected: 11 .md files at top + chapters/ subdir with 3 chapters.

- [ ] **Step 2: Move figures**

```bash
mv analysis/vkr/figures/* archive/2026-05-03/vkr_manuscript/figures/
rmdir analysis/vkr/figures
ls archive/2026-05-03/vkr_manuscript/figures | head -20
```

Expected: PNG files (figure_2_1, figure_3_*).

### Task 4.2: Move VKR generator scripts → tools/vkr/

- [ ] **Step 1: Move .py files**

```bash
mv analysis/vkr/build_final_vkr.py tools/vkr/
mv analysis/vkr/generate_chapter3_figures.py tools/vkr/
mv analysis/vkr/generate_figure_2_1.py tools/vkr/
mv analysis/vkr/implement_revised_final3_review.py tools/vkr/
mv analysis/vkr/insert_chapter3_into_docx.py tools/vkr/
mv analysis/vkr/render_final_vkr_pdf.py tools/vkr/
mv analysis/vkr/verify_bibliography.py tools/vkr/
ls tools/vkr
```

Expected: 7 .py files.

### Task 4.3: Remove now-empty analysis/vkr

- [ ] **Step 1: Verify empty + remove**

```bash
ls -la analysis/vkr 2>/dev/null
rmdir analysis/vkr
test ! -d analysis/vkr && echo OK
```

Expected: removed.

---

## Phase 5 — Move other analysis/ content

### Task 5.1: Move utility scripts at analysis/ root → tools/

- [ ] **Step 1: plots/animation generators → tools/plots/**

```bash
cd /home/afetz/work/clean/NEWWAY
mv analysis/render_sionna_animation.py tools/plots/
mv analysis/visualize_sionna_3d.py tools/plots/
mv analysis/plot_5g_phy_metrics.py tools/plots/
ls tools/plots
```

- [ ] **Step 2: analyzers → tools/analysis/**

```bash
mv analysis/analyze_phy_safety.py tools/analysis/
ls tools/analysis
```

### Task 5.2: Archive docx and PDFs from analysis/

- [ ] **Step 1: Move all docx + pdf to archive**

```bash
mv analysis/1.before_citations.docx archive/2026-05-03/superseded/analysis_docx/
mv analysis/1.citations_preview.docx archive/2026-05-03/superseded/analysis_docx/
mv analysis/chapter1_reference_fix_package.docx archive/2026-05-03/superseded/analysis_docx/
mv analysis/chapter1_reference_fix_package.md archive/2026-05-03/superseded/analysis_docx/
mv "analysis/отчет.before_ch1_integration.docx" archive/2026-05-03/superseded/analysis_docx/
mv "analysis/отчет.ch1_integrated_preview.docx" archive/2026-05-03/superseded/analysis_docx/
mv analysis/Rethinking_Persistent_Scheduling_in_5G_New_Radio_Vehicle_to_Everything.pdf archive/2026-05-03/analysis_misc/
ls archive/2026-05-03/superseded/analysis_docx
```

Expected: 6 files in superseded/analysis_docx.

### Task 5.3: Archive one-off scripts and logs

- [ ] **Step 1: Move misc scripts**

```bash
mv analysis/markdown_to_docx_package.py archive/2026-05-03/analysis_misc/
mv analysis/rebuild_simple_a3_docx.py archive/2026-05-03/analysis_misc/
mv analysis/docx_audit.py archive/2026-05-03/analysis_misc/
mv analysis/integrate_ch1_revision_into_report.py archive/2026-05-03/analysis_misc/
mv analysis/one_docx_reference_revision.txt archive/2026-05-03/analysis_misc/
mv analysis/thesis_campaign.log archive/2026-05-03/analysis_misc/
ls archive/2026-05-03/analysis_misc | head -20
```

### Task 5.4: Archive vkr_extract

- [ ] **Step 1: Move folder**

```bash
mv analysis/vkr_extract archive/2026-05-03/analysis_misc/vkr_extract
ls archive/2026-05-03/analysis_misc/vkr_extract | head -10
```

### Task 5.5: Archive smoke runs and campaign smokes

- [ ] **Step 1: Move smoke folders**

```bash
mv analysis/strict_runs_smoke archive/2026-05-03/smoke_runs/strict_runs_smoke
mv analysis/strict_runs_smoke_full archive/2026-05-03/smoke_runs/strict_runs_smoke_full
mv analysis/thesis_campaign_calibration_smoke archive/2026-05-03/smoke_runs/thesis_campaign_calibration_smoke
mv analysis/thesis_campaign_runs_smoke archive/2026-05-03/smoke_runs/thesis_campaign_runs_smoke
ls archive/2026-05-03/smoke_runs
```

Expected: 4 dirs.

### Task 5.6: Archive intersection_3d_animation and mode2_loss

- [ ] **Step 1: Move folders directly (dest dirs do not exist yet)**

```bash
mv analysis/intersection_3d_animation archive/2026-05-03/intersection_3d_animation
mv analysis/mode2_loss archive/2026-05-03/mode2_loss
ls archive/2026-05-03/intersection_3d_animation | head -10
ls archive/2026-05-03/mode2_loss | head -10
```

### Task 5.7: Archive audit history

- [ ] **Step 1: Move audit + workspace files**

```bash
mv analysis/CODE_TRIAGE_2026-04-19.md archive/2026-05-03/audit_history/
mv analysis/WORKSPACE_CLEANUP_2026-04-19.md archive/2026-05-03/audit_history/
mv analysis/REPO_AUDIT_2026-02-27.md archive/2026-05-03/audit_history/
mv WORKSPACE_MAP.md archive/2026-05-03/audit_history/WORKSPACE_MAP.md
mv codex.md archive/2026-05-03/audit_history/codex.md.old
ls archive/2026-05-03/audit_history
```

Expected: 8+ files.

### Task 5.8: Move before-cleanup-tree.txt into archive

- [ ] **Step 1: Move from /tmp**

```bash
mv /tmp/before-cleanup-tree.txt archive/2026-05-03/before-cleanup-tree.txt
test -f archive/2026-05-03/before-cleanup-tree.txt && echo OK
```

---

## Phase 6 — Reports + cycle7 merge

### Task 6.1: cycle7_fizulin_av merge per Q3

- [ ] **Step 1: Move live cycle7 → reports/**

```bash
cd /home/afetz/work/clean/NEWWAY
mkdir -p reports
mv cycle7_fizulin_av reports/cycle7_fizulin_av
ls reports/cycle7_fizulin_av | head -20
```

- [ ] **Step 2: Copy lena_db_dataset from archive copy**

```bash
cp -R archive/legacy/2026-04-19/cycle7_variant_from_root_1/lena_db_dataset reports/cycle7_fizulin_av/lena_db_dataset
ls reports/cycle7_fizulin_av/lena_db_dataset | head -10
```

Expected: dataset folder present in live reports/cycle7_fizulin_av.

### Task 6.2: cycle7_fizulin_av_report (organized version) → reports/cycle7_fizulin_av_v2/

- [ ] **Step 1: Move**

```bash
mv analysis/cycle7_fizulin_av_report reports/cycle7_fizulin_av_v2
ls reports/cycle7_fizulin_av_v2 | head -20
```

### Task 6.3: web_ui_scenario_manager_report → reports/

- [ ] **Step 1: Move**

```bash
mv analysis/web_ui_scenario_manager_report reports/web_ui_scenario_manager
ls reports/web_ui_scenario_manager | head -10
```

### Task 6.4: Verify analysis/ is now empty

- [ ] **Step 1: Inventory remaining**

```bash
ls -la analysis 2>/dev/null
find analysis -type f 2>/dev/null
```

Expected: пусто (или только `.` и `..`).

- [ ] **Step 2: Remove dir**

```bash
rmdir analysis 2>/dev/null
test ! -d analysis && echo OK || (echo "FAIL: analysis still has content"; ls -la analysis)
```

Expected: OK.

---

## Phase 7 — Conference cleanup

### Task 7.1: Archive transitional/older docx

- [ ] **Step 1: Move transitional + older Paper Title6**

```bash
cd /home/afetz/work/clean/NEWWAY
mv conference/Italian_MAIN_transitional.docx archive/2026-05-03/superseded/conference/
mv conference/Paper_Title6_transitional.docx archive/2026-05-03/superseded/conference/
mv "conference/Paper Title6.docx" archive/2026-05-03/superseded/conference/
ls conference
```

Expected: 2 docx остались (Fizulin_Romanov_MAIN2026..., Italian_MAIN_conference_FizulinAV) + generate_ieee_paper.py.

### Task 7.2: Move generator script → tools/vkr/

- [ ] **Step 1: Move**

```bash
mv conference/generate_ieee_paper.py tools/vkr/generate_ieee_paper.py
ls conference
```

Expected: только 2 docx.

---

## Phase 8 — Path/reference updates

### Task 8.1: Inventory ROOT references in run.sh files

- [ ] **Step 1: List all run.sh that need ROOT update**

```bash
grep -rln 'cd "\$(dirname "\${BASH_SOURCE\[0\]}")/\.\.' experiments/*/scripts/ 2>/dev/null
```

Expected: list of run.sh files (truck_lane_change, intersection_crash, intersection_radar_comm, cpm_perception, intersection_v2x_awareness).

### Task 8.2: Fix experiments/truck_lane_change/scripts/run.sh

**Files:**
- Modify: `experiments/truck_lane_change/scripts/run.sh`

- [ ] **Step 1: Read top of file to find current ROOT line**

```bash
head -10 experiments/truck_lane_change/scripts/run.sh
```

Expected: line `ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"`.

- [ ] **Step 2: Edit ROOT (use Edit tool)**

Old:
```bash
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
```

New:
```bash
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
```

- [ ] **Step 3: Replace OUT_DIR scenario name**

Old:
```bash
OUT_DIR="${OUT_DIR:-$HOME/NEWWAY_runs/$DATE_TAG/valid_scenario}"
```

New:
```bash
OUT_DIR="${OUT_DIR:-$HOME/NEWWAY_runs/$DATE_TAG/truck_lane_change}"
```

- [ ] **Step 4: Replace SIONNA_START_SCRIPT path**

Search in file:
```bash
grep -n 'SIONNA_START_SCRIPT' experiments/truck_lane_change/scripts/run.sh
grep -n 'valid_scenario' experiments/truck_lane_change/scripts/run.sh
```

Replace each occurrence of `valid_scenario/start_sionna_server.sh` → `experiments/truck_lane_change/scripts/start_sionna_server.sh`. Replace `analysis/scenario_runs/chatgpt_exports` → `runs/chatgpt_exports`.

- [ ] **Step 5: Validate**

```bash
bash -n experiments/truck_lane_change/scripts/run.sh && echo "syntax OK"
grep -n 'analysis/scenario_runs\|valid_scenario' experiments/truck_lane_change/scripts/run.sh
```

Expected: syntax OK; grep returns nothing.

### Task 8.3: Fix experiments/intersection_crash/scripts/run.sh

Same pattern as 8.2 but:
- `valid_intersection_scenario` → `intersection_crash` in OUT_DIR
- `valid_intersection_scenario/start_sionna_server.sh` → `experiments/intersection_crash/scripts/start_sionna_server.sh`
- `analysis/scenario_runs/chatgpt_exports` → `runs/chatgpt_exports`
- ROOT levels +2

- [ ] **Step 1: Edit ROOT**

Same Edit as 8.2 step 2.

- [ ] **Step 2: Edit OUT_DIR**

Old: `OUT_DIR="${OUT_DIR:-$HOME/NEWWAY_runs/$DATE_TAG/valid_intersection_scenario}"`
New: `OUT_DIR="${OUT_DIR:-$HOME/NEWWAY_runs/$DATE_TAG/intersection_crash}"`

- [ ] **Step 3: Edit SIONNA_START_SCRIPT and EXPORT_BASE**

Use grep first:
```bash
grep -n 'valid_intersection_scenario\|analysis/scenario_runs' experiments/intersection_crash/scripts/run.sh
```

Replace `valid_intersection_scenario/start_sionna_server.sh` → `experiments/intersection_crash/scripts/start_sionna_server.sh` and `analysis/scenario_runs/chatgpt_exports` → `runs/chatgpt_exports`.

- [ ] **Step 4: Replace any `scenarios/v2v-emergencyVehicleAlert-nrv2x/` references**

```bash
grep -n 'scenarios/v2v-' experiments/intersection_crash/scripts/run.sh
```

Replace with `experiments/operational/v2v-emergencyVehicleAlert-nrv2x/`.

- [ ] **Step 5: Validate**

```bash
bash -n experiments/intersection_crash/scripts/run.sh && echo "syntax OK"
grep -n 'analysis/scenario_runs\|valid_intersection_scenario\|scenarios/v2v-' experiments/intersection_crash/scripts/run.sh
```

Expected: syntax OK; grep empty.

### Task 8.4: Fix experiments/intersection_radar_comm/scripts/run.sh

Same pattern; replace:
- ROOT levels +2
- `OUT_DIR` scenario tag → `intersection_radar_comm`
- `valid_intersection_radar_comm_scenario/...` → `experiments/intersection_radar_comm/scripts/...`
- `analysis/scenario_runs/chatgpt_exports` → `runs/chatgpt_exports`
- Any `summarize_runs.py` / `analyze_outputs.py` invocations → `experiments/intersection_radar_comm/tools/...`

- [ ] **Step 1: Inventory references**

```bash
grep -n 'valid_intersection_radar_comm_scenario\|analysis/scenario_runs\|scenarios/v2v-' experiments/intersection_radar_comm/scripts/run.sh
grep -n 'summarize_runs\|analyze_outputs' experiments/intersection_radar_comm/scripts/run.sh
```

- [ ] **Step 2: Apply Edit per occurrence (all replacements above)**

- [ ] **Step 3: Same for run_radar_*.sh**

```bash
for f in experiments/intersection_radar_comm/scripts/run_radar_*.sh; do
  echo "=== $f ==="
  grep -n 'valid_intersection_radar_comm_scenario\|analysis/scenario_runs\|scenarios/v2v-' "$f" || echo "(clean)"
done
```

Apply Edit per file as needed.

- [ ] **Step 4: Validate**

```bash
for f in experiments/intersection_radar_comm/scripts/*.sh; do bash -n "$f" || echo "FAIL: $f"; done
echo "done"
```

Expected: no FAIL.

### Task 8.5: Fix experiments/cpm_perception/scripts/run.sh + run_sensor_*.sh

Same pattern: ROOT +2, OUT_DIR → `cpm_perception`, paths to start_sionna_server.

- [ ] **Step 1: Inventory**

```bash
grep -n 'valid_cpm_perception_scenario\|analysis/scenario_runs\|scenarios/v2v-' experiments/cpm_perception/scripts/*.sh
```

- [ ] **Step 2: Apply Edits**

- [ ] **Step 3: Validate**

```bash
for f in experiments/cpm_perception/scripts/*.sh; do bash -n "$f" || echo "FAIL: $f"; done
```

### Task 8.6: Fix experiments/intersection_v2x_awareness/scripts/run.sh

The original `hardwork/run_intersection_natural.sh` had its own ROOT pattern. Inspect:

- [ ] **Step 1: Inventory**

```bash
head -20 experiments/intersection_v2x_awareness/scripts/run.sh
grep -n 'ROOT=\|hardwork\|scenarios/' experiments/intersection_v2x_awareness/scripts/run.sh
```

- [ ] **Step 2: Update ROOT level (was likely 1, now 3) if applicable**

If file uses `ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"` (1 level up from `hardwork/`), update to 3 levels.

- [ ] **Step 3: Replace any `scenarios/v2v-` → `experiments/operational/v2v-`**

- [ ] **Step 4: Validate**

```bash
bash -n experiments/intersection_v2x_awareness/scripts/run.sh && echo OK
```

### Task 8.7: Fix experiments/operational/v2v-emergencyVehicleAlert-nrv2x/run.sh and *.sh

The operational scenarios may have ROOT = `../..` (one level up from `scenarios/<name>/`). After move to `experiments/operational/<name>/`, ROOT levels need +1.

- [ ] **Step 1: Inventory all run*.sh in operational/**

```bash
find experiments/operational -name '*.sh' -exec grep -l 'ROOT=\|cd.*BASH_SOURCE' {} \;
```

- [ ] **Step 2: For each, check ROOT pattern**

```bash
for f in $(find experiments/operational -name '*.sh'); do
  echo "=== $f ==="
  grep -n 'ROOT=' "$f" || echo "(no ROOT line)"
done
```

- [ ] **Step 3: Update ROOT level in each (Edit tool, +1 level deeper)**

For files like `experiments/operational/v2v-emergencyVehicleAlert-nrv2x/run.sh`:

Old: `ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"`
New: `ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"`

- [ ] **Step 4: Replace any `analysis/scenario_runs` → `runs/`**

```bash
for f in $(find experiments/operational -name '*.sh'); do
  grep -n 'analysis/scenario_runs' "$f" || true
done
```

Apply Edit per occurrence.

- [ ] **Step 5: Validate all**

```bash
for f in $(find experiments/operational -name '*.sh'); do bash -n "$f" || echo "FAIL: $f"; done
echo "done"
```

### Task 8.8: Fix tools/scenario_manager/scenarios.py

**Files:**
- Modify: `tools/scenario_manager/scenarios.py`

- [ ] **Step 1: Inventory my_scenarios references**

```bash
grep -n 'my_scenarios\|valid_\|scenarios/v2v-\|hardwork' tools/scenario_manager/scenarios.py
```

- [ ] **Step 2: Replace per mapping**

Mapping:
- `my_scenarios/truck_lane_change_scenario` → `experiments/truck_lane_change`
- `my_scenarios/intersection_crash_scenario` → `experiments/intersection_crash`
- `my_scenarios/cpm_perception_scenario` → `experiments/cpm_perception`
- `my_scenarios/intersection_radar_comm_scenario` → `experiments/intersection_radar_comm`
- `my_scenarios/compare_tech` → `experiments/compare_tech`
- `valid_scenario` → `experiments/truck_lane_change`
- `valid_intersection_scenario` → `experiments/intersection_crash`
- `valid_cpm_perception_scenario` → `experiments/cpm_perception`
- `valid_intersection_radar_comm_scenario` → `experiments/intersection_radar_comm`
- `scenarios/v2v-...` → `experiments/operational/v2v-...`

Use Edit per literal string occurrence.

- [ ] **Step 3: Update run.sh paths** (`<scenario>/run.sh` → `<scenario>/scripts/run.sh`)

If the file references run.sh paths, prefix `scripts/`.

- [ ] **Step 4: Validate Python syntax**

```bash
./.venv/bin/python -c "import ast; ast.parse(open('tools/scenario_manager/scenarios.py').read())" && echo OK
```

### Task 8.9: Fix tools/scenario_manager/run_*.sh

- [ ] **Step 1: Inventory**

```bash
grep -n 'scenarios/v2v-\|my_scenarios\|valid_\|hardwork' tools/scenario_manager/*.sh
```

- [ ] **Step 2: Apply Edits per file** (same mapping as 8.8)

- [ ] **Step 3: Validate**

```bash
for f in tools/scenario_manager/*.sh; do bash -n "$f" || echo "FAIL: $f"; done
```

### Task 8.10: Fix tools/plots/build_*.py and others

**Files:** all `tools/plots/*.py`, `tools/analysis/*.py`, `tools/vkr/*.py`

- [ ] **Step 1: Inventory `analysis/` references in tools/**

```bash
grep -rn 'analysis/scenario_runs\|analysis/vkr/figures\|my_scenarios/\|valid_\|scenarios/v2v-' tools/
```

- [ ] **Step 2: For each .py file, replace literal paths**

Mapping:
- `analysis/scenario_runs/` → `runs/`
- `analysis/vkr/figures/` → `archive/2026-05-03/vkr_manuscript/figures/` *(but better: пускай скрипты пишут в `tools/vkr/output/figures/` через --out-dir; для атомарности — оставляем literal substitution)*
- `my_scenarios/` → `experiments/` (с учётом маппинга имён)
- `valid_scenario/` → `experiments/truck_lane_change/`
- `valid_intersection_scenario/` → `experiments/intersection_crash/`
- `valid_cpm_perception_scenario/` → `experiments/cpm_perception/`
- `valid_intersection_radar_comm_scenario/` → `experiments/intersection_radar_comm/`
- `scenarios/v2v-*` → `experiments/operational/v2v-*`

Apply Edit per literal occurrence.

- [ ] **Step 3: Validate Python syntax across tools/**

```bash
for f in $(find tools -name '*.py'); do
  ./.venv/bin/python -c "import ast; ast.parse(open('$f').read())" || echo "FAIL: $f"
done
echo "done"
```

Expected: nothing FAIL.

### Task 8.11: Fix scripts/sync-overlay-into-bootstrap-ns3.sh and scripts/docker-run-eva-sionna.sh

- [ ] **Step 1: Inventory**

```bash
grep -n 'scenarios/v2v-\|my_scenarios\|valid_\|hardwork\|analysis/scenario_runs' scripts/*.sh
```

- [ ] **Step 2: Apply Edits per occurrence**

- [ ] **Step 3: Validate**

```bash
for f in scripts/*.sh; do bash -n "$f" || echo "FAIL: $f"; done
```

### Task 8.12: Update .gitignore

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Search for old patterns**

```bash
grep -n 'analysis/scenario_runs\|my_scenarios\|valid_\|hardwork\|scenarios/' .gitignore
```

- [ ] **Step 2: Replace with new layout (Edit per pattern)**

Mapping:
- `analysis/scenario_runs/` → `runs/`
- `analysis/vkr/figures/` (если есть как ignore) → удалить (figures в архиве)
- `my_scenarios/.../output` → `experiments/.../results/output`
- `analysis/strict_runs_smoke*` → удалить (теперь в archive/)
- `analysis/thesis_campaign_*` → удалить (в archive/)

Be conservative: keep what's still relevant, drop dead patterns.

- [ ] **Step 3: Verify .gitignore parses**

```bash
git check-ignore -v experiments/truck_lane_change/scripts/run.sh 2>&1 | head -3
```

Expected: not ignored (file is content we want tracked).

---

## Phase 9 — New documentation

### Task 9.1: Create experiments/README.md

**Files:**
- Create: `experiments/README.md`

- [ ] **Step 1: Write content**

```bash
cat > experiments/README.md <<'EOF'
# experiments/

Все эксперименты и сценарии симуляции в одном месте. Каждый подпакет — самодостаточный сценарий со своими `scripts/`, `docs/`, опционально `tools/`, `sumo/`, `results/`.

## Карта экспериментов

| Папка | Что делает | Главный скрипт |
|---|---|---|
| `truck_lane_change/` | Lane-change объезд остановившегося лидера, с явной cause-effect цепочкой PRR → manoeuvre. | `scripts/run.sh` |
| `intersection_crash/` | Junction priority-конфликт с третьим автомобилем. Demo crash vs safe pass. | `scripts/run.sh` |
| `intersection_radar_comm/` | Перекрёсток с 3 режимами: радар + V2X comm, плюс sweep по equiv_tx_power. | `scripts/run.sh`, `scripts/run_radar_*.sh` |
| `cpm_perception/` | CPM / collective perception, 3 режима (sensor only / good CPM / bad CPM). | `scripts/run.sh`, `scripts/run_sensor_*.sh` |
| `compare_tech/` | Compare V2X стека (NR-V2X / 802.11p) на одном trace. | `scripts/run.sh` |
| `intersection_v2x_awareness/` | Свежая (apr 2026) переработка intersection без timer-hardcoding. | `scripts/run.sh` |
| `operational/` | Operational launchers для C++ примеров ms-van3t (cttc, west-to-east-highway, v2v-cam-exchange-sionna, v2v-coexistence-80211p, v2v-emergencyVehicleAlert, 5g-phy-metrics). | `<name>/run.sh` |
| `strict_sionna_vkr/` | Строгий Sionna-пакет с собственными manifests/scripts/scenes. | `scripts/...` |
| `raw/` | Raw-only прогоны без постобработки (для воспроизводимости). | `<name>/run.sh` |

## Где результаты

Все evidence-прогоны для ВКР и анализов лежат в `runs/<YYYY-MM-DD>/<run_dir>/`. См. [`runs/README.md`](../runs/README.md).

In-experiment artifacts (если есть) — в `experiments/<name>/results/`.

## Где инструменты

Постобработка / графики / агрегация — в `tools/`. См. [`tools/README.md`](../tools/README.md).
EOF
```

### Task 9.2: Create runs/README.md

**Files:**
- Create: `runs/README.md`

- [ ] **Step 1: Write content**

```bash
cat > runs/README.md <<'EOF'
# runs/

Централизованное хранилище evidence-прогонов сценариев. Каждая дата — отдельная папка `<YYYY-MM-DD>/`, внутри — конкретные run-директории с `*.log`, `artifacts/`, `figures/`, `run_summary.csv`, `REPORT.md`.

## Структура

- `runs/<YYYY-MM-DD>/<run_dir>/` — данные одного прогона
- `runs/chatgpt_exports/` — компактные export-бандлы (опциональны, формируются `EXPORT_RESULTS=1` в run.sh сценариев)

## Постобработка

Скрипты лежат в `tools/`:

```bash
# Дипломные story-графики по lane-change кейсу
./.venv/bin/python tools/plots/build_valid_scenario_story_plots.py \
  --run-dir runs/<YYYY-MM-DD>/<run_dir>

# Интуитивные CSV-only графики
./.venv/bin/python tools/plots/build_valid_scenario_intuitive_plots.py \
  --run-dir runs/<YYYY-MM-DD>/<run_dir>

# Drop → decision timeline
./.venv/bin/python tools/plots/build_drop_decision_timeline.py \
  --run-dir runs/<YYYY-MM-DD>/<run_dir>

# Полный аудит логов по всем прогонам
./.venv/bin/python tools/analysis/analyze_all_logs.py \
  --root runs --out-dir runs --tag <YYYY-MM-DD>
```

## Управление объёмом

`runs/` может разрастаться. Правила:

1. Сохраняем только прогоны, которые упомянуты в защитных артефактах (тексты ВКР, статьи, отчёты).
2. Лишние черновые прогоны — переносим в `archive/<date>/runs/` (не удаляем).
3. Никогда не лезем руками в чужие даты — только добавляем новые.
EOF
```

### Task 9.3: Create tools/README.md

**Files:**
- Create: `tools/README.md`

- [ ] **Step 1: Write content**

```bash
cat > tools/README.md <<'EOF'
# tools/

Инструменты разработки и анализа. Не путать с in-experiment tools (`experiments/<name>/tools/`), которые специфичны для одного сценария.

## Структура

- `plots/` — генераторы графиков и анимаций (`build_*_plots.py`, `make_plots.py`, `render_*.py`, `visualize_*.py`, `plot_*.py`).
- `analysis/` — analyzers и aggregators (`analyze_*.py`, `compare_*.py`, `export_*.py`).
- `vkr/` — генераторы ВКР: фигуры (`generate_chapter*_figures.py`), сборка docx/pdf (`build_final_vkr.py`, `render_final_vkr_pdf.py`), bibliography (`verify_bibliography.py`), один-к-одному IEEE statья (`generate_ieee_paper.py`).
- `scenario_manager/` — модуль для централизованного запуска / sweep сценариев.
- `results_pipeline/` — пайплайн агрегации результатов.

## Типичные команды

```bash
# График из конкретного прогона
./.venv/bin/python tools/plots/build_valid_scenario_story_plots.py --run-dir runs/2026-03-04/<run>

# Аудит всех логов
./.venv/bin/python tools/analysis/analyze_all_logs.py --root runs --out-dir runs --tag <date>

# Регенерация фигур ВКР главы 3
./.venv/bin/python tools/vkr/generate_chapter3_figures.py
```

## Среды

В репозитории есть `.venv/`, `.venv_sionna/`, `.venv_docs/`. Большинство скриптов работают с `.venv/`.
EOF
```

### Task 9.4: Create archive/README.md

**Files:**
- Create: `archive/README.md`

- [ ] **Step 1: Write content**

```bash
cat > archive/README.md <<'EOF'
# archive/

> **ИИ-агентам (Claude/Codex/Gemini/прочие): НЕ ЧИТАТЬ И НЕ ИНДЕКСИРОВАТЬ содержимое этой папки.** Здесь лежат замороженные тексты ВКР, дублирующие docx, одноразовые скрипты, GIF-арт, отдельные эксперименты, аудиторские отчёты прошлых уборок. Эти файлы не должны влиять на текущую работу и не дают актуального контекста.

## Структура

- `legacy/` — материалы от предыдущих уборок (в т.ч. `2026-04-19/`).
- `2026-05-03/` — текущая большая уборка (см. `docs/superpowers/specs/2026-05-03-repo-cleanup-design.md`):
  - `vkr_manuscript/` — все тексты ВКР (главы, bibliography, appendices, tables, conclusion, front matter, inventory, PLAN, CHAPTER_DRAFT) + figures.
  - `superseded/conference/` — transitional/older docx статьи.
  - `superseded/analysis_docx/` — старые отчётные docx и pre-citations версии.
  - `analysis_misc/` — vkr_extract/, одноразовые скрипты сборки docx, разовый log, pdf чужой статьи.
  - `smoke_runs/` — strict_runs_smoke, thesis_campaign_*.
  - `intersection_3d_animation/` — GIF / 3D-анимации.
  - `mode2_loss/` — отдельный CARLA-эксперимент (не часть основной линии ВКР).
  - `audit_history/` — старые audit-документы (CODE_TRIAGE, WORKSPACE_CLEANUP, REPO_AUDIT, LOG_AUDIT, WORKSPACE_MAP, codex.md.old).
  - `before-cleanup-tree.txt` — снимок дерева перед уборкой.

## Когда нужно вернуться сюда

Только в трёх случаях:

1. Восстановить замороженный фрагмент текста ВКР для обновления.
2. Поднять архивные evidence для проверки утверждения в защите.
3. Audit-расследование «когда и зачем что-то менялось».
EOF
```

### Task 9.5: Create AGENTS.md

**Files:**
- Create: `AGENTS.md`

- [ ] **Step 1: Write content**

```bash
cat > AGENTS.md <<'EOF'
# AGENTS.md — инструкции для ИИ-агентов (Claude, Codex, Gemini и т.п.)

Этот файл — единый источник правил для любого AI-помощника, работающего в репозитории.

## Самое важное

**НЕ ЧИТАТЬ И НЕ ИНДЕКСИРОВАТЬ:**

- `archive/` — замороженные тексты ВКР, дубликаты, GIF-арт, audit-история. Не даёт актуального контекста и сбивает анализ.
- `.venv/`, `.venv_sionna/`, `.venv_docs/` — Python virtualenvs.
- `.bootstrap-ns3/` — sandboxed ns-3 build environment.
- `.optix-wsl/` — NVIDIA OptiX runtime.
- `.cache/`, `tmp/`, `__pycache__/` — кэши и временные данные.

Если запрос связан с историей или старыми решениями — спросить у пользователя, нужно ли поднимать `archive/`. Без явного запроса — не лезть.

## Карта репозитория

См. [REPO_LAYOUT.md](REPO_LAYOUT.md).

Краткий список:

- `src/` — overlay поверх ns-3/VaN3Twin (C++ код симулятора). **Не реструктурировать без необходимости** — это живая ветка от upstream.
- `experiments/` — все сценарии и эксперименты. См. [experiments/README.md](experiments/README.md).
- `runs/` — evidence-прогоны для ВКР и анализов. См. [runs/README.md](runs/README.md).
- `tools/` — генераторы графиков, аналитические скрипты, ВКР-сборка. См. [tools/README.md](tools/README.md).
- `reports/` — отчёты по циклам практики и web UI scenario manager.
- `conference/` — финальные docx статей (без черновиков).
- `docs/` — документация ns-3 upstream.

## Принципы при работе с кодом

1. **Минимальные изменения.** Не рефакторить лишнее. Если задача — fix bug, не делать reorg того же файла.
2. **Не трогать `src/` без причины.** Это код симулятора (большой, чувствительный к upstream).
3. **`run.sh` сценариев имеют собственный `ROOT="..."` контракт** (3 уровня вверх от `experiments/<name>/scripts/`). Не ломать.
4. **Тексты ВКР, конференц-статьи, отчёты циклов** — не править без явного запроса. В `archive/2026-05-03/vkr_manuscript/` лежит замороженный snapshot текста ВКР; основная работа над ВКР ведётся вне этого репозитория.
5. **Один большой коммит для крупных reorg** — текущий пользователь предпочитает атомарные изменения, см. историю коммитов.

## Среды и инструменты

- Стандартный Python venv: `.venv/bin/python`. Все скрипты в `tools/` и `experiments/<name>/tools/` рассчитаны на него.
- Для Sionna-зависимых скриптов: `.venv_sionna/bin/python`.
- `make` цели — в `Makefile`.

## Если непонятно — спросить

Не угадывать. Сценарии связаны с симулятором, ошибки могут привести к invalid evidence. Лучше спросить и сделать правильно.
EOF
```

### Task 9.6: Create CLAUDE.md as link to AGENTS.md

**Files:**
- Create: `CLAUDE.md`

- [ ] **Step 1: Write minimal content**

```bash
cat > CLAUDE.md <<'EOF'
# CLAUDE.md

См. [AGENTS.md](AGENTS.md) — единый источник правил для всех ИИ-агентов в репозитории.

Никогда не читать `archive/` без явного запроса. Все основные карты — `experiments/README.md`, `runs/README.md`, `tools/README.md`, `REPO_LAYOUT.md`.
EOF
```

### Task 9.7: Create REPO_LAYOUT.md

**Files:**
- Create: `REPO_LAYOUT.md`

- [ ] **Step 1: Write content**

```bash
cat > REPO_LAYOUT.md <<'EOF'
# REPO_LAYOUT.md — карта репозитория NEWWAY

Последняя реорганизация: 2026-05-03 (см. `docs/superpowers/specs/2026-05-03-repo-cleanup-design.md`).

## Корневые директории

| Путь | Назначение |
|---|---|
| `src/` | Overlay поверх ns-3 / VaN3Twin: C++ модули симулятора. Изменять осторожно. |
| `docs/` | Документация ns-3 upstream (rst). |
| `experiments/` | Все сценарии и эксперименты. См. `experiments/README.md`. |
| `runs/` | Evidence-прогоны (по датам). См. `runs/README.md`. |
| `reports/` | Учебные/рабочие отчёты (cycle7, scenario manager). |
| `conference/` | Финальные docx статей. |
| `tools/` | Генераторы графиков, analyzers, ВКР-сборка. См. `tools/README.md`. |
| `tests/` | Базовые тесты. |
| `scripts/` | Operational helpers (sync overlay, docker run и т.п.). |
| `emulation-support/` | CARLA / OpenCDA вспомогательные файлы. |
| `docker/` | Dockerfile-ы. |
| `tmp/` | Временные данные (gitignored). |
| `archive/` | **Не читать ИИ.** Замороженные тексты ВКР, дубликаты, audit-история. |
| `.venv/`, `.venv_sionna/`, `.venv_docs/` | Python virtualenvs (gitignored). |
| `.bootstrap-ns3/` | Sandboxed ns-3 build (gitignored). |
| `.optix-wsl/` | NVIDIA OptiX runtime (gitignored). |

## Корневые файлы

| Файл | Назначение |
|---|---|
| `README.md` | Описание проекта (от upstream). |
| `AGENTS.md` | Правила для всех ИИ-агентов. |
| `CLAUDE.md` | Указатель на AGENTS.md. |
| `REPO_LAYOUT.md` | Этот файл. |
| `Makefile`, `LICENSE`, `AUTHORS`, `CHANGES.md`, `RELEASE_NOTES.md` | Standard project files (от upstream). |
| `DEVELOPMENT.md` | Разработческие заметки. |
| `adapt_files.py`, `install_carla_opencda.sh`, `enable_v2x_emulator.sh`, `sandbox_builder.sh`, `switch_*.sh` | Operational scripts (от upstream + локальные). |
| `docker-compose.gpu.yml`, `*.cflags`, `*.cxxflags` | Build configs. |

## Куда что класть

| Что | Куда |
|---|---|
| Новый сценарий | `experiments/<name>/{scripts,docs,tools,results}/` |
| Новый прогон evidence | `runs/<YYYY-MM-DD>/<run_dir>/` |
| Новый аналитический скрипт | `tools/{plots,analysis,vkr}/` |
| Учебный/рабочий отчёт | `reports/<name>/` |
| Финальный docx статьи | `conference/` |
| Старая версия / транзишнл / черновик | `archive/<YYYY-MM-DD>/superseded/...` |
EOF
```

---

## Phase 10 — Validation & final commit

### Task 10.1: Acceptance check 1 — old dirs gone

- [ ] **Step 1: Run negative tests**

```bash
cd /home/afetz/work/clean/NEWWAY
for d in valid_scenario valid_intersection_scenario valid_cpm_perception_scenario valid_intersection_radar_comm_scenario my_scenarios scenarios raw_experiments hardwork cycle7_fizulin_av strict_sionna_vkr analysis WORKSPACE_MAP.md codex.md; do
  if [ -e "$d" ]; then echo "FAIL: $d still exists"; else echo "OK: $d gone"; fi
done
```

Expected: every line `OK`.

### Task 10.2: Acceptance check 2 — new dirs present

- [ ] **Step 1: Run positive tests**

```bash
for d in experiments runs reports tools/plots tools/analysis tools/vkr archive/2026-05-03/vkr_manuscript archive/2026-05-03/superseded/conference archive/2026-05-03/audit_history AGENTS.md CLAUDE.md REPO_LAYOUT.md experiments/README.md runs/README.md tools/README.md archive/README.md; do
  if [ -e "$d" ]; then echo "OK: $d"; else echo "FAIL: $d missing"; fi
done
```

Expected: every line `OK`.

### Task 10.3: Acceptance check 3 — bash syntax for all run.sh

- [ ] **Step 1: Run bash -n on every shell script in experiments/, scripts/, tools/scenario_manager/**

```bash
fail=0
for f in $(find experiments scripts tools/scenario_manager -name '*.sh' -type f); do
  if ! bash -n "$f" 2>&1; then echo "FAIL: $f"; fail=1; fi
done
if [ $fail -eq 0 ]; then echo "ALL OK"; fi
```

Expected: `ALL OK`.

### Task 10.4: Acceptance check 4 — Python syntax for all tools/

- [ ] **Step 1: Run ast.parse on every .py in tools/**

```bash
fail=0
for f in $(find tools experiments -name '*.py' -type f); do
  if ! ./.venv/bin/python -c "import ast; ast.parse(open('$f').read())" 2>&1; then echo "FAIL: $f"; fail=1; fi
done
if [ $fail -eq 0 ]; then echo "ALL OK"; fi
```

Expected: `ALL OK`.

### Task 10.5: Acceptance check 5 — no stale path references

- [ ] **Step 1: Grep for old path patterns in all live code**

```bash
echo "=== Checks across live tree (excluding archive/, docs/, .git/) ==="
grep -rln 'analysis/scenario_runs\|analysis/vkr/\|my_scenarios/\|valid_scenario\|valid_intersection_scenario\|valid_cpm_perception_scenario\|valid_intersection_radar_comm_scenario' \
  --include='*.sh' --include='*.py' --include='*.md' \
  experiments/ runs/ tools/ reports/ scripts/ AGENTS.md CLAUDE.md REPO_LAYOUT.md 2>/dev/null
```

Expected: empty output (или только matches в README.md где старые имена упомянуты как «было»).

### Task 10.6: Stage and commit

- [ ] **Step 1: Stage all**

```bash
git add -A
git status --short | wc -l
```

Expected: large number (this is the big reorg).

- [ ] **Step 2: Diff overview**

```bash
git diff --cached --stat | tail -20
git diff --cached --stat | head -3
```

Expected: lots of renames (`R`), new files (`A`), deletions absorbed in renames.

- [ ] **Step 3: Commit**

```bash
git commit -m "$(cat <<'EOF'
chore(repo): reorganize into experiments/runs/tools/reports/archive layout

Single atomic reorg per docs/superpowers/specs/2026-05-03-repo-cleanup-design.md:

- experiments/ — все сценарии под одной крышей (truck_lane_change,
  intersection_crash, intersection_radar_comm, cpm_perception, compare_tech,
  intersection_v2x_awareness, operational, strict_sionna_vkr, raw)
- runs/ — централизованный evidence-стор (бывший analysis/scenario_runs/)
- tools/ — все аналитические скрипты (plots, analysis, vkr)
- reports/ — учебные/рабочие отчёты (cycle7_fizulin_av, web_ui_scenario_manager)
- archive/ — замороженные тексты ВКР, дубликаты, audit-история;
  AGENTS.md явно скрывает её от ИИ
- AGENTS.md / CLAUDE.md / REPO_LAYOUT.md — навигация для людей и ИИ

Path-rewrites внутри run.sh скриптов и tools/ выполнены атомарно вместе с
переездом. WORKSPACE_MAP.md (устаревший) и codex.md (старый) уехали в
archive/2026-05-03/audit_history/.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
git log --oneline -5
```

Expected: new commit on top, two commits visible (snapshot + reorg).

### Task 10.7: Final clean status

- [ ] **Step 1: Verify**

```bash
git status
git log --oneline -5
ls
```

Expected: clean tree, корень содержит только новую структуру.

---

## Out of scope (повтор из спека)

- Build / пересборка ns-3.
- Восстановление ВКР PDF.
- Удаление `.venv*`, `.bootstrap-ns3/` runtime-зон.
- Окончательное удаление файлов — всё уезжает в `archive/`.
