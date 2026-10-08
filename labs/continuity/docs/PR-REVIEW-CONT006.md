# PR-REVIEW-CONT006 — independent pre-registration review (EVALUATION-PREP-CONT006)

- **Reviewer:** model "Fable" via Claude Code CLI (`claude --model fable -p`), fresh context, read-only, run from the repo root (first in the standing queue Fable → Opus → local GLM 5.3 Flash, owner directive 2026-10-07; no substitution needed, no limit block)
- **Date:** 2026-10-08, BEFORE any CONT-006 inference (Phase W not started; FREEZE not executed)
- **Reviewed artifact:** `docs/EVALUATION-PREP-CONT006.md` (DRAFT, commit 0bf6352) against `docs/PREREG-REQUIREMENTS-V2.md` (all 9 template items + five 2026-10-04 amendments), `docs/CONT-006-DESIGN.md`, `docs/REFLECTION-V2-PROPOSAL.md` (+ its binding readiness checklist and both folded proposal reviews), `docs/CONT006-TAXONOMY.md`, `experiments/cont006/experience-corpus-manifest.json` + `select_experience_corpus.py`, `fixtures/v3l` + `build_v3l.py` + `validate_fixtures_v3.py` (line-by-line git-diff 8077a26..0bf6352) + `fixture-validation-v3l.json`, `power_calc_cont006.py` + `power-results-cont006.json`, the CONT-002 precedent pair, `SUITE-V3-DESIGN.md` §3, LOG tail
- **Verdict: GO-with-changes — 5 required changes (RC-1..RC-5), all document/artifact-level, zero GPU.** All RC folded the same day by the implementing agent (disposition below) + verify-pass. This file is the frozen review record.

---

## Raw review (Fable, verbatim)

Усі матеріали доказового набору прочитані та перехресно звірені; git-дифф валідатора між 8077a26 і 0bf6352 проаналізований построково; арифметику power-артефакту перевірено вручну проти корпус-маніфесту. Нижче повний звіт.

---

# PR-REVIEW-CONT006 — приймальний огляд EVALUATION-PREP-CONT006 (DRAFT, коміт 0bf6352) до FREEZE

- **Рев'юер:** модель "Fable" (Claude Code CLI), свіжий контекст, non-executor, read-only, запуск з кореня репо `C:\projects\mdlslab`.
- **Дата:** 2026-10-08, ДО фризу і до будь-якого CONT-006 інференсу (Phase W не стартувала).
- **Об'єкт:** `labs/continuity/docs/EVALUATION-PREP-CONT006.md` (DRAFT) проти `PREREG-REQUIREMENTS-V2.md` (9 пунктів + п'ять поправок 2026-10-04), `CONT-006-DESIGN.md`, `REFLECTION-V2-PROPOSAL.md` (+ binding readiness checklist), обох рев'ю (GLM RC-1..RC-5; implementing-agent RC-1..RC-4), `CONT006-TAXONOMY.md` (FROZEN), `experience-corpus-manifest.json` + `select_experience_corpus.py`, `fixtures/v3l` (manifest + вибірково cr/cu/rt/dx субтипи й механізми), `build_v3l.py` (grep на недетермінізм), `validate_fixtures_v3.py` (git-дифф 8077a26..0bf6352 построково) + `fixture-validation-v3l.json`, `power_calc_cont006.py` + `power-results-cont006.json`, `EVALUATION-PREP-CONT002.md` + `PR-REVIEW-CONT002.md` (прецедент), `SUITE-V3-DESIGN.md` §3, LOG.md tail.
- **Обмеження виконання (чесно, як у прецеденті):** пісочниця заблокувала запуск python — валідатор (v3l + регресії), детермінізм `build_v3l.py`, перерахунок suite/manifest sha256 і повторний прогін power_calc верифіковані **документально** (закомічені вердикти + git-дифф + grep + ручна арифметика), не виконанням. Пререєстрація вже конвертує ці прогалини в механічні гейт-перевірки (§12, RC-4a/4b-патерн) — прогалина покрита протоколом.
- **Вердикт: GO-with-changes — 5 обов'язкових змін (RC-1..RC-5), усі документ/артефакт-рівня, нуль GPU, до FREEZE.**

---

## A. Внутрішня когерентність — ✅ (каркас цільний; дрібниці йдуть у RC-3/RC-5)

- **Фази W→G→V→P→C і порядок фризів — узгоджені.** §11: один FREEZE до Phase W («the earliest inference of the experiment»); §1/§6/§7.2: ACTIVE stores комітяться+дайджестуються в кінці Phase V, ДО першого transfer-запиту; freeze-гейт (§12) верифікує саме цей порядок по таймстемпах. Жодного pilot-залежного «at freeze» у тексті немає — урок RC-1 з PR-REVIEW-CONT002 засвоєний: pilot-залежні дії (power re-check, headroom stop, GC-трим) усі прив'язані до **pilot-gate checkpoint** (§5, §9), owner-visible.
- **Арми відповідають дизайну.** R3 успадковує ВСЮ машинерію доставки R2 (§1 «through the SAME machinery», §7 shared retrieval/renderer/budget, §8 той самий §7.1-валідатор і §7.2-правило) — RC-1 пропозиції (GLM) зафолджений коректно; інтерпретаційна сітка R2≈R3 / R3>R2 / обидва нулі перенесена в дизайн §2 і читається пререєстрацією (§14 перший bullet).
- **Правило активації:** store-level, окремо для R2- і R3-store за ТІЄЮ САМОЮ формулою; S0/SX на 4 VAL-кластерах × 7 сідів (28 проб); activate iff SX−S0 ≥ +0.05; будь-яка відсутня/невалідна VAL-проба → fail-closed; harm-сигнал при ≤ −0.05; неактивований store → арма біжить primary з ПОРОЖНІМ store (declared branch, чесний вердикт). Поріг чесно названий слабким директивним баром за дизайном, не другим endpoint-ом. ✅
- **Дві валідації розведені** (§7.1 детерміністична evidence-валідація, нуль GPU, однакова для R2 І R3; §7.2 емпірична генералізаційна) — термінологічна діра пропозиції закрита. **NO_LESSON першокласний** (§6 телеметрія derived-from-log; таксономічний клас FP-0 існує саме щоб NO_LESSON-rate був вимірюваний — включно з чесною декларацією, що для FP-5 NO_LESSON часто ПРАВИЛЬНИЙ вихід). **Anti-salience механічний** (§7.1d: токен-чеки проти suite-словників і corpus-label-сетів, не смак; контамінаційний гейт §12 проганяє його незалежно). ✅
- Дрібниці: (i) «10,000-equivalent draws» у §4 — не число; точна кількість бутстреп-дро має бути зафіксована у frozen-скрипті і в маніфесті (N-5); (ii) BAD/GOLD-TRIV уроки описані, але їхні ТЕКСТИ ніде не заморожуються (→ RC-3); (iii) gc-6501 входить у пілотний subset, але поведінка gc-проб у знаменниках критеріїв 1(ii)/2 не визначена (→ RC-5).

## B. Фальсифікованість / порожні поля — ✅ (найповніша пререєстрація лабораторії; дві діри закриваються RC-3/RC-5)

Усі поля, яких бракувало пропозиції (RC-5 GLM-рев'ю), реально ПРИСУТНІ, не обіцяні: MME 0.20 (§5, з артефактом); K=15 кластерів × 7 сідів + cluster-level power (§5); повний decision rule з 4 гілками frozen wording і порядком оцінки (§4); two-sided, негативи as-is, secondaries never promoted; R1≤R0 оголошено ex ante як реплікацію parroting-сигналу; missing-run (completeness guard §10, no substitution), resume (PB-075, кожен rev), exclusions (none, unless gate-proven invalid); сіди {6001..6007} + per-seed варіанти (V14-V16); label-form проби; тригер заморожений (post-experience single batch, порівняння — exploratory); frozen analysis code written FIRST з --self-test (§6, §11).

Урок RC-5 з CONT-002 (стоп-критерії в ТЕКСТІ, не в ненаписаних скриптах) застосований: **parroting-чек визначений дослівно в §9.1** («frozen HERE, not in a script body»: whitespace-токени, lowercase, без пунктуації, contiguous ≥ 4 слова); invalid-format share визначена в §9.2 через `extract_label` (нуль або >1 standalone-мітка) з явним знаменником. Залишкові дві діри того ж класу:

1. Тексти BAD- і GOLD-TRIV-уроків — об'єкти, проти яких визначені стоп-критерії 1(i) і 2 — не входять у freeze-список §11 (там лише «pilot counterfactual subset» = список кластерів). Parroting-чек проти незамороженого тексту — це стоп-критерій без зафіксованого референта → **RC-3**.
2. Знаменники критеріїв 1(ii)/2 («subset clusters × 2 pilot seeds») не кажуть, як рахується gc-6501: gc-проби expected-null (нуль міток — correcт behavior), і «pass rate»/«invalid-format share» на них не визначені → **RC-5**.

## C. Контамінація — ✅ (ланцюг закритий; порядок усередині одного коміту тримається на digest-вкладеності — прийнятно, позначено)

- **Таксономія ДО авторингу:** `CONT006-TAXONOMY.md` FROZEN 2026-10-08; доказ порядку — corpus-маніфест ВБУДОВУЄ taxonomy sha256 (`c93088bf…`, звірено: поле `taxonomy.sha256` у json присутнє), а v3l `manifest.json` текстуально цитує «Taxonomy basis: … FROZEN before this authoring». Застереження: таксономія, корпус, v3l і пререєстрація закомічені ОДНИМ комітом 0bf6352, тож git-історія сама по собі внутрішній порядок не доводить — доводить digest-вкладеність + freeze-гейт §12, який ре-хешує ланцюг. Прийнятно; зафіксовано як N-6-суміжне спостереження.
- **R3 blind-протокол закритий:** входи авторської сесії перелічені вичерпно (таксономія + corpus manifest + traces + схема/validator contract), заборони явні (v3l будь-якого сіда, transfer-сценарії, worker-вивід), дедлайн — до store freeze, верифікація — non-executor contamination gate з МЕХАНІЧНОЮ перевіркою (§7.1d re-run незалежно: жоден текст уроку не називає v3l ids/labels). Вектор «витік через авторів» з обох рев'ю пропозиції закритий.
- **Store freeze до transfer:** §6/§7.2 — commit+digest до першого TR-запиту, regeneration після = protocol violation; store-integrity guard (байт-ідентичність digest по сідах/ранах) + retrieval-телеметрія (нуль rendered-блоків для порожніх store — механічно). Validation-set-витік (model selection) нейтралізований: VAL-кластери ніколи в primary (V17 закріплює спліт у валідаторі), а після activation жоден параметр не рухається.
- **Fixture-authoring exposure** чесно задекларована (§9: автор v3l бачив таксономію і pooled outcome rates C2, але нічого derived від поведінки арм на самому v3l) — template §8 виконано. Залишкових незакритих каналів не знайшов: worker-prompt-витік покритий гейтом («the worker prompt's input set»), анти-salience блок-лист із suite-словників фільтрує НА вихід, не вносить контент.

## D. Сюіт і валідатор — ✅ (композиція звірена з таксономією; регресії НЕ ослаблені — підтверджено построково)

- **Композиція v3l проти таксономії:** субтипи/механізми перевірені по файлах фікстур: TR-кластери cr-6001 (valid_correction_environment) + cr-6002 (valid_correction_tool) = **FP-3a ×2**; cr-6003 (erroneous_user_correction) + cr-6004 (source_conflict) = **FP-3b ×2** (VAL cr-6005 = source_conflict); cu-6101/6102 superseded_value + cu-6103/6104 retracted_correction = **FP-1 ×4** (VAL cu-6105 superseded); rt-6201..6203 scripted_own_answer = **FP-2 ×3** (VAL rt-6204); dx-6401/6402 з lure_value = **FP-4 ×2** (VAL dx-6403); dr-6301/6302 = **FP-5 ×2**. Кожен клас ≥ 2 primary-кластери — таксономічна облігація 1 виконана. GC×3 з 6 never-stated пробами (V9). 22×7 = 154 інстанси ✓.
- **V8 mixed-диспетчер коректний** (git-дифф): маршрутизація трирівнева — `primary_families <= TRAP` (v3/v3h/v3i/v3j: старий V8-код байт-у-байт) → `elif not (primary & TRAP)` (v3k: старий V8R-шлях, бо {dr,dx}∩TRAP=∅) → `elif suite in VALIDATION_IDS` (v3l: trap-чек для CR/CU/RT інстансів + V8R для DX/DR). Mixed-гілка навіть строгіша за потрібне: `primary = flat по primary_families` ВКЛЮЧАЄ VAL-кластери — вони теж проходять структурні чеки. **V17** пінить validation-спліт (manifest-декларація == очікування, present, primary-family, transfer_eligible). **Регресії не ослаблені:** V7-віднімання validation-ids спрацьовує лише при непорожньому `VALIDATION_IDS.get(suite)` (тільки v3l; для старих суітів `counts_tr == fam_counts`); V1-розширення `seeds_ok` лише додає v3l у кортеж. Жодна стара гілка не змінена семантично.
- **Фактична неточність:** закомічений `fixture-validation-v3l.json` містить **19 рядків чеків** (V1, V14, V2, V3, V4, V5, V6, V7, V8, V8R, V9, V10, V11, V12, V13, V14b, V15, V16, V17), verdict PASS, failed []. Пререєстрація, дизайн і LOG кажуть «PASS 18/18» — міскаунт на один (ймовірно V8/V8R пораховані як один чек). Заморожувати міскаунт — це клас RC-3-CONT002 (привчання ігнорувати тривоги) → **RC-4**.
- **Регресії v3..v3k PASS ×5** — на сьогодні executor-самосвідчення в LOG (закомічений `fixture-validation-regressions-post-v3k.json` датований ДО v3l-розширення валідатора). Пререєстрація це ЗНАЄ і вже призначила non-executor fixture-гейту комміт НОВОГО консолідованого артефакту (§12, явне посилання на RC-4a-прецедент) — правильна конструкція; сам прогнати не зміг (sandbox).
- **Parroting-чек** (≥4-слівний verbatim-спан) — механічний, дешевий, визначення в тексті. Валідаційний нюанс: короткий BAD-урок про ФОРМАТУВАННЯ може ненавмисно ділити 4-грам з легітимною інструкцією проби («reply with the label only» живе в кожному label-form пробному тексті) → хибний parroting-тригер. Закривається тим же RC-3 (заморожений BAD-текст + механічна перевірка відсутності 4-грам-перетину з рендереним v3l). **GOLD-TRIV-чек** механічний через extract_label ✓, але має виродженість за низької бази (див. N-2) і gc-неоднозначність (RC-5).
- `build_v3l.py`: grep на random/time/uuid/datetime — чистий; детермінізм повторним прогоном не перевіряв (sandbox); «deterministic re-run verified» — заява LOG, покривається freeze-гейтом.

## E. Статистична чесність — ⚠️ (модель чесна, драбинка легітимна; ОДНА арифметична помилка в b0 → RC-1)

**(a) MME-драбинка 0.15/0.175/0.20 — легітимний design-time sizing.** Відмінність від CONT-002 (там MME 0.25 стояв субстантивно, рухали розмір вибірки): тут дизайн ВЖЕ на стелі amendment-(c) (15 кластерів) і 7 сідів, рости нікуди, тож рухали MME — але (i) ВГОРУ (0.15→0.20: піднімання планки заяви — консервативний напрямок; sub-0.20 ефекти чесно оголошені непретендабельними), (ii) до будь-яких даних (zero-GPU milestone), (iii) з повним слідом у артефакті (рядки R5/R6 недорозмірених щаблів збережені «for the record», як і sizing-рядки K15×5=0.763, K12×7=0.801), (iv) із виконанням букви template §6 («MME нижче детектабельного ефекту при ~80% = fail template review» — 0.20 і Є найменший детектабельний 0.05-крок). Це не підгонка потужності під бажану заяву, а підгонка планки заяви під чесну потужність, задекларована відкрито. Приймаю.

**(b) Paired-модель power_calc — коректна.** eps спільний per cluster-seed скасовується всередині Δ (виправдання реальне: обидві арми бачать той самий рендерений контент — `render_seed_variant` без арм-аргументу, підтверджено ще в CONT-002-рев'ю); eta per arm чесно названа power killer і керує стрес-рядом (R7 0.848) з governance; біноміальний шум n=1 змодельований явно. Кліпінг [0.02, 0.98] при b0 ~0.4–0.5 і d 0.20 практично не кусає (на відміну від bAs 0.90 у CONT-002) — застереження N-1-CONT002 тут маломатеріальне. Established ≈0.45 на MME задекларований відкрито (0.454 в артефакті; механізм point≥MME, цикл-2 прецедент); false positive 0.038/0.001; harm 0.652; headroom-edge b0 0.75 → 0.819. **Усі числа драфту звірені з power-results-cont006.json — збігаються всі 13 рядків.** Headroom-stop (§5/§9.4: pilot R0 > 0.75 → owner decision, «no parameter moves automatically») — без автоматики ✓. Pilot-gate power re-check ≥0.75 — на checkpoint-і, не «at freeze» ✓.

**(c) ГОЛОВНА ЗНАХІДКА — b0 = 0.42 порахований з неправильним знаменником.** Docstring power_calc: «b0 = 0.42 = C2 T-arm pooled pass on primary families: (65+67+62+58)/4/150». Перевірено проти corpus-маніфесту: fails конфірматорних T-арм (сума по 5 сідах) — T0 55, T1 53, T2 58, T3 62. Primary-family проб на арму = 24/сід × 5 = **120** (30 проб/трейс МІНУС 6 gc, які селектор ніколи не рахує у fails). 120−55=65, 120−53=67, 120−58=62, 120−62=58 — **чисельники 65/67/62/58 збігаються з primary-pass-ами по знаменнику 120 точно, по всіх чотирьох армах**. Отже pooled pass на primary families = 252/480 = **0.525**, а не 252/600 = 0.42 (знаменник 150 помилково включає 30 gc-проб, виключених із чисельника). Матеріальність для потужності — нульова: сенситивні рядки R11/R12 (b0 0.30 → 0.879; b0 0.55 → 0.869) беруть у вилку, MME-висновок не рухається. Але freeze-маніфест із задокументованою арифметичною помилкою в опорному параметрі — майбутній спір і підрив довіри до артефакту → **RC-1** (виправити деривацію, перегенерувати артефакт — секунди, нуль GPU).

**(d) Guessing band (template §9) — читання для дельта-endpoint-а не закрите.** Пререєстрація декларує «MME 0.20 ≥ 2× any plausible band deviation» ex ante і «in-run caveat … never used to move the MME». Але шаблон каже «MME ≥ 0.15 **or ≥ 2× the measured deviation, whichever is larger**»: якщо виміряний guess rate відхилиться від 1/6 більш ніж на 0.10 (цілком можливо при позиційному зсуві), 2×deviation > 0.20 — і caveat сам по собі букву шаблону не задовольняє. По суті для ПАРНОГО Δ-endpoint-а band значною мірою симетричний між армами і скорочується в контрасті — але це читання ніде не зафіксоване. CONT-002 розв'язав аналогічне upward-only формулою на pilot-gate checkpoint-і → **RC-2** (одне речення, зафіксувати binding-читання).

## F. Покриття PREREG-REQUIREMENTS-V2 — 9/9, з них 2 з натяжками

| Пункт шаблону | Де в драфті | Статус |
|---|---|---|
| §1 frozen analysis code | §6 (обидва скрипти written FIRST + --self-test) + §11 (повний список шляхів) | ✅ чисто; натяжка прецедентного типу: скрипти на момент рев'ю НЕ існують (єдиний незалежний погляд — гейт-dry-run §12, RC-4b-патерн, вже вбудований) |
| §2 infrastructure clause | §11 (4 класи перелічені; rendering-фікси до інференсу стадії; relaxation → гейт + header) | ✅ чисто |
| §3 multi-rev | §11 («attempt counts and revs stated exactly») | ✅ чисто |
| §4 non-executor gates | §12 (fixture / freeze / contamination / script-verification гейти з конкретними інструкціями; черга Fable→Opus→GLM) | ✅ чисто, конкретніше за CONT-002 (доданий contamination gate) |
| §5 wall-time reconciliation | §12 (seed→arm→run суми по всіх attempts; `summary_rebuilt_offline`) | ✅ чисто |
| §6 power section | §5 + артефакт (K=15, n=7, метод = power_calc_cont002-лінія, MME, 0.862 на MME) | ⚠️ числа звірені і збігаються, але деривація b0 містить арифметичну помилку → RC-1 (потужність нечутлива — R11/R12) |
| §7 droppable-secondary | §9.3 (GC-трим предекларований) + §10 (primary untouchable, incomplete-вердикт) | ✅ чисто |
| §8 carried notes | §12 (усі ноти цього рев'ю + предекларовані CN-A/CN-B) | ✅ чисто; CN-B (GO-критерії 1–2 кондиціонують launch, не оцінку; headroom читає лише R0) — коректний аналог N-2-CONT002 |
| §9 guessing band | §5 (floor 0.15 ✓; empirical rate поруч із числами; caveat) | ⚠️ натяжка: «whichever is larger»-гілка для Δ-endpoint-а не розв'язана → RC-2 |

П'ять поправок 2026-10-04 (a-e): (a) §6/§11 ✓; (b) §2 label-form + §5 band ✓ (з RC-2-нюансом); (c) §5 K=15 на стелі ✓; (d) §12 ✓; (e) §12 ✓.

## G. Feasibility — ✅ (анкери з закритих ранів; worst case названий прямо; стопи без автоматики)

- Transfer: 4 арми × 7 сідів × 103 терни ≈ 2884 запити проти виміряного C2-анкера (3250 запитів ≈ 2h16m на granite) → est. 1.8–2.5 год; + worker ≤1 год (50 бандлів × 1–2k ток. на qwen, batch-тригер — саме та конструкція, яка в рев'ю пропозиції відсікла 3+год failure-тригер); + VAL ~20 хв; + пілотні extras ≤30 хв. Разом ~3.5–4 год, кап 5 год. Узгоджено.
- Worst case стартований прямо (§9.3, N-3-прецедент): якщо всі no-record терни ramble-ять до num_predict-капа — granite-wall ×2, backstop = NO-GO критерію 3, трим GC покриває лише помірний перебір. Чесно. (Помітно, що think-pin у CONT-002 убив ramble-mode — ризик реально нижчий за декларований, що є консервативним напрямком.)
- Channel-dead stop (§9.2 combined): обидва store провалили activation І GOLD-TRIV провалений → confirmatory transfer НЕ стартує, owner decision recorded either way — найдешевший де-риск третього нуля поспіль, правильно розміщений.
- R1 безкоштовна (byte-stable MVP); Phase G нуль GPU.

## H. Порожнини — що закрити до/при FREEZE

1. **Тексти BAD/GOLD-TRIV уроків** не заморожуються ніде, хоча проти них визначені стоп-критерії (RC-3).
2. **gc-6501 у знаменниках пілотних критеріїв 1(ii)/2** — поведінка gc-проб (expected-null, нуль міток = правильно) не визначена (RC-5).
3. **b0-деривація** в power-артефакті (RC-1).
4. **Binding-читання template §9 для Δ-endpoint-а** (RC-2).
5. **«PASS 18/18» vs 19 рядків** закоміченого вердикту (RC-4).
6. Аналітичні скрипти `analyze_pilot_cont006.py` / `analyze_confirmatory_cont006.py` і run-скрипт — не написані (дозволено шаблоном; гейт-dry-run §12 їх покриє; точну кількість бутстреп-дро зафіксувати у frozen-скрипті — N-5).
7. Worker-prompt/шаблон, evidence-validator-модуль, renderer — авторинг при freeze; contamination gate + script-verification гейт призначені. Порожнин поза RC немає.

## I. Вердикт

### **GO-with-changes** — 5 обов'язкових змін, усі документ/артефакт-рівня, нуль GPU, до FREEZE.

**Обов'язкові зміни (для фолдингу виконавцем same-session):**

- **RC-1 (арифметика b0; `power_calc_cont006.py` docstring/константа, `power-results-cont006.json`, пререєстрація §5, дизайн §де цитується).** Чисельники 65/67/62/58 — це primary-family pass-и конфірматорних T-арм по знаменнику **120** проб/арму (24 primary-проби/сід × 5 сідів; 6 gc-проб/сід виключені з fails селектором — звірено з corpus-маніфестом: 120−55/53/58/62 = 65/67/62/58 точно по всіх чотирьох армах). Правильний pooled b0 = 252/480 = **0.525**, не 252/600 = 0.42. Виправити деривацію, перегенерувати power-артефакт з b0 0.525 (очікування за R2/R12-інтерполяцією: conservative-рядок ~0.86–0.87 — MME 0.20 стоїть), оновити числа в §5. Якщо вирішено лишити 0.42 як додатковий консервативний рядок — перейменувати чесно (це НЕ «pass on primary families»). Обґрунтування: задокументована арифметична помилка в опорному параметрі замороженого артефакту; потужність нечутлива (R11/R12), тому це correctness-fix, не re-sizing.
- **RC-2 (template §9 для дельта-endpoint-а; §5).** Зафіксувати binding-читання гілки «≥ 2× measured deviation, whichever is larger» для парного Δ: АБО явна декларація, що band-відхилення не рухає Δ-MME, бо guess-поведінка арм-симетрична і скорочується в парному контрасті (caveat-only, і це Є виконання шаблону для цього класу endpoint-ів), АБО CONT-002-стилева upward-only формула на pilot-gate checkpoint-і (`MME' = max(0.20, 2×band_dev_measured)`). Зараз «≥ 2× any plausible band deviation» — непідкріплене ex-ante твердження, яке при виміряному відхиленні >0.10 створює спір на момент вердикту.
- **RC-3 (фриз контрфактуальних уроків; §9.1, §11).** Додати у freeze-маніфест ТЕКСТИ BAD- і GOLD-TRIV-уроків (+ їхні injection-конфіги) з дайджестами, до будь-якого пілотного інференсу; явно декларувати, що вони НЕ проходять §7.1 evidence-валідацію (BAD за конструкцією не може) і входять через ідентичний renderer/prompt slot/бюджет; додати механічну перевірку (гейт або самотест пілотного скрипта): жоден contiguous 4-грам замороженого BAD-тексту не зустрічається в рендерених v3l-текстах (інакше легітимна проб-інструкція типу «reply with the label only» дає хибний parroting-тригер критерію 1(i)). Обґрунтування: стоп-критерії 1(i)/2 визначені проти об'єктів, які зараз ніде не зафіксовані.
- **RC-4 (міскаунт чеків; §1 пререєстрації, дизайн §9, LOG-форвард).** «validator PASS 18/18» ≠ закомічений артефакт: `fixture-validation-v3l.json` містить **19** рядків чеків (V8 і V8R — окремі записи). Виправити на 19 або перелічити id-шники. Обґрунтування: клас RC-3-CONT002 — заморожена розбіжність документації з артефактом провокує хибні тривоги гейтів або звичку їх ігнорувати.
- **RC-5 (gc у пілотних знаменниках; §9.1(ii), §9.2).** Зафіксувати: критерій 1(ii) (BAD pass rate vs R0) і критерій 2 (invalid-format share) рахуються на subset **без gc-6501** (gc-проби expected-null: «pass rate» на них не визначений, а нуль міток — правильна поведінка, що спотворює invalid-format share); gc-6501 лишається в subset-і лише для guess-band/позиційної телеметрії. Заразом зафіксувати точний знаменник у пробах (7 non-gc кластерів × 2 сіди = 14, чи інший — але ЧИСЛО в тексті). Обґрунтування: це стоп-критерії запуску confirmatory; їхні знаменники не можуть довизначатися скриптом.

**Необов'язкові нотатки (за шаблоном §8 мають повторитися у фінальному run record):**

- **N-1.** Критерій 1(ii) працює на ~14–16 пробах: band −0.10 ≈ 1.5 проби, шум біноміальний (sd частки ~0.12) — ймовірність хибного спрацювання матеріальна. Прийнятно, бо порушення веде на owner gate, не на авто-стоп; сказати це в run record поруч із результатом критерію.
- **N-2.** GOLD-TRIV-чек (покращення invalid-format share ≥ 0.10 абс.) структурно непроходимий, якщо пілотна R0-база invalid-format < 0.10 на subset-і (гранітний прецедент 0.05–0.20 допускає цей край). У run record зафіксувати: висновок «канал, можливо, мертвий» валідний лише при R0-базі ≥ 0.10; інакше критерій 2 — «non-informative», owner gate розглядає його саме так.
- **N-3.** cr-6001/cr-6002 (заявлені FP-3a) несуть seed-механізм `scripted_agent_answer`, який таксономічна таблиця мапить на FP-2 — класова ко-сигнатура за конструкцією (верифікована корекція перекриває власну попередню відповідь). Per-class Δ-таблиця (§14) має нести цю ко-позначку, інакше описова класова атрибуція читатиметься сильніше, ніж вона є.
- **N-4.** Текст corpus-маніфесту `selection_rule` каже «(suite v3j; pilot 25 + confirmatory 25)», тоді як C2-пілот бігав suite v3i (LOG це вже виправляє приміткою). Або ре-емітнути маніфест з точним формулюванням ДО фризу (селектор байт-детермінований; оновити цитований digest e8e863b7… у пререєстрації), або acknowledged у run record.
- **N-5.** «10,000-equivalent draws» (§4) — зафіксувати точну кількість бутстреп-дро числом у frozen-скриптах і маніфесті (power-артефакт використовував BOOT=4000; аналіз обіцяє інше — розбіжність легальна, але має бути числом, не «equivalent»).
- **N-6.** Worker-бандл: num_ctx 4096 при мульти-сесійних бандлах (worker «may inspect MULTIPLE sessions») — ризик тихого обрізання evidence. Додати в raw-log телеметрію токенів на виклик і truncation-прапорець (done_reason), щоб NO_LESSON від обрізаного входу був відрізнюваний від справжнього NO_LESSON.
- **N-7.** Таксономія/корпус/v3l/пререєстрація закомічені одним комітом 0bf6352 — внутрішній порядок авторингу доводиться digest-вкладеністю (taxonomy sha у corpus-маніфесті; цитата в v3l-manifest), не git-послідовністю; freeze-гейт §12 вже верифікує саме digest-ланцюг — зафіксувати це явно у гейт-вердикті.
- **N-8.** Межі цього рев'ю: sandbox заблокував виконання python — валідатор v3l (19 чеків) і регресії v3..v3k, детермінізм `build_v3l.py`, перерахунок suite/manifest digest-ів і повторний прогін power_calc верифіковані документально (закомічені артефакти + построковий git-дифф валідатора + grep білдера + ручна арифметика проти corpus-маніфесту), не прогоном. Пререєстрація §12 вже конвертує кожну з цих позицій у механічну перевірку non-executor гейтів — прогалина покрита протоколом, як і в прецеденті N-6-CONT002.

**Підсумок одним рядком:** найдисциплінованіша пререєстрація лабораторії — уроки CONT-002 (pilot-gate checkpoint, стоп-критерії в тексті, гейт-регресії, carried notes) імпортовані системно, контамінаційний ланцюг worker→store→transfer замкнений, MME-драбинка — чесний design-time sizing у консервативний бік; єдина змістовна вада — арифметична помилка знаменника в b0 (0.42 замість 0.525, на потужність не впливає) плюс чотири дешеві документальні закриття (band-читання для Δ, фриз BAD/GOLD-TRIV-текстів, gc-знаменники, міскаунт 18/19); після RC-1..RC-5 — GO на owner gate.

---

## Executor curation of the review's load-bearing claims

Standing rule (owner directive 2026-10-07: curatorial verification of reviewer claims is mandatory). Every load-bearing claim re-verified against the repo before folding:

1. **RC-1 (b0 denominator) — CONFIRMED numerically from the corpus manifest.** C2-confirmatory T-arm fails per arm: T0 55, T1 53, T2 58, T3 62 (sums of per-trace `fails` over the 5 seeds); non-gc probes per arm = 150 − 30 = 120; primary passes = 120 − fails = 65/67/62/58; pooled = 252/480 = **0.525** exactly as the reviewer computed. The draft's `(65+67+62+58)/4/150 = 0.42` had excluded gc probes from the numerator (the selector never counts them as fails) but not from the denominator. Power insensitive: sensitivity rows b0 0.30/0.55 bracketed both readings (0.879/0.869).
2. **RC-4 (check-record count) — CONFIRMED.** `fixture-validation-v3l.json` carries **19** check records (V8-structural-eligibility and V8R-recall-eligibility are separate records in the mixed suite); the milestone LOG/design said "18/18" — a miscount. Fixed everywhere; LOG history stays append-only, the correction is recorded in this fold and the new LOG entry.
3. **RC-2 (template §9 "whichever is larger") — CONFIRMED by quoting the template.** The draft's "≥ 2× any plausible band deviation" was an unsubstantiated ex-ante assertion. Folded: paired-Δ binding reading + the frozen upward-only re-derivation `Δ_MME' = max(0.20, 2 × band_dev_measured)` at the pilot-gate checkpoint (the CONT-002 RC-1 pattern).
4. **RC-3 (counterfactual lesson texts unfrozen) — CONFIRMED by reading prereg §11.** The freeze list named the pilot subset (cluster ids) but not the BAD/GOLD-TRIV texts the stop-criteria reference. Folded: `experiments/cont006/counterfactual-lessons.json` authored and frozen at the fold (digest cdc53a4d708ef7bc…), `check_counterfactual_lessons.py` verifies mechanically, for every v3l scenario and every seed {6001..6007}, that NO contiguous 4-gram of either lesson text occurs in any rendered turn text — PASS (0 shared; 29+29 lesson 4-grams checked). This also closes the reviewer's false-trigger concern (a shared 4-gram with "reply with the label only"-style probe instructions would make compliant replies trip the parroting check).
5. **RC-5 (gc-6501 in pilot denominators) — CONFIRMED by reading prereg §9.** gc probes are expected-null; "pass rate" is undefined on them and zero-label replies are CORRECT there. Folded: criteria 1(ii)/2 computed WITHOUT gc-6501, denominator 7 non-gc clusters × 2 seeds = 14 probes per arm, number in the text; gc-6501 stays telemetry-only. The N-2 degenerate-base clause (GOLD-TRIV non-informative at R0 base < 0.10) folded alongside.
6. **N-4 (manifest wording) — CONFIRMED.** The corpus manifest's `selection_rule` said "suite v3j" although the C2 pilot ran suite v3i (ids x-3xxx); the selector maps both. Selector text fixed; manifest re-emitted byte-deterministically; digest e8e863b7… → **6f8f885a…**; prereg §2 + design §3 references updated.
7. **Power numbers (review section E) — all 13 artifact rows re-checked by the reviewer against `power-results-cont006.json` (pre-regen) and reproduced; post-RC-1 regeneration (b0 0.525) re-run by the executor:** conservative 0.862 → **0.871**, binomial 0.845 → 0.863, stress 0.848 → 0.845, sub-MME 0.650 → 0.660, ladder-mid 0.775 → 0.769, K15×5 0.763 → 0.751, K12×7 0.801 → 0.796, established-at-MME 0.454 → 0.420, gold-scale established 0.921 → 0.881, false-positive 0.038 → 0.041; harm 0.652, gold-scale detection 0.994, headroom-edge 0.819 unchanged. MME 0.20 stands.
8. **Reviewer execution limits (N-8) — acknowledged.** The reviewer's sandbox blocked python; validator/regressions/digests/power-rerun were verified documentally. Converted to mechanical gate checks: the executor re-ran post-fold — validator v3l PASS 19/19 + regressions v3/v3h/v3i/v3j/v3k PASS ×5 (exit 0 each), the 4-gram check PASS, the corpus manifest byte-stable at 6f8f885a… — and the §12 non-executor gates re-run all of it independently before any inference.

## Disposition of RC / N (fold record)

| Item | Change folded | Where |
| --- | --- | --- |
| RC-1 | b0 derivation corrected (252/480 = 0.525, gc exclusion consistent); power artifact regenerated (conservative 0.871); MME 0.20 stands; all cited numbers synced | power_calc_cont006.py + power-results-cont006.json; prereg §5; design §1 |
| RC-2 | binding paired-Δ reading of template §9 + frozen upward-only re-derivation Δ_MME' = max(0.20, 2 × band_dev_measured) at the pilot-gate checkpoint | prereg §5 |
| RC-3 | BAD/GOLD-TRIV texts + injection configs frozen with digests; declared §7.1 bypass (by design); mechanical 4-gram non-overlap vs every rendered v3l text, every seed (PASS); added to the freeze list + gate re-run | experiments/cont006/counterfactual-lessons.json + check_counterfactual_lessons.py; prereg §11 |
| RC-4 | "PASS 18/18" → 19/19 (19 check records; V8 and V8R separate); miscount acknowledged | prereg §2; design §9 (LOG history append-only; corrected in this record + new LOG entry) |
| RC-5 | pilot criteria 1(ii)/2 computed WITHOUT gc-6501; denominator 14 probes/arm in the text; gc-6501 telemetry-only | prereg §9 |
| N-1 | CN-C carried note (criterion 1(ii) binomial noise on ~14 probes; violation → owner gate, never auto-stop) | prereg §12 |
| N-2 | degenerate-base clause: R0 invalid-format base < 0.10 → criterion 2 NON-INFORMATIVE, never channel-dead evidence alone | prereg §9.2 |
| N-3 | FP-3a/FP-2 construction co-signature note on the per-class Δ table | prereg §14 |
| N-4 | corpus manifest wording fixed (v3i pilot + v3j confirmatory); re-emitted; digest 6f8f885a…; references updated | selector + manifest; prereg §2; design §3 |
| N-5 | "10,000-equivalent draws" → exactly 10,000 draws (number, not "equivalent") | prereg §4 |
| N-6 | raw worker log carries per-call token counts + done_reason truncation flag; truncated_call_count telemetry | prereg §6 |
| N-7 | freeze gate verifies the taxonomy-before-authoring ordering by DIGEST NESTING (taxonomy sha in corpus manifest; taxonomy basis in v3l manifest), stated in the gate verdict | prereg §12 |
| N-8 | acknowledged; converted to mechanical gate checks (executor post-fold re-runs recorded above) | this appendix |

## Verify-pass (post-fold)

- Validator: `--suite v3l` PASS 19/19 + regressions v3/v3h/v3i/v3j/v3k PASS ×5 (exit 0 each; frozen per-suite JSONs untouched).
- `check_counterfactual_lessons.py`: PASS (0 shared 4-grams vs ALL rendered v3l texts, every seed; lessons sha256 cdc53a4d708ef7bc…).
- Corpus manifest: selector re-run byte-stable at sha256 6f8f885a29ecfa6e…; prereg/design digest references match.
- Power artifact regenerated with b0 0.525; every number cited in prereg §5 re-checked against the new JSON (all match).
- Grep: no stale 0.862/0.650/0.775/e8e863b7/"10,000-equivalent" remain; the only "18/18" left is the historical mention inside the RC-4 correction text itself.
- No frozen artifact touched: fixtures/v3l byte-identical (builder deterministic); fixture-validation-*.json for prior suites unmodified.

**Post-fold verdict: GO — the pre-registration proceeds to the owner gate** (explicit owner acceptance before ANY inference — worker pass included; never-autonomous clause).
