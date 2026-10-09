<!--
PROVENANCE: independent reviewer = Fable (claude --model fable -p, stdin
invocation, no --allowedTools — doc/code-level review by reading; declared
no python/inference run). RC-6 chain step 2 of 4. Launched by the
implementing agent (ZCode) 2026-10-09 from the repo root with a
self-contained Ukrainian prompt covering: the V2 package, the self-review
SR-1..SR-9 folds, the RC-6 direct-trace-inspection mandate, the invalid-run
trace path, v3m/bundles/recap artifacts, and the honest declarations.
Raw output below is VERBATIM (16,276 chars); curation appendix follows.
Model-substitution rule: queue Fable -> Opus -> GLM 5.3 Flash; Fable was
available (probe answered; no limit block).
-->

# Незалежне рев'ю V2-пакета (RC-6, крок 2/4) — Fable, 2026-10-09

Read-only, документно-кодове; жодного python/інференсу. Усі числа нижче перевірені мною напряму (Grep-цензуси по трейсу, читання фікстур/артефактів), окрім явно позначених як цитовані.

**Вердикт одразу: GO-with-changes.** Пакет суттєво сильніший за V1, усі мої F-1..F-3 та більшість C/D-знахідок сфолджені чесно і механічно. Але я знайшов п'ять нових дефектів — три з них саме того класу, який цей пакет мав убити (задекларовано-але-не-механічно), і два з них сидять в артефактах, що йдуть у freeze manifest. Усі п'ять — zero-GPU фікси до фризу.

---

## 1. Пряма верифікація (вимога RC-6)

**Трейс інвалідного рана R2/seed-6003 — цензус мій власний:**
- `memory.append`: **0** ✔
- `memory.injected`: **35**, із них з `injected: true` — **0**, з `episode_count` ≠ 0 — **0** (зразковий рядок: `episode_count: 0, episode_ids: [], injected: false`) ✔
- `lessons.injected`: **53**, із них з `injected: false` — **0** (тобто всі true, з резолвнутими lesson_ids) ✔
- summary.json: `completed: true`, `memory_episodes: 0`, `probes_passed: 3/21` ✔

Сигнатура CN-012 підтверджена незалежно і збігається з self-review §A дослівно. Гейт її ловить трьома чеками одночасно (T1 нуль append-ів; T2 жодної непорожньої ін'єкції; T5 completed-summary з 0 епізодів) — FAIL-CLOSED семантика проти цього трейса реальна, не декларативна.

**v3m (cu-7101):** структура свіжа, механіка успадкована (superseded_value, probe-in-last-session, 7 сідових варіантів з old/new/options), validator-файл `fixture-validation-v3m.json` → PASS. **Але див. знахідку К-2 — «свіжість світів» порушена.**

**Бандл cr-FP3a-vce:** 12 scenario-runs з 12 різних трейсів ✔, fails-first ✔, 5-частинні refs у заголовках ✔. **Але всі 12 — це ОДИН сценарій cr-4001** (12 арм-сідових повторів), нуль сценарійної різноманітності всередині бандла — див. К-1.

---

## 2. КРИТИЧНЕ (RC-обов'язкові зміни до фризу)

**К-1. Бандл-групування cr НЕ відповідає sub_type фікстур — пріга A.4 / DESIGN-V2 §3 («grouped by family/sub-type») фактично хибні для cr.**
`worker_v2_bundles.py:37-47` групує за суфіксом id, але реальні sub_type у v3i/v3j інші: cr-x003 — це `valid_correction_environment` (FP-3a), а не euc; справжні euc — cr-x004/x005. Наслідки, перевірені по самому `worker_v2_bundles.json`:
- бандл **cr-FP3b-euc** містить ВИКЛЮЧНО cr-4003/cr-3003, усі з `class=FP-3a` — бандл з ім'ям «erroneous_user_correction» не містить жодного euc-сценарію;
- бандл **cr-FP3b-sc** — суміш euc (cr-4004/4005, FP-3b) + sc + retraction (cr-4008, **FP-1**) з лише 3 трейсів;
- бандл **cr-FP3a-vce** пропускає vce-сценарії cr-x003 і виродився у 12 повторів одного cr-4001.
Іронія: код ЧИТАЄ sub_type (`_scenario_classes()`), пише правильний class у кожен digest-рядок — і не використовує його для групування. Фікс: групувати за фактичним sub_type з фікстур, регенерувати артефакт, перерахувати n_traces, оновити декларації. Це freeze-артефакт — виправляти зараз, не після owner accept.

**К-2. «Fresh worlds» v3m — задекларовано, не механізовано, і фактично порушено, зокрема проти v3l.**
- **cu-7104** («pottery workshop… glaze kiln holds {old} shelves») — той самий світ, що **v3l cu-6102** («pottery kiln room… glaze load soaks {old} hours»): pottery+kiln+glaze, та сама сім'я CU, та сама correct-the-value механіка. v3l — саме та поверхня, відмежування від якої було суттю C.6 (гейти V2 калібрувалися знаючи покластерні v3l-результати).
- **cu-7101** («You keep the planetarium notes…») — той самий світ і та сама вступна фраза, що **v3h cu-2001** («You keep the planetarium notes…»).
- Валідаторна «дизджойнтність» — лише exact-turn-text рівність (`shared turn texts 0`); світову свіжість ніхто механічно не перевіряє.
Це робить хибним і рядок мого мандата, і self-review §A («fresh world (planetarium)» — ні). Фікс: owner-рішення — або пере-світити колізійні сценарії (день роботи по білдеру), або чесний амендмент A.1 («свіжі ТЕКСТИ, світи можуть повторюватись» — я б НЕ радив для cu-7104-проти-v3l) — плюс у будь-якому разі механічний world/n-gram чек у валідатор, щоб властивість перестала бути прозовою.

**К-3. FP-6 cap обходиться незатегованим або хибно затегованим уроком.**
`reflection_v2.py:473-478`: невалідний/відсутній `class` → `cls=""`, лічильник `untagged_or_invalid_class` інкрементиться — і кандидат **далі йде у validate_candidate та може бути accepted**; `lesson_class("")≠"FP-6"` → cap його не бачить. Клас — самодекларація воркера у промпті; «mechanically apply_class_cap» (A.4) механічний лише НАД цією самодекларацією. Формат-урок без тега (або з тегом FP-2) легально обійде cap — рівно той сценарій, через який у інвалідному сторі жили три формат-близнюки. Фікс (fail-closed, у дусі всієї лабораторії): кандидат без валідного class = rejected як schema violation (промпт його вимагає явно), або щонайменше предекларований гейт «untagged_or_invalid_class > 0 → стор не фризиться без ад'юдикації». Задекларувати чесно: cap механічний, класифікація — модельна.

**К-4. Смоук НЕ покриває R1 (і RGOLD) — DESIGN-V2 §2 («every memory arm») хибний, мій C.5-ассерт не існує.**
`combined_channel_smoke.py:66-67`: арми — R0/R2/R3/RBAD. Мій C.5 прямо просив смоук-assert на ненульові епізод-деривовані reflection-саммарі R1 (щоб відрізняти A.2-режим «рефлексія без епізодів» від повного) — його немає; R1 знову єдина арма, чий ключовий шлях ніколи не вправлявся офлайн до GPU. Self-review §B чесно пише «R0/R2/R3/RBAD», але не помічає розриву з «every memory arm» у власному дизайн-документі. Фікс: додати R1 (із selfmodel-плумбінгом) + RGOLD, assert на episode-derived reflection-шлях.

**К-5. Новий гейт сам містить два doc-code розриви класу RC-4 (той самий клас, що SR-5 щойно виправляв у T5).**
- **T2 «resolves to an APPEND committed EARLIER»** (`live_telemetry_gate.py:63-71`): код перевіряє членство в множині ВСІХ append-ів трейса — без порядкової перевірки. Ін'єкція, чий реф резолвиться у ПІЗНІШИЙ append, пройде. Фікс: порівняння seq (append.seq < injection.seq). Заодно: docstring обіцяє «at session >= 2», код сесію не перевіряє.
- **T3 «non-lesson arms show ZERO lessons.\* events»**: код дивиться лише `lessons.injected`, а runner емітить ще `lessons.retrieve/render/digest/status` (runner.py:350-371 — перевірено). Не-lesson арма з lessons.retrieve-подіями пройде гейт. Фікс: `e["type"].startswith("lessons.")` для заборонної гілки.
Обидва фікси — по рядку; але залишати їх у ГЕЙТІ, чия легітимність — «код робить рівно те, що каже docstring», не можна.

---

## 3. Бажане (не блокує крок 3, але варто до фризу)

- **Б-1.** Формулювання cap-правила: prereg A.4 каже «keep-first by lessonId among FP-6», а `apply_class_cap` — keep-first за порядком списку. Для R3 це збігається (r3-candidates.json у lessonId-порядку — перевірено), для R2 порядок = порядок акцепту, і воркер МОЖЕ подати власний lessonId (`les.get("lessonId") or …`), що розірве еквівалентність. Узгодити текст із кодом (чесніше: «keep-first in acceptance order»).
- **Б-2.** T4 мовчки пропускає agent.response без usage (default 0); дрібниця, але default має бути fail, не pass.
- **Б-3.** `NUM_CTX=4096` у гейті захардкоджено (SR-7 перевірив збіг СЬОГОДНІ) — імпортувати константу з провайдера/ранера, щоб збіг був структурним.
- **Б-4.** Дубль digest-логіки та `_scenario_classes` між reflection_v2 (V1) і worker_v2_bundles з різними ширинами абревіації (14/12, 10/8 слів). V1 заморожений як record — ок, але перехресний коментар обов'язковий, бо це знову паралельні копії.
- **Б-5.** Fails-first сортування `(failed, prefix, sid)` дає бандли з одного сценарію (К-1 наслідок); після фіксу групування додати tie-break на сценарійну різноманітність.
- **Б-6.** Мертвий ключ `scripted_agent_answer` у CR_SUBTYPE_CLASS (rt-сценарії мають `scripted_own_answer` і йдуть через FAMILY_CLASS) — ніколи не метчиться; прибрати або задокументувати.
- **Б-7.** Питання до кроку 3: чи Phase V layout (арми/сіди активаційної фази) сумісний із гейтовим глобом `*/seed-*` — «every phase's traces pass the gate» має бути перевірене на V-лейауті до фризу, хоча б self-test-ом.

---

## 4. Оцінка SR-1..SR-9

| SR | Оцінка |
|---|---|
| SR-1 | ✔ Підтверджено: `module.__qualname__` у arm_equivalence_audit.py:69-70 |
| SR-2 | ✔ Механіка існує (schema/cap/coverage у src) — але з дірою К-3 |
| SR-2b | ✔ gold-lesson-classes.json ↔ recap_r3_v2.py ↔ r3-store-v2.json (7 уроків, sha 48064a02…, LL-G-008 → accepted_then_capped) — узгоджені; анотація LL-G-008 як FP-6 обґрунтована операційним визначенням, спірність чесно задекларована |
| SR-3 | ✔ run_worker_v2 існує; шаблон — single source у src; worker_v2_bundles імпортує bundle_prompt; мертвого prompt_for немає |
| SR-4 | ✔ Обидва доки тепер несуть канонічний порядок (worker → recap → contamination → calibration → V) |
| SR-5 | **Частково**: T5-рівність і --self-test у обох напрямках ✔, але T2/T3 розриви (К-5) — фолд не довів клас до кінця у самому гейті |
| SR-6 | ✔ assert у runner.py:216 |
| SR-7/8/9 | ✔ (power-артефакт називає v3m; 4-gram скан охоплює v3l+v3m×14 сідів — перевірено в коді скрипта) |

## 5. Мапа моїх full-arc знахідок → фіксів

F-1/F-2 ✔ (MEMORY_ARMS runner.py:87 + guard-імпорт run_cont006.py:311 — перевірено кодом). F-3 ✔ (A.3.2 halt-семантика + S0-чек у A.6). C.1 ✔ (A.3.1, обидві арми). C.2 ✔ MME 0.20/caveat-only band — рівно моя перша опція; контекст-смоук — частково (К-4). C.3 → реалізовано з дефектом К-1. C.4 → реалізовано з дірою К-3. C.5 → R1 лишається ✔, але смоук-ассерт відсутній (К-4). C.6 → v3m існує, але К-2. D.3.8 ✔ з К-5. D.4 ✔ (пілот з пам'яттю, 2 сіди, тепер у можливій позиції ланцюга).

## 6. Чесність декларацій D/E

Загалом — висока: run_worker_v2-без-провайдера, крос-сюітність анкера 0.525 з halt-семантикою, implementer-judged анотація, непокритий acknowledgment-підклас — усе назване прямо. Єдина фактична хиба: «fresh world (planetarium)» у §A (К-2). Окремо відзначу, що self-review знайшов SR-2/SR-3 (неіснуючий cap і неіснуючий executor) сам — це той рівень безжальності до себе, якого V1-ланцюгу бракувало.

## 7. Рішення

**GO-with-changes.** RC-обов'язкові перед кроком 3 (усі zero-GPU):

1. Перегрупувати cr-бандли за фактичним sub_type; регенерувати worker_v2_bundles.json; оновити A.4/DESIGN §3 (К-1).
2. Owner-рішення по К-2 (пере-світити cu-7104 і cu-7101 АБО амендувати A.1) + механічний world-freshness чек у валідатор; виправити «fresh world» у self-review §A.
3. Fail-closed на невалідний/відсутній `class` у run_worker_v2 (К-3) + чесне формулювання «cap механічний над модельною класифікацією».
4. Смоук: додати R1 (+ C.5-ассерт на episode-derived reflection) і RGOLD; виправити «every memory arm» (К-4).
5. Гейт: T2 порядкова перевірка seq (+ session>=2), T3 `startswith("lessons.")`; перепрогнати --self-test (К-5).
6. Після 1-5 — повторний прогін усієї верифікаційної батареї та оновлення digest-ів freeze-маніфеста.

Після фолду цих шести — пакет, на мою оцінку, готовий до кроку 3 (ко-овнер) без повторного повного кола з мого боку: достатньо буде дифу фолдів.

---

# Curation appendix (ZCode, the implementing agent — PB-073 discipline)

Every load-bearing Fable claim was re-verified against the repo BEFORE
folding. Results:

| Claim | Verification |
|---|---|
| K-1 bundle misgrouping (cr-x003 = vce not euc; euc bundle all FP-3a; vce bundle = 12× one scenario) | CONFIRMED by reading fixture sub_types (cr-3003/4003 = valid_correction_environment) and the bundle artifact composition (cr-FP3b-euc contained only cr-4003/cr-3003, all class FP-3a; cr-FP3a-vce = 12 runs of cr-4001) |
| K-2 world reuse (cu-7104 pottery/kiln/glaze = v3l cu-6102; cu-7101 planetarium + opening phrase = v3h cu-2001) | CONFIRMED by grep + side-by-side text read; own rare-word scan additionally flagged cr-7005↔v3l/cr-6005 decorations (circular/noticeboard/photo/reassigned) which V18 also catches |
| K-3 untagged-class cap bypass | CONFIRMED in own code (cls="" continued to validation/acceptance) |
| K-4 smoke misses R1/RGOLD; C.5 assert absent | CONFIRMED (smoke arm list was R0/R2/R3/RBAD) |
| K-5 T2 no seq ordering + no session>=2; T3 forbidden branch only lessons.injected | CONFIRMED by code read (runner emits lessons.retrieve/render/digest/status too) |
| Б-1..Б-7 | Б-1 confirmed (wording); Б-2/Б-3 confirmed (folded); Б-4 confirmed (cross-comment added); Б-5 folded with K-1 interleave; Б-6 confirmed (inert key, documented); Б-7 verified (Phase V uses the same arm/seed-* layout, gate glob compatible) |
| Invalid-run trace census (0 appends; 35 empty injections; 53 live lesson renders; 3/21 probes) | CONFIRMED — matches the implementer's own §A census exactly |

All five K-findings and Б-1/2/3/5/6 folded same-session (see
labs/continuity/LOG.md RC-6 step-2 entry for the fold details and the
re-run battery). Curation verdict: 100% of load-bearing claims reproduced.
