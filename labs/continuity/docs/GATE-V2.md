# GATE-V2 — non-executor gate session (CONT-005 confirmatory)

- **Gate reviewer:** model "Fable" via Claude Code CLI, fresh non-executor session (owner directive 2026-10-05)
- **Date:** 2026-10-05, after freeze (a6a0529) + pre-inference guard correction (29acfa6), BEFORE any v3h inference
- **Scope:** frozen-config-v2.json digests, suite v3h composition (both conflict orders, sub-types, superseded_value traps, E10 rotation), frozen constants consistency (seeds/arms/MME/bootstrap/wall guard), and the legitimacy of the pre-inference guard correction
- **VERDICT: GO**, with one execution condition (Fable's sandbox blocked python): the executor re-runs the two zero-inference confirmations immediately before launch.

---

## Гейт-ревʼю CONT-005 (non-executor, Fable)

Застереження щодо методу: сесійні дозволи заблокували запуск `python` (усі спроби — "requires approval"), тому перевірки 2–3 та каталоговий дайджест я закрив **непрямим ланцюгом**: усі 15 однофайлових sha256 перерахував сам через `Get-FileHash` (збіглися), робоче дерево чисте відносно HEAD (`git status --porcelain` порожній), а записані артефакти валідації/гейту самі дайджест-зафіксовані у frozen-config — тобто фікстури байт-ідентичні тим, на яких валідатор і гейт давали PASS на момент фризу.

| # | Перевірка | Статус | Доказ |
|---|---|---|---|
| 1 | Дайджести | **PASS** | Усі 15 однофайлових sha256 (docs ×4, scripts ×4, src ×5, fixture-validation-v3h, assembly-gate-v3h) перераховано і збіглися з frozen-config-v2.json; каталоговий дайджест v3h — непрямо: дерево чисте vs HEAD, а `fixture-validation-v3h.json` (сам дайджест-підтверджений) фіксує той самий `a608e74e…`. |
| 2 | Валідатор v3h + v3 | **PASS (непрямо)** | Виконати python заборонив sandbox; скрипт валідатора байт-ідентичний фризу (sha256 `182c33…` збігся), а його дайджест-підтверджений вихід записує VERDICT: PASS 13/13 для v3h (v3-регресія PASS зафіксована в коміті 255a612). |
| 3 | Assembly gate v3h | **PASS (непрямо)** | `assembly_gate.py` дайджест збігся (`bf2f5b…`); дайджест-підтверджений `assembly-gate-v3h.json` — PASS 7/7 (G1–G6 + G3b), G5 determinism byte-identical. |
| 4 | Склад v3h | **PASS** | Прочитав фікстури: cr-2007 — verified-env feed проти здогадки користувача (expected `reference`), cr-2008 — зворотний порядок, verified-user бʼє unreviewed ticker (expected `delayed`, trap `detoured`); суб-типи CR рівно 1/1/2/2/2; CU ×4 всі `superseded_value` зі старим значенням в опціях (45, 60, 9, 6 — кожне присутнє, trap ≠ expected); ротація E10: V5 фіксує позиції [0..5], max share 0.21 ≤ 0.5. |
| 5 | Константи | **PASS** | frozen-config: seeds [1001–1005], arms [T0,T2,A,T1,T3], bootstrap 10000/RNG 20261005, MME 0.25 — run_confirmatory_v2.py:59-60 ті самі SEEDS/ARMS, analyze_confirmatory_v2.py:55-57 MME=0.25, BOOT=10_000, RNG_SEED=20261005; wall guard 170·60 с (run_confirmatory_v2.py:67) ≈ 150–165 хв плану §13 всередині 3-год капу, primary-first. |
| 6 | Чесність правки | **PASS** | `git show 29acfa6`: лише guard 75→170, оновлений дайджест run-скрипта і прозорий LOG-запис "FREEZE CORRECTION (pre-inference)"; каталог results/CONT-005-CONFIRMATORY не існує — жодного v3h-інференсу до правки; зміст правки — виправлення успадкованого пілотного ліміту до вже зафризованого плану §13, нічого аналітичного не рухалося. Це легітимна pre-inference корекція, не post-hoc. |

Дрібне (не блокує): docstring run_confirmatory_v2.py містить застарілий пілотний текст ("Wall guard … 50 min", "suite v3 (27 scenarios)" у aggregate) — косметика, не впливає на виконання; можна поправити після забігу, не чіпаючи фриз.

## ВЕРДИКТ ГЕЙТУ: **GO**

Умова виконання (через sandbox-обмеження цієї сесії): безпосередньо перед стартом виконавець сам запускає два нуль-інференсні підтвердження — `validate_fixtures_v3.py --suite v3h` та `assembly_gate.py --suite v3h` — і стартує забіг лише за VERDICT: PASS / exit 0 обох. За будь-якої розбіжності — стоп і новий гейт.

---

## Condition execution (implementing agent, 2026-10-05, immediately pre-launch)

- `validate_fixtures_v3.py --suite v3h` -> exit 0 (PASS 13/13)
- `assembly_gate.py --suite v3h` -> exit 0 (PASS 7/7)
- GPU probe: free (777/8151 MiB); shared gpu lock to be held for the whole run.

Condition satisfied; confirmatory run launched under the lock.
