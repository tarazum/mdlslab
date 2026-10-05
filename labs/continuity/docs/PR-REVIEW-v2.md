# PR-REVIEW-v2 — independent pre-registration review (EVALUATION-PREP-v2)

- **Reviewer:** model "Fable" via Claude Code CLI (`claude --model fable -p`), fresh context, read-only, run from the repo root
- **Date:** 2026-10-05, BEFORE any held-out (v3h) data or inference exists
- **Reviewed artifact:** `docs/EVALUATION-PREP-v2.md` (DRAFT) against `docs/PREREG-REQUIREMENTS-V2.md` (all 9 template items), `docs/SUITE-V3-DESIGN.md`, `experiments/suite-v3/power-results-v2.json`, the pilot aggregate, and the validator source
- **Verdict: NO-GO until 5 required changes** (all document/validator, zero GPU) — all folded the same day; see the disposition appendix. This file is the frozen review record; EVALUATION-PREP-v2.md was edited only as specified below.

---

Ревʼю завершено. Усі шість артефактів прочитані й звірені між собою (пре-рег ↔ шаблон ↔ дизайн ↔ power-артефакт ↔ aggregate пілоту ↔ код валідатора). Нижче — по чеклисту, далі вердикт.

---

## 1. ВИМІРНІСТЬ — ✅ з однією дірою в маніфесті

- Endpoint (label-form error rate, `EVALUATION-PREP-v2.md §3`) пілот фактично вимірював: `aggregate.json → per_arm.*.per_family_pass` містить CR і CU по армах, `rm_primary.error_rate` (0.714/0.619/0.524) рахувався тим самим harness-ом. Композит «12 кластерів CR+CU» як одне число harness ще не рахував, але analysis-script зобовʼязано написати й задайджестити ДО фризу (`§10`) — прийнятно.
- Скоринг-правило зафіксовано посиланням (`§9` → `SUITE-V3-DESIGN.md §3`, оголошено до pilot run 4) і реалізацію (`continuity.runner.extract_label`) дайджестять через `runner.py`. **АЛЕ:** сам `SUITE-V3-DESIGN.md` — носій прозового правила — у списку фриз-маніфесту `§10` відсутній. Правило «заморожено за посиланням» на документ, який не заморожено. → required change.

## 2. СПИВСТВОРЕНІСТЬ / MME — переважно ✅, але цифру 0.36 треба демістифікувати

- Критерій фальсифіковний: two-sided 95% CI, вердикт лише при «CI виключає 0 **І** точкова Δ ≥ 0.25» (`§6`). Обидва критерії роблять успіх *важчим*, не легшим — анти-reverse-engineering напрямок правильний.
- MME 0.25 **не** «підігнана під пілот» у сенсі гарантії успіху (вона нижча за пілотні 0.36, і 0.36 узгоджується з даними: CR err T0 0.583/T2 0.417 + CU err T0 0.75/T2 0.0, зважено 8:4 → 0.639 vs 0.278). Але вона **повністю power-обґрунтована** (0.25→0.812, 0.20→0.641 «rejected», `power-results-v2.json`): це найменша детектована дельта, а не змістовний поріг. Жодного substantive-речення в `§5` немає. Шаблон `§6` формально задоволений, тому це нотатка, не блокер.
- Головна упередженість сидить не в MME, а в **складі primary**: `SUITE-V3-DESIGN.md §4.1` визначав primary = CR(8)+RM(6)=14 кластерів, CU — secondary (відкрите питання №2 у `§10`). Пре-рег (`§2`) ставить primary = CR(8)+CU(4)=12: RM, де пілот показав **нуль ефекту** (T0=T2=0.333), демотовано, а CU, де T2 вийшла **в стелю** (1.0 при n=12, 3 seeds), промотовано. Це легітимна пілот→конфірматорна ітерація (пілот і є design data, v3h — held-out), і LOG це чесно фіксує як «design input #1», але сам пре-рег деviації від SUITE-V3-DESIGN не називає. → required change (прозорість, не переробка).

## 3. АГРЕГАЦІЯ / ПРОПУСКИ — ✅

Кластер=сценарій, 5 obs/кластер, 10k ресемплів, RNG seed на фризі (`§6–7`). Completeness guard: будь-який відсутній cluster-seed у T0/T2 → «incomplete», без підстановок і без ре-дро сидів (`§7`) — чисто. Resume за PB-075 із «zero repeated inference» має прецедент у самому пілоті (`aggregate.json → resumed_arm_seeds`, A×3 без повторного інференсу). Сумісно.

## 4. HELD-OUT ЧИСТОТА — ⚠️ механічний контроль відстає від заяви

- План v3h (`§2`) правильний по формі: свіжий контент, предекларовані сиди, «validator V3 runs against all prior suites».
- **АЛЕ код не відповідає заяві:** у `validate_fixtures_v3.py:150-164` V3 перевіряє disjointness лише від **v1/v2/v2-calibration** — v3-pilot (найнебезпечніше джерело витоку!) не покривається. І `validate_fixtures_v3.py:111` жорстко вимагає `primary_cluster_count == 14` — v3h із 12 primary кластерами **провалить власний валідатор**, або валідатор доведеться правити; якщо після фризу — це protocol violation за `§10`. → required change (оновити валідатор до фризу).
- Залишковий витік — fixture-authoring exposure: один автор, що бачив пілот (зокрема знає, що T2 ідеальна саме на CU), пише v3h. Визнано в `§2`; структурні перевірки E9–E13 + незалежне фікстур-ревʼю на гейті — розумна механіка, але див. пункт 7.

## 5. НЕ РЕВЕРС-ІНЖИНІРИНГ — ✅ з одним непокритим конфаундом

- Порогів, що гарантують успіх, не знайдено; негативний/нульовий результат має заморожене формулювання без промоції secondary (`§6`), exclusions тільки через гейт-сесію до читання результатів (`§7`).
- Непокритий конфаунд конструкту: у пілоті T0 дала **невалідні label-відповіді на 1/3 guess-проб** (`aggregate.json → T0.guess.valid_fraction = 0.667` проти 1.0 в A і T2). Якщо частина «помилок» T0 — це не хибна памʼять, а неспроможність видати чистий label (zero-or-multi-label = miss за правилом §3), primary contrast частково міряє формат-комплаєнс. Пре-рег має зобовʼязати декомпозицію помилок (wrong-label vs no/multi-label) як mandatory secondary. → required change.

## 6. ШАБЛОН (9 пунктів PREREG-REQUIREMENTS-V2)

| § шаблону | Покриття |
|---|---|
| 1 frozen analysis code | ✅ `§10` |
| 2 infra clause | ✅ `§11` (класи енумеровано, halt-gate → гейт-сесія) |
| 3 multi-rev | ✅ `§11` |
| 4 non-executor gates | ✅ `§12` |
| 5 wall-time reconcile | ✅ `§12` |
| 6 power section | ✅ `§5` (K=12, 5 obs, артефакт, MME, power 0.812) |
| 7 droppable-secondary | ✅ `§2` + `§13` (primary-first) |
| 8 notes не випаровуються | ⚠️ частково: `§2` згадує лише fixture-exposure; загального зобовʼязання, що нотатки ЦЬОГО ревʼю reappear у run record, немає → required change |
| 9 guess-звіт | ⚠️ частково: звітність є (`§2`, `§8`), але умова «MME ≥ 2× виміряного відхилення guess» ніде не операціоналізована (як рахується in-run, що робити, якщо band не кліриться) → required change |

## 7. ОДНА РУКА

Автор пропозиції-фікстур-пілоту-пре-регу — один агент. Наявні запобіжники (non-executor гейти `§12`, дайджест-маніфест `§10`, V3-disjointness, незалежне це ревʼю, owner-гейт) — пристойний мінімум, **за умови** що гейт-сесії отримають конкретні інструкції, а не «подивитись». Найслабша ланка — авторство v3h після знайомства з пілотом: жоден дайджест не ловить «я написав CU-сценарії такими, на яких T2 блищить». Додатковий механічний запобіжник, який варто вписати: фікстур-гейт перевіряє v3h на баланс sub-types і обох порядків source-конфліктів (вимога пропозиції «no arm can win by ranking alone») та підтверджує E10-ротацію позицій — з огляду на position-bias T2 0.667 у пілоті.

---

## ВЕРДИКТ: **NO-GO** (до фризу; всі зміни — документ/валідатор, нуль GPU, шлях до GO короткий)

## REQUIRED CHANGES

1. **Валідатор до фризу:** оновити `validate_fixtures_v3.py` — (а) V3-disjointness має покривати і v3-pilot, як заявлено в `EVALUATION-PREP-v2 §2`; (б) `primary_cluster_count == 14` (рядок 111) привести у відповідність до 12; перезапустити, зафіксувати новий дайджест у маніфесті, зазначити зміну E12 у пре-регу.
2. **Задекларувати зміну primary-складу** відносно `SUITE-V3-DESIGN §4.1` (RM → secondary, CU → primary) прямо в пре-регу, з позначкою «pilot-informed» і посиланням на LOG design input #1.
3. **Додати `SUITE-V3-DESIGN.md` у фриз-маніфест `§10`** — скоринг-правило заморожене посиланням на документ, який інакше лишається редагованим.
4. **Операціоналізувати шаблон §9:** формула in-run guess-band (|guess − 1/k|), правило на випадок, якщо MME 0.25 не клірить 2× band; плюс mandatory-secondary декомпозиція помилок wrong-label vs invalid/multi-label (мотив: T0 valid_fraction 0.667 у пілоті).
5. **Вписати клаузу шаблону §8** явно: всі нотатки PR-REVIEW-v2 reappear (addressed/acknowledged) у фінальному run record.

## NON-BLOCKING NOTES

1. MME 0.25 має лише power-обґрунтування; додайте одне змістовне речення (чому саме «чверть помилок» виправдовує складність T2). Врахуйте: пілотні 0.36 на ~2/3 несе CU-стеля (T2=1.0, n=12) — регресія до середнього ймовірна, і чесний результат у зоні 0.15–0.25 («CI виключає 0, але < MME») цілком реальний; заплануйте заморожене формулювання для цього кейсу окремо.
2. T2 position-bias 0.667 (LOG design input #3 «investigate before trusting») у пре-рег не потрапив — гейт має явно звірити E10-ротацію в v3h і звітувати позиційний розподіл по армах.
3. `§2`: слово «candidate» щодо сидів {1001–1005} двозначне — або це І Є сиди (їх рівно 5), або зафіксуйте правило вибору до фризу.
4. Completeness guard покриває лише T0/T2 — додайте одне речення, що означає некомплектність secondary-арм (звітується, не воїдить вердикт).
5. `§13` оцінка ~130 turns/seed проти 128 у пілоті на 27 сценаріях, тоді як v3h має 24+3 — звірте арифметику турнів після авторингу v3h, щоб 3-годинний кап не зрізав secondary несподівано.

**Найбільший ризик дизайну:** пілот-інформована промоція CU (родини, де T2 у пілоті вийшла в стелю) у primary-набір єдиним автором — головний канал, яким очікування 0.36 може виявитись артефактом дизайн-петлі, а не ефектом trust-ієрархії; v3h-disjointness це помʼякшує, лише якщо валідатор і фікстур-гейт реально його перевіряють (required changes 1 і нотатка 2).

---

## Appendix — disposition of required changes (implementing agent, 2026-10-05)

| # | Required change | Disposition |
| --- | --- | --- |
| 1 | Validator: v3-pilot disjointness + primary count parameterization | DONE — `validate_fixtures_v3.py` suite-parameterized (`--suite v3h`, EXPECTED_PRIMARY map); disjointness set now includes every other suite incl. v3-pilot; suite-v3 regression re-run PASS 13/13 |
| 2 | Declare the pilot-informed primary deviation from SUITE-V3-DESIGN §4.1 | DONE — EVALUATION-PREP-v2 §2 "Pilot-informed deviation" block (RM demoted / CU promoted, LOG design input #1) |
| 3 | Add SUITE-V3-DESIGN.md to the freeze manifest | DONE — §10 |
| 4 | Operationalize the guess-band rule + mandatory error decomposition | DONE — §12 guess-band formula and caveat rule; §8 mandatory wrong-label vs invalid-format decomposition (T0 guess valid_fraction 0.667 motivation stated) |
| 5 | §8 template clause: review notes reappear in the run record | DONE — §12 |

Non-blocking notes: 1 (substantive MME grounds + sub-MME frozen wording) — DONE §5/§6; 2 (gate checks E10 rotation + position report) — DONE §8/§12; 3 (seeds "candidate" ambiguity) — DONE §2 (seeds frozen {1001..1005}); 4 (secondary incompleteness wording) — DONE §7; 5 (v3h turn arithmetic after authoring) — carried as a freeze-time checklist item (executed when v3h is authored).

---

## Verify-pass (Fable, same day, read-only)

| Required change | Status |
| --- | --- |
| 1 validator parameterization + pilot disjointness | SATISFIED |
| 2 deviation declared | SATISFIED |
| 3 design doc in freeze manifest | SATISFIED |
| 4 guess-band + error decomposition | SATISFIED |
| 5 notes-reappear clause | SATISFIED |

Non-blocking 1-4: folded. **VERDICT: GO** (freeze path open: author v3h ->
analysis script FIRST into the digest manifest -> confirmatory run). Cosmetic
note (fixed same day): the validator report hardcoded `"suite": "fixtures/v3"`
— now derived from the --suite argument.
