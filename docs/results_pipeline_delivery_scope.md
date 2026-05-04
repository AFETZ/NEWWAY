# Состав поставки results pipeline

Документ фиксирует, что входит в инженерную поставку results pipeline проекта NEWWAY, а что должно оставаться вне коммита.

## Входит в поставку

```text
tools/results_pipeline/
tests/smoke_results_pipeline/
tests/smoke_results_pipeline/data/
docs/
scripts/results_pipeline/
```

## Пользовательский слой

```text
scripts/results_pipeline/README.md
scripts/results_pipeline/scripts/
scripts/results_pipeline/sample_inputs/
scripts/results_pipeline/sample_outputs/
```

Пользовательский слой отделён от внутренней реализации.
Пользователь должен иметь возможность запустить пример обработки без открытия Python-модулей и тестов.

## Developer-слой

```text
tools/results_pipeline/
tests/smoke_results_pipeline/
docs/
docs/
```

Этот слой предназначен для будущих разработчиков, которые будут расширять readers, схемы, метрики, diagnostics, тесты и документацию.

## Не входит в поставку

```text
local_inputs/
tmp/
runs/
большие raw dumps
посторонние ASN1 generated files
экспериментальные черновики
```

Следующие пути нельзя случайно добавлять в staged files в рамках results pipeline:

```text
emulation-support/
src/automotive/model/ASN1/
local_inputs/
tmp/
runs/
```

## Правило коммита

Нельзя использовать:

```powershell
git add .
```

Использовать только selective staging:

```powershell
git add .gitignore
git add tools/results_pipeline
git add tests/smoke_results_pipeline
git add docs
git add scripts/results_pipeline
```

Перед коммитом обязательно проверить:

```powershell
git diff --cached --name-only
```

В staged не должны попасть:

```text
emulation-support/
src/automotive/model/ASN1/
local_inputs/
tmp/
runs/
```
