# GATE-CONT002 — non-executor gate verdict (FREEZE 5058f83, before any CONT-002 inference)

- **Gate session:** model "Fable" via Claude Code CLI (`claude --model fable -p`), fresh context, non-executor, repo root; python execution EXPLICITLY ALLOWED for this gate (RC-4a/RC-4b made execution part of the gate) — the gate re-hashed all digests, ran all five validator suites, both analyzer self-tests, the live preflight, and a diagnostic on rendered seed 5001. CONT-002 inference level at gate time: **zero**.
- **Date:** 2026-10-07, after FREEZE commit 5058f83, before the pilot.
- **Verdict: GO-with-conditions — condition A BLOCKING (one deterministic false-positive guard in the frozen runner, legally fixable pre-inference per prereg §11).** Condition A was executed the same day (fix + digest refresh + executor diagnostic + FRESH Fable verification: CONDITION-A SATISFIED — appended verbatim below). This file is the frozen gate record.

---

## Raw gate report (Fable, verbatim)

Усі перевірки завершені. Нижче — повний протокол гейту (готовий до дослівного коміту).

---

# GATE-CONT002 — non-executor gate verdict (FREEZE 5058f83, перед пілотом CONT-002)

> Процедурна примітка: гейт виконано на **Fable** (fresh context, non-executor, read-only щодо проіндексованих файлів). Виконання python-скриптів дозволене і виконане: перехеш, 5 прогонів валідатора, 2 self-тести, live preflight-only, 1 діагностичний скрипт на rendered-фікстурах (нуль інференсу експерименту; preflight — лише два прогрівні "ready"-запити, передбачені самою командою гейту). Рівень інференсу CONT-002 на момент гейту = 0 (жодної директорії `cont002-pilot-*`/`cont002-confirmatory-*` не існує). Поточний rev: `5058f83960d5cb0b31b34054dd6ff562eb13025e`, старт — чисте дерево.
> Побічні ефекти сесії гейту: (1) два untracked каталоги `labs/continuity/results/CONT-002-PILOT/selftest-cont002-pilot/` і `.../CONT-002-CONFIRMATORY/selftest-cont002-confirm/` — створені самим `--self-test` заморожених аналізаторів (RC-4b dry-run, синтетика, нуль інференсу); (2) спроби записати консолідований RC-4a-артефакт і тимчасовий хелпер **заблоковані permission-політикою середовища** — зміст артефакту винесено в умову B. Жоден проіндексований файл не змінено (`git status`: лише два untracked results-каталоги).

---

## 1. НЕЗАЛЕЖНИЙ ПЕРЕХЕШ — ✅ 27/27, нуль розходжень

Власний скрипт (hashlib, окрема від маніфеста ітерація) відтворив обидва заморожені рецепти: `rendered_seed_digest` (sha256 конкатенації `json.dumps(scenario, sort_keys=True, ensure_ascii=True)` по сценаріях seed-рендера, сортування за id — run_cont002.py:122–127) і `suite_digest` (relpath-as-posix + bytes, `rglob` sorted — run_cont002.py:130–135); 19 файлових шляхів — прямий sha256 по байтах.

Результат: **`TOTAL frozen=27 computed=27 mismatches=0 extra=[]`** — усі 27 ключів `frozen-config-cont002.json:54–80` збігаються рядок-у-рядок, включно з:
- 7 × `fixtures/v3k_rendered_seed5001..5007` (`c85946dd…`, `71fa06a8…`, `fc4a7ab4…`, `9c044529…`, `f4faf6e9…`, `54b2bbdf…`, `7b01698b…`);
- `fixtures/v3k_suite` = `06b897f6e727…`;
- обидва аналізатори (`80b14d7d…`, `19b3d1ed…`), runner-скрипт (`6eb7913a…`), пререєстрація (`9c7e80cb…`), 6 src-модулів.

Піни маніфеста звірені з кодом: seeds pilot {5001,5002} / confirmatory {5003..5007} (frozen-config:6–16 = run_cont002.py:89–90); core A `granite-code:8b`/`36c3c3b9683b`, core B `qwen36-35b-a3b:mdlslab`/`8a0fd5da454e` (frozen-config:19–26 = run_cont002.py:93–96); ollama prefix `0.34` (frozen-config:29 = run_cont002.py:97); wall_guard 18000 s / cap 19800 s (frozen-config:45–46 = run_cont002.py:105, 189); budget per cell 120/400 000/5400 (frozen-config:47–51 = run_cont002.py:106).

## 2. RC-4a — ✅ усі 5 сюїт VERDICT: PASS, exit 0; артефакт → умова B

Виконано в цій сесії гейту (не executor-логом):

```
python labs/continuity/experiments/suite-v3/validate_fixtures_v3.py --suite v3    → VERDICT: PASS (14 чеків, V14 skipped pre-v3i)
python labs/continuity/experiments/suite-v3/validate_fixtures_v3.py --suite v3h   → VERDICT: PASS (14 чеків)
python labs/continuity/experiments/suite-v3/validate_fixtures_v3.py --suite v3i   → VERDICT: PASS (17 чеків, 135 інстансів)
python labs/continuity/experiments/suite-v3/validate_fixtures_v3.py --suite v3j   → VERDICT: PASS (17 чеків, 135 інстансів)
python labs/continuity/experiments/suite-v3/validate_fixtures_v3.py --suite v3k   → VERDICT: PASS (17 чеків, 18 сценаріїв × 7 seeds = 126 інстансів; V8R чистий; V15 identical-share 0.0; V16 ротація чиста)
```

Усі exit 0, жодного `[FAIL]`. Заморожені `fixture-validation-*.json` не торкалися. Запис нового консолідованого артефакта `fixture-validation-regressions-post-v3k.json` (пререг §12(a), рядки 299–307) **заблоковано правами запису цієї сесії** — зміст і команди зафіксовані тут, коміт артефакта = умова B.

## 3. RC-4b — ✅ self-тести PASS; код аналізаторів = §2/§4–§6 з двома консервативними нотатками

Виконання:
```
python labs/continuity/experiments/suite-v3/analyze_pilot_cont002.py --self-test
  SELF-TEST PASS: GO case (dA 0.6, B invalid 0.1, no re-derivation)
  SELF-TEST PASS: NO-GO case (dA 1/3 -> crit3 fail + upward re-derivation to 0.5)
python labs/continuity/experiments/suite-v3/analyze_confirmatory_cont002.py --self-test
  SELF-TEST PASS: known R~0.5 -> RETENTION-ESTABLISHED (dA 0.7619, R 0.4, CI [0.2588, 0.5455])
  SELF-TEST PASS: dB=0 -> NULL branch
  SELF-TEST PASS: dA~0 -> NON-ESTIMABLE + per-family ratios withheld
```
2 PASS і 3 PASS відповідно, з очікуваними гілками.

Построкова звірка коду проти преріги:

| Пункт | Статус | Доказ |
|---|---|---|
| (a) ratio-of-means, спільні ресемпл-індекси | ✅ | один `idx` на дро живить і `da_stars`, і `db_stars` (analyze_confirmatory:129–133); R точково = `db/da` з кластерних середніх (125, 146); R* подрово = `db*/da*` (141); метод задекларований у записі "cluster percentile, ratio of means, shared indices" (184). Жодного mean-of-ratios. B=10 000, RNG seed 20261007 заморожений (53–54) = §4 "RNG seed recorded at freeze" |
| (b) estimability gate | ✅ | `gate_point = da >= 0.30` (DA_MIN=0.30, рядок 52) AND `gate_ci` = CI(dA) виключає 0 двобічно (138–139, 175–176); провал → гілка NON-ESTIMABLE з дослівним §6-формулюванням (153, 59–60) |
| (c) нестабільний знаменник | ✅* | `unstable_share = частка дро з \|dA*\| <= 0.05` (142), поріг >0.10 (143, 56–57); прапор у записі R (181–182). *Нотатка: код при unstable видає окрему гілку UNSTABLE-DENOMINATOR (154–157), що блокує не лише "established", а й below-MME/harm/null; §4 дослівно забороняє лише "established". Відхилення строго консервативне (утримує більше тверджень, ніж вимагалось) — зафіксоване, не блокує |
| (d) RC-2 per-family R | ✅ | `if main["gate"]["passed"] and not …unstable…` → лише тоді `R_delayed_recall`/`R_distractor_recall` (193–199); інакше явний рядок "NOT COMPUTED — … RC-2: no ratios in this branch" (200–202); дельта-таблиці per-cluster завжди (`out["per_cluster"] = rows`, 192). Self-тест 3 підтверджує утримання наживо. Додаткове "and not unstable" — знову консервативніше за букву §8, зафіксовано |
| (e) N-4 дро з ΔA*=0 | ✅ | `nonfinite` лічильник дро з `d == 0.0` (140), записаний у `R.nonfinite_draws` (183); `r_stars` будується лише з `d != 0.0` (141), перцентилі — по `len(r_stars)` (144–145), тобто виключені з перцентилів І пораховані — дослівно §4 п.2 |
| (f) формула MME-re-derivation | ✅ | analyze_pilot:148–149: `if da < 0.60: mme = max(0.25, max(0.15, 2*band_max)/da)` — точно `R_MME' = max(0.25, max(0.15, 2×band_max)/ΔA_measured)` з §5:170–172; зовнішній max(0.25, …) гарантує ТІЛЬКИ вгору (`upward_only_ok`, 156); `da <= 0` → `inf` (fail-closed вгору); тригер строго `< 0.60` = §3-драбина (self-тест: dA=0.6 НЕ тригерить — 285). Драбина 0.30/0.45/0.60 = константи 44–46 = §2 крит.3 |
| (g) RC-5 invalid-share | ✅ | `observed_label is None` = нуль або >1 відмінний standalone-label під extract_label (analyze_pilot:83–86, докстрінг 11–14, поле definition у записі 182) = заморожене визначення §2 крит.1; знаменник 15×2=30 на клітину (K_PRIMARY*2, 117, 122); поріг <0.30 на ОБОХ B-клітинах (126); порожній список → 1.0 fail-closed (84–85) |

Решта пілотних критеріїв: крит.2 — екстраполяція на 7 seeds проти cap 19800 s, GC-B-трим = 3 seed-середні GC-B (52, 135–139), N-3 worst-case задекларований у записі (191–193); крит.4 — sd репортується, стрес-прапор sd>0.25 → owner-signoff-рядок, не гейт (160–171, 206–210); carried N-1/N-2 в обох записах (222–226; 226–234).

Дві не-блокуючі технічні нотатки: (i) операціоналізація guess-band = |частка position-0 − 1/6| ідентична в обох заморожених скриптах (analyze_pilot:93–99; analyze_confirmatory:218–224) — §5 формулу не деталізує, визначення заморожене до інференсу, конфлікту немає; (ii) `verdict()` впаде з TypeError (а не чистим INCOMPLETE), якщо в якогось кластера повністю відсутня клітина (`None` у `da_c` на рядку 123–125) — fail-closed збій без хибного вердикту, прийнятно.

## 4. RUNNER — live preflight ✅; виявлено ОДИН БЛОКУЮЧИЙ ДЕФЕКТ (умова A)

Виконано наживо:
```
python labs/continuity/experiments/suite-v3/run_cont002.py --stage pilot --preflight-only
  freeze digests verified (byte-match) — preflight ok
  ollama_version 0.34.2 (prefix_ok true); обидва піни дайджестів пройшли (granite 36c3c3b9683b, qwen 8a0fd5da454e)
  warmup_s: granite 8.5, qwen 27.6
  PREFLIGHT-ONLY OK (no inference performed)
```

| Пункт | Статус | Доказ |
|---|---|---|
| (a) порядок клітин = §13 | ✅ | `CELL_ORDER = [learn-A, A-restored, A-clean, B-restored, B-clean, GC-A, GC-B]` (108–110) = §13:329–330 = frozen-config:32–40 |
| (b) симетрія: один export-файл в обидві restored | ✅ механіка / ❌ guard | один `export_path = out_root/learn-A/seed-<n>/state-export.json` на seed (391) передається всім клітинам; обидві restored: `assert export_path.exists()` + `import_dict(…, require_empty=True)` (286–290); sha256 export-а в cells.json (425–428). **АЛЕ сам state-integrity assert — хибнопозитивний, див. дефект Д-1 нижче** |
| (c) clean-клітини зі звірено порожнього store | ✅ | `assert memory.count() == 0, "clean cell must start from a verified-empty store"` (291–292); store — свіжий файл у новій attempt-директорії (274) |
| (d) wall guard 300 хв / cap 330 | ✅ | `WALL_GUARD_S = 300*60` (105), перевірка перед стартом КОЖНОЇ клітини (393–397, прапор `wall_guard_fired`); declared cap `330*60` = frozen-config:46 |
| (e) resume: completed summary → skip | ✅ у межах інвокації / ⚠ між інвокаціями | `cell_complete()` читає `summary.json.completed` (341–348), у циклі спроб — скіп без інференсу (400–402); спроби в окремих `seed-<n>-a<k>` директоріях, зберігаються як докази (403–414). **Обмеження:** `out_root` містить timestamp (373–376) і CLI не має аргументу вказати існуючий корінь → крах самого процесу між клітинами = повний новий прогін з повторним інференсом. → умова D |
| (f) digest-preflight до будь-якого інференсу | ✅ | `preflight()` першим рядком викликає `verify_freeze_digests()` fail-closed (217–218, 199–210); `main()` викликає preflight (378) до будь-якого `run_cell`; перевіряються suite digest + всі 7 rendered digests (142–145, 205–209) |
| (g) CN-001 warm-then-pin | ✅ | коментар + код 232–244: спершу warm-chat "ready", ПОТІМ `model_info()` і звірка префікса дайджеста, fail-closed, для обох ядер |

### ❌ Д-1 (БЛОКУЮЧИЙ): state-integrity guard детерміновано вбиває learn-A хибним спрацюванням

`run_cont002.py:304–308` порівнює **голі цілі індекси сесій** без прив'язки до сценарію:
```python
sessions_in_export = {ep.get("session") for ep in data.get("episodes", [])}
probe_sessions = {scenario_parts(s)[1]["index"] for s in scenarios}
assert not (sessions_in_export & probe_sessions), ...
```
Факти, кожен перевірений:
1. `scenarios` в learn-A — це ВСІ 18 сценаріїв, включно з GC (`plan = [... for s in scenarios]`, 280–281; докстрінг рядка 8 каже "every primary scenario" — код не фільтрує).
2. У v3k primary-сценарії мають сесії [1,2,3] (probe=3), а GC — [1,2] (probe=**2**) — перевірено на rendered seed 5001 (dr-5301/dx-5401: [1,2,3]; gc-5501/02/03: [1,2]).
3. Arm B записує епізоди з КОЖНОГО ходу learning-сесій з цілим `session=index` (runner.py:401–405; схема `session INTEGER`, memory.py:46; export віддає його як є, memory.py:202).
4. Отже export learn-A гарантовано містить епізоди з `session=2` (s2 primary), а `probe_sessions = {3, 2}` (2 — від GC). Діагностичний прогін на rendered seed 5001: **`INTERSECTION: [2] -> state-integrity assert FIRES: True`**.

Наслідок: AssertionError на learn-A у кожній з 3 спроб (детерміновано, до запису export-а — 307 перед 309), обидві restored-клітини падають на "export missing", прогін спалює GPU-час на clean/GC-клітинах і завершується без жодних restored-даних → вердикт "incomplete". Fail-closed (хибного результату не буде), але експеримент неможливий. Сам намір guard-а (§7:206–209 — нуль probe-контенту в export-і) кодом НЕ порушується: у export потрапляють лише learning-сесії; дефект — у нескваліфікованому порівнянні індексів.

Шлях виправлення легальний: §11:273–275 явно дозволяє фікси "run-script wiring" ДО будь-якого інференсу ураженої стадії, same-commit LOG + digest refresh. Інференсу стадії не було (рівень 0). → умова A.

### ⚠ Д-2 (суміжний, той самий корінь): GC-сценарії беруть участь у learn-A і в чотирьох probe-клітинах

Плани learn-A (280–281) і probe-клітин (282–283) не фільтрують по сім'ї: GC s1 потрапляє в export, а GC probe-сесії виконуються в A/B-restored/clean. Аналітично нешкідливо (retrieval строго same-scenario — runner.py:279–280, 337; аналізатори фільтрують `family != guess_calibration` у primary-клітинах і читають GC лише з GC-A/GC-B директорій), але це відхилення від §1–§2 (GC "measured clean on BOTH cores" лише у GC-клітинах) і зайвий B-side інференс (~9 ходів/клітину-seed), який крит.2 поміряє чесно. Вирішити в тому ж комміті, що й Д-1 (фільтр до primary-сімей), або явно задокументувати в LOG як прийняте — рішення виконавця/власника, зафіксоване.

### ⚠ Д-3 (косметичний): `stopped`-маркер мертвий
`run_cont002.py:324`: `"stopped": any(p.get("stopped") for p in [{}]) or False` — завжди False; "stopped marker" з докстрінга (50) ніколи не спрацює. Реальна інформація йде через `budget_violation` (325) + completeness guard на етапі аналізу. Не блокує; НЕ виправляти після інференсу (протокол), можна в комміті умови A з LOG-рядком.

## 5. CORE-NEUTRALITY + FOUR-CELL WIRING — ✅

- **Жодних посилань на ядра у фікстурах:** grep `granite|qwen|core|model|ollama` по `fixtures/v3k/` — єдине влучання — опис у `manifest.json:23` ("Suite v3k for CONT-002 (state transfer across cores…)" — метаопис протоколу, не текст сценарію; у `sessions`/`variants` жодного влучання.
- **Рендер пам'яті — одна arm-B машинерія для обох ядер:** `format_memory_block` (runner.py:83) і фіксоване правило ін'єкції (71–78) не мають жодної моделе-умовної гілки; всі 7 клітин викликають `run_scenario(…, arm="B", memory=…)` (run_cont002.py:296) — байт-ідентичний пайплайн, §1 "byte-identical pipeline across cells and cores".
- **Вибіркова перевірка (3 файли):** `dr-5301` — s1 факт (haul motor code) + нейтральний companion ("duty kettle whistles at six"), s2 рутина, s3 held-out label-form probe, 6 опцій, expected у labels; `dx-5404` — s1 факт+lure (lure `T43` присутній у labels probe-а, ≠ expected `S21`), s2 рутина, s3 probe; `gc-5502` — 2 сесії, 2 never-stated probes без `expected` (null). Companion/lure факти — побутові предмети (kettle, lamp, rack codes), нульова асоціація з будь-яким ядром. Систематично це ж покриває V8R/V6/V9 валідатора (PASS, §2 цього звіту).
- Probe = остання сесія скрізь (`scenario_parts`, run_cont002.py:259–261), learning = всі попередні — відповідає §1 "s1+s2 learning, s3 held-out".

---

## ВЕРДИКТ: **GO-with-conditions** — умова A БЛОКУЮЧА (жодного інференсу до її виконання)

**A (блокуюча — виправлення Д-1 перед будь-яким інференсом, §11 "run-script wiring", інференс стадії = 0):**
1. У `run_cont002.py:304–308` скваліфікувати порівняння парами `(scenario_id, session_index)`: export-епізоди несуть поле `scenario` (memory.py:57) — порівнювати `{(ep["scenario"], ep["session"])}` проти `{(s["id"], scenario_parts(s)[1]["index"]) for s in scenarios}`. У тому ж комміті вирішити Д-2 (відфільтрувати плани learn-A і probe-клітин до primary-сімей, або LOG-рядок про свідоме прийняття) і, за бажанням, Д-3.
2. Same-commit: LOG-entry + оновлення дайджеста `experiments/suite-v3/run_cont002.py` у `frozen-config-cont002.json` (§11; манifest не входить у власний перелік дайджестів).
3. Після фіксу, перед інференсом, виконати і залучити у run-record:
   - `python labs/continuity/experiments/suite-v3/run_cont002.py --stage pilot --preflight-only` → має завершитись `PREFLIGHT-ONLY OK`;
   - повторний перехеш 27 дайджестів (рецепт §1 цього звіту) → 27/27;
   - fresh non-executor перевірка зміненого guard-а (мінімум: діагностичний скрипт цього гейту на rendered seed 5001 → `assert fires: False` для нової логіки, плюс підтвердження, що probe-пари, як і раніше, виключаються).

**B:** закомітити разом із цим протоколом консолідований RC-4a-артефакт `labs/continuity/experiments/suite-v3/fixture-validation-regressions-post-v3k.json` (запис цієї сесії заблокований правами): 5 сюїт × команда з §2, усі `VERDICT: PASS`, exit 0, `overall: PASS`, з приміткою "gate-session re-run; frozen per-suite records untouched". Заморожені `fixture-validation-*.json` не чіпати.

**C (прецедент GATE-V3B умова A, префлайт виконавця):** безпосередньо перед КОЖНИМ інференс-стартом (пілот і confirmatory окремо): `--preflight-only` (вбудований fail-closed ланцюг digests→tags→warm→pin уже інституціоналізований) + `python …/analyze_pilot_cont002.py --self-test` і `python …/analyze_confirmatory_cont002.py --self-test` → 2 PASS / 3 PASS.

**D:** якщо прогін обірветься між клітинами — НЕ перезапускати наосліп: CLI не має cross-invocation resume (нова timestamp-директорія = повторний інференс завершених клітин, всупереч PB-075-наміру). Додавання `--resume-root`-аргументу підпадає під §11 "path/argument prefixes" hotfix-клас (LOG + digest refresh); альтернатива — консультація non-executor гейту перед повтором.

**E:** у run-record header — N-1/N-2 carried notes (вже зашиті в обидва аналізатори), точні revs виконання і лічильники спроб (§11), двоє untracked selftest-каталогів цього гейту (зберегти як докази або видалити — зафіксувати рішення), і консервативні відхилення §3 цього звіту (unstable-гілка блокує всі вердикт-гілки; per-family R утримується також при unstable) — повторити в підсумковому записі.

**Підсумок одним рядком:** FREEZE цілісний (27/27 дайджестів, 5/5 валідаторів PASS, self-тести PASS, live preflight PASS, core-neutrality чиста), але заморожений runner містить один детермінований хибнопозитивний guard (Д-1), легально виправний до інференсу за §11 — **GO-with-conditions: інференс дозволений лише після виконання умови A; умови B–E супроводжують виконання.**

---

## Condition-A verification (fresh Fable session, verbatim)

## ВЕРДИКТ: CONDITION-A SATISFIED

**Докази по пунктах:**

**1) Diff реалізує точно призначене.**
- **Д-1 (пари):** guard тепер порівнює `export_pairs = {(ep.scenario, ep.session)}` проти `probe_pairs = {(s["id"], probe_index)}` лише для не-GC сімей (`run_cont002.py:313-318`). Зіставність пар підтверджена кодом: епізоди реально несуть `scenario`=s["id"] і `session`=session["index"] (`memory.py:199-202`, `runner.py:407-410`), і learn-A передає оригінальні session-дикти, тож індекси не перенумеровуються.
- **Д-2 (фільтр планів):** learn-A та чотири probe-клітини фільтрують `family != "guess_calibration"`; GC-клітини — тільки GC-сценарії, з LOG-коментарем з посиланням на prereg section 2 і «GATE-CONT002 D-2 fix» (`run_cont002.py:281-288`).
- **Д-3 (stopped):** мертвий вираз `any(... for p in [{}]) or False` замінено на реальний акумулятор `stopped_any` по результатах `run_scenario` (`run_cont002.py:297-301, 334`).

**2) Діагностика на rendered seed 5001** (18 сценаріїв: 15 primary, 3 GC):
- Нова логіка: 30 export-пар (learning-сесії primary) ∩ 15 probe-пар = **∅** — assert не спрацьовує.
- Підтверджено сенс фіксу: стара логіка голих індексів давала детермінований хибний спрацьовувач — GC-probe на індексі **2** збігається з primary learning-індексами **{1, 2}**.
- Негативний контроль: ін'єктована probe-пара `('dr-5301', 3)` — **ЛОВИТЬСЯ** (перетин рівно {victim}).

**3) Дайджест:** sha256 поточного `run_cont002.py` = `c4f7e31b…d0e05f` — **збігається** з полем у перегенерованому `frozen-config-cont002.json` (created_utc 19:55:47Z, тобто після фіксу 19:44:16Z). Контрольний прохід по всіх інших file-дайджестах маніфесту: mismatch — none.

**Примітки (не блокери):** (а) git попереджає про LF→CRLF normalization для `run_cont002.py` — дайджест рахований по поточних LF-байтах; якщо checkout колись нормалізує закінчення рядків, preflight впаде fail-closed (безпечна поведінка, але варто знати); (б) untracked `fixture-validation-regressions-post-v3k.json` у робочій директорії — поза скоупом умови A; (в) вимога «same-commit LOG + digest refresh» щодо LOG виконана на рівні коду (коментарі D-1/D-2 fix у самому файлі) — чи потрібен окремий запис у LOG-документ, вирішує гейт, не ця перевірка.

---

## Executor record of condition execution

| Condition | Execution |
| --- | --- |
| A (blocking) | run_cont002.py fixed: guard qualified by (scenario, session) pairs (D-1); learn-A and the four probe-cell plans filtered to primary families, GC only in GC cells per prereg §2 (D-2); stopped-marker accumulator (D-3). Freeze manifest re-emitted (run_cont002.py digest c4f7e31b…; 27 digests). Executor diagnostic on rendered seed 5001: intersection empty, negative control caught. Preflight-only PASS post-fix. Fresh non-executor verification (above): CONDITION-A SATISFIED, incl. an independent manifest re-hash with zero mismatches. |
| B | `fixture-validation-regressions-post-v3k.json` committed with this protocol (5 suites PASS, overall PASS; provenance records the gate-session runs + the executor re-run at this commit; frozen per-suite JSONs untouched). |
| C | Executes at every inference start (the run script's built-in fail-closed preflight + the two analyzer self-tests are run immediately before each stage launch; recorded in the run record). |
| D | Noted: no cross-invocation resume in the CLI; if a run breaks between cells, `--resume-root` (§11 path/argument hotfix class, LOG + digest refresh) or a non-executor consult — never a blind re-run. |
| E | Run-record header obligations: N-1/N-2 carried notes (embedded in both analyzers), exact revs + attempt counts, conservative deviations restated (unstable-denominator branch blocks ALL verdict branches; per-family R also withheld when unstable), gate selftest dirs decision: DELETED (regenerable via --self-test; outputs preserved verbatim in this protocol). |

**Post-condition verdict: GO — the pilot may start** (seeds {5001, 5002}, declared cell order, ~45–85 min GPU under the shared lock; then ONLY the frozen analyze_pilot_cont002.py; the pilot-gate checkpoint outputs go to the owner if any action fires).
