# General Theory of Civilisation Degradation — APP

- **Теория:** `index.html` — общая теория деградации цивилизаций.
- **Код:** `adaptive_pluralism_protocol` — реализация APP
  (Adaptive Pluralism Protocol): иммунная архитектура цивилизации перед
  эпохой AGI.

*«Цель цивилизации — не сохранить себя. Цель цивилизации — сохранить
возможность стать чем-то другим.»*

## Установка

```bash
pip install -e .
```

Зависимостей нет — только стандартная библиотека Python (>= 3.10).

## Быстрый старт

Прогнать пять сценариев песочницы (монолит, плюрал, adaptive,
adaptive vs hostile AGI, мета-тест):

```bash
python examples/run_scenarios.py
# или после установки:
app-sim
```

Запустить демонстрацию ядра APP v5.0:

```bash
python -m adaptive_pluralism_protocol.app_v5
```

## API

```python
from adaptive_pluralism_protocol import (
    run_scenario,
    scenario_report,
    measure_reachability,
)

civ = run_scenario("meta", True, seed=1, hostile_agi=True)
r = scenario_report(civ)
print(r["scenario"], r["crystallized"], r["R"], r["protocol_gen"])
```

Ключевые сущности:

| Компонент | Роль |
|---|---|
| `Institution` / `AGI` | единая иерархия структур; AGI — не особая вершина, а структура с высокой `adaptation_rate` (закон 7) |
| `ReplaceabilityImmunity` | заменяемость: паразитизм, концентрация (`spin_off`), скорость (`MAX_ADAPTATION`) |
| `Protocol` | заменяемый компонент правил; `revise()` переписывает правила, когда они сами стали аттрактором |
| `SelfImmunity` | аудит достижимости каждые 4 пульса; R < порога → протокол себя пересматривает |
| `measure_reachability` | R = измеряемая достижимость: N траекторий × горизонт T, разнообразие живых бассейнов (Simpson) |

## Проверка

```bash
python -m unittest discover -s tests -v
```

Вердикты (seeds 1–5 стабильно): MONOLITH/PLURAL кристаллизуются (R=0),
ADAPTIVE выживает (R≈0.47), ADAPTIVE_H погибает против враждебного AGI
(R=0), META выживает hostile AGI и переписывает свой протокол (R≈0.61).

## Документация

- `docs/SPEC.md` — 12 законов APP и соответствие реализации v5.3.
- Критерий принадлежности кода протоколу: не сходство с прошлой версией,
  а инварианты 12 законов (раздел 4 спецификации).
