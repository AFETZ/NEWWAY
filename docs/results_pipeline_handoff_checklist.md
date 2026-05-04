# Developer handoff checklist

Документ фиксирует порядок входа разработчика в results pipeline NEWWAY.

## 1. Открыть репозиторий

```powershell
cd C:\Users\fgrac\projects\NEWWAY-src
```

## 2. Активировать виртуальное окружение

```powershell
.\.venv\Scripts\Activate.ps1
```

Проверка:

```powershell
where.exe python
python --version
python -m pip --version
```

Первым Python должен быть:

```text
.venv\Scripts\python.exe
```

## 3. Проверить ветку

```powershell
git branch --show-current
git status -sb
```

Рабочая developer-ветка:

```text
feature/simu5g-adapter-v0
```

## 4. Запустить тесты

```powershell
python -m pytest .\tests\smoke_results_pipeline -q
```

Ожидаемый результат:

```text
all smoke tests passed
```

## 5. Основные зоны разработки

```text
tools/results_pipeline/                 код pipeline
tools/results_pipeline/readers/         readers/adapters
tests/smoke_results_pipeline/           smoke tests
tests/smoke_results_pipeline/data/      small fixtures
docs/                         input contracts
docs/                         developer docs
scripts/results_pipeline/                               пользовательский слой
results/                                canonical sample outputs
```

## 6. Что нельзя stage-ить

```text
emulation-support/
src/automotive/model/ASN1/
local_inputs/
tmp/
runs/
```

## 7. Перед commit

```powershell
python -m pytest .\tests\smoke_results_pipeline -q
git diff --check -- .\tools\results_pipeline .\tests\smoke_results_pipeline .\docs .\scripts/results_pipeline .\experiments\results_pipeline\results
git diff --cached --name-only
```

## 8. Правило staging

Нельзя использовать:

```powershell
git add .
```

Использовать только selective add:

```powershell
git add .gitignore
git add tools/results_pipeline
git add tests/smoke_results_pipeline
git add docs
git add scripts/results_pipeline
git add experiments/results_pipeline/results/van3twin_sample results/simu5g_sample
```
