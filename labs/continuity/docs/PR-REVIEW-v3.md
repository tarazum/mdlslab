# PR-REVIEW-v3 — independent pre-registration review (EVALUATION-PREP-v3)

- **Reviewer:** model "Fable" via Claude Code CLI (`claude --model fable -p`), fresh context, read-only, run from the repo root
- **Date:** 2026-10-06, BEFORE any v3i inference (FREEZE-A not yet executed)
- **Reviewed artifact:** `docs/EVALUATION-PREP-v3.md` (DRAFT) against `docs/PREREG-REQUIREMENTS-V2.md` (all 9 template items), `docs/NEXT-CYCLE-NOTES.md`, `docs/SUITE-V3-DESIGN.md` §3, `experiments/suite-v3/power_calc_v3.py` + `power-results-v3.json`, `fixtures/v3i` (variant-table mechanics), `src/continuity/fixtures.py` (render), the validator, and the cycle-1 record (`docs/REVIEW-FABLE-RESULTS.md`, confirmatory `results-summary.json`)
- **Curation:** every load-bearing claim was re-verified by the implementing agent against the repo before folding (see disposition appendix): the cycle-1 bimodal T0 pooled 0.50 passing the original pooled headroom gate (recomputed from per-cluster data), the T1/T3 0.45 tie, the single-seed gate artifact + hardcoded "14 primary" G3 detail, and the ~15% clip-floor probability at base 0.25 — all reproduced exactly.
- **Verdict: NO-GO until 5 required changes** (all document/validator/artifact, zero GPU) — all folded the same day; verify-pass appended below. This file is the frozen review record.

---

## Raw review (Fable, verbatim)

Усі матеріали прочитані й перехресно звірені; ключові числа циклу 1 я переперевірив незалежно (T0/T1 primary error 0.50/0.60 реконструюються з `family_pass_by_arm` у results-summary.json; CI [−0.2833, 0.000] і P1/P2/P3 збігаються з артефактами). Спробу самостійно прогнати assembly gate на сідах 2002–2005 заблокував sandbox — цей пункт верифікований лише документально. Нижче повний звіт.

---

# PR-REVIEW-v3 — приймальний огляд EVALUATION-PREP-v3 (DRAFT) до FREEZE-A

## A. Вимірність — ✅ (з одним розривом, винесеним у REQUIRED #2)

- Endpoint вимірюється наявним harness: `labs/continuity/src/continuity/runner.py:94` (`extract_label`, правило «рівно одна standalone-мітка») + `score_probe` реалізують рівно те правило, що заморожене посиланням у §9 драфту на SUITE-V3-DESIGN §3 (декларація 2026-10-05). Числові near-miss мітки CU безпечні щодо substring-колізій (lookbehind/lookahead по `[a-z0-9]` — «16» не матчиться всередині «26»).
- FREEZE-B order «analysis script FIRST» зафіксовано (`EVALUATION-PREP-v3.md` §2, крок 1; §10).
- **Розрив:** GO/NO-GO пілоту «reported from the frozen analysis path only» (§2), але FREEZE-A-маніфест (§10) заморожує лише «pilot run script» — скрипт, який обчислює headroom/sd/echo для GO/NO-GO, у маніфесті відсутній. PREREG-REQUIREMENTS-V2 §1 вимагає заморозки «every analysis/scoring script the results pass through» — GO/NO-GO-числа пілоту через такий скрипт проходять.

## B. Фальсифіковність / MME — ⚠️

1. **MME 0.25:** power-вимога шаблону §6 виконана: 0.842 на conservative P3, 0.810 на stress P4, δ=0.20 відхилено (0.670) — `power-results-v3.json`. Substantive-обґрунтування (§5: зміна рендерера для всіх майбутніх сесій; чверть менше помилок — мінімум, що виправдовує дефолт) — присутнє і не зводиться до power. Для найдешевшого інтервента 0.25 на межі завищення (менший ефект теж міг би виправдати копійчану анотацію), але формулювання «directional difference below the MME» чесно покриває цей результат. Прийнятно.
2. **Двобічність:** чотири зони вердикту в §6 симетричні, зона «annotations increase errors» названа прямо, cycle-1 контекст (T1 0.60 vs T0 0.50 — T1 ГІРША; я реконструював обидва числа з `results-summary.json` family_pass: T1 CR 0.225/CU 0.75 → 0.60; T0 CR 0.25/CU 1.0 → 0.50) задекларований у §4. ✅
3. **Челендж eps_s-скасування — математично коректний, з двома застереженнями.** У моделі `power_calc_v3.py:76-77` p0−p1 = (base0−base1) + (η0−η1) — eps зникає точно **до кліпінгу**. Кліпінг (0.02, 0.98) скасування ламає: при base_T1=0.25 і sd=√(0.2²+0.1²)≈0.224 ~15% cluster-seed імовірностей T1 упираються в підлогу 0.02, що стискає реалізовану дельту і повертає частину сід-дисперсії. Емпірично ефект мізерний: P2 0.855 vs P1 0.844 — різниця 0.011 ≈ 1.7 SE Монте-Карло (SE≈0.0065 при REPS 3000), тобто в межах шуму; кліпінг проблему НЕ ховає при заявлених (0.20, 0.10), але при більшому sig_shared або δ=0.30 асиметрія підлоги зросла б — пілотний re-check spread це покриває. Друге застереження: `eps = rng.normal(0, sig_shared, N_OBS)` (рядок 75) — складність сіда спільна для ВСІХ 12 кластерів, тоді як реально варіант-складність per-scenario-seed; до кліпінгу це нічого не змінює (все одно скасовується), після — залишки корелюють між кластерами в межах сіда, що cluster-bootstrap трохи лестить. Дрібниця. Реальний світ: `render_seed_variant` (fixtures.py:89) не має аргументу арми — контент справді спільний, претензія «same rendered content» підтверджена кодом. Невраховане на користь дизайну: при temp 0 відповіді обох арм на спільному контенті корельовані позитивно, що ЗМЕНШУЄ дисперсію парної дельти проти моделі з незалежними біноміальними — модель консервативна.

## C. Агрегація / пропуски — ✅

Completeness guard 12×5 обидві primary-арми, «incomplete» без підстановок (§7); сід-варіант як частина знаменника без ре-дро — сформульовано точно (§7, перший bullet); variant-integrity guard з per-seed rendered digests (§7); resume PB-075; exclusions тільки через gate-сесію з доказом (§7, останній bullet). Droppable-secondary не чіпає primary (§7, §13 primary-first). Зауважень немає.

## D. Held-out чистота / двофризовий design-loop — ⚠️

Канал, який я флагав у PR-REVIEW-v2 (pilot-інформована калібрація), тут легалізований відкрито: v3j авториться ПІСЛЯ пілоту, «difficulty calibration MAY use pilot per-sub-type rates» (§2), з мітигацією «fresh content + independent gate review» і V3-disjointness по rendered-текстах усіх сідів (validate_fixtures_v3.py:132-145). Механічні запобіжники реальні. Чого бракує:

- **Headroom-поріг №1 дірявий:** «mean primary error strictly inside (0.15, 0.85)» рахується по СЕРЕДНЬОМУ 12 кластерів. Власна патологія циклу 1 — T0 primary mean рівно 0.50 при 6/8 CR на підлозі 1.0 і 4/4 CU на стелі 0.0 — цей гейт ПРОХОДИТЬ. Бімодальна поверхня, яку гейт нібито ловить, через pooled mean невидима. (Див. також пункт I.)
- **Concentration-каденція без правила:** P5 (8/12 → 0.705; 6/12 → 0.578) у §5 названа caveat-ом і «the pilot's per-cluster report checks this» — але на відміну від spread-клаузи (§2.2: stress row + owner sign-off) до концентрації не привʼязано жодної пре-декларованої дії.
- Калібрація складності v3j тим самим автором по пілотних per-sub-type rates ніде не обмежена вимогою арм-нейтральності: гейт-інструкції §12 перевіряють склад і баланс, але не «чи не написані нові corrections так, що тільки T1-рендер їх підсвічує».

## E. Anti-reverse-engineering — ✅

Зони вердикту симетричні по ±0.25; «no promotion of secondaries»; exclusions тільки через gate-сесію; guess-band — лише caveat, не важіль. Перекіс CR-сабтайпів «toward T1's source/verification surface» (§2) — це відкрито задекларований pro-hypothesis вибір поверхні, легітимний для двобічного тесту (якщо T1 не виграє навіть на своїй поверхні — це інформативно; якщо виграє — узагальнення обмежене цією поверхнею, що §14 чесно не заперечує).

## F. Покриття шаблону PREREG-REQUIREMENTS-V2 — ⚠️ (8/9 чисто, §9 — натяжка)

| Пункт шаблону | Де в драфті | Статус |
|---|---|---|
| §1 frozen analysis code | §10 | ⚠️ pilot-analysis script відсутній у FREEZE-A (REQUIRED #2) |
| §2 infrastructure clause | §11 | ✅ класи перелічені |
| §3 multi-rev pre-declared | §11 | ✅ |
| §4 non-executor gates | §12 | ✅ Fable, verdict files до читання результатів |
| §5 wall-time reconciliation | §12 | ✅ |
| §6 power section | §5 + артефакт | ✅ 0.842 на MME |
| §7 droppable-secondary | §7, §13 | ✅ |
| §8 carried-over notes | §12, останнє речення | ✅ |
| §9 guessing band | §12 | ⚠️ див. нижче |

**§9:** шаблон каже «the MME **must clear** the guessing band (MME ≥ 0.15 or ≥ 2× the measured deviation, whichever is larger)». Драфт перетворює це на репортований caveat і прямо пише «never used to move the MME». У циклі 1 max-arm band = 0.333 (`results-summary.json` guess_band) → 2× = 0.667 > 0.25: якби §9 читати буквально, MME провалюється вже на цифрах циклу 1. Варіант-ротація v3i має стиснути band (саме cycle-1 band роздутий виродженими сідами: 30 guess-проб були фактично 6), але розбіжність «must clear» vs «never moves the MME» — суперечність драфту з binding-шаблоном, яку треба зняти текстом, а не замовчати.

## G. Одна рука — ⚠️ прийнятно з доповненням

Автор фікстур, білдера (`build_v3i.py`, LOG 1556-1561) і пре-рег — одна сесія. Проти каналу «сценарії, на яких T1 блищить» реально працюють: V14/V14b (fail-closed рендер + token closure), V15 (поби попарно різні, ≤0.5 ідентичних тернів), V16 (ротація позицій), V3 по rendered-мультисету, per-seed rendered digests у фризі, конкретні гейт-інструкції §12 (sub-type баланс, ОБИДВА порядки source-conflict, E10/V16). Це ловить структурні й позиційні маніпуляції. НЕ ловить семантичний тюнінг формулювань correction-тернів під T1-рендер — єдиний реальний залишковий канал, і він загострюється на FREEZE-B (автор уже бачив пілотні rates). Мінімальний фікс — додати в гейт-інструкції §12 явний пункт арм-нейтральності (NON-BLOCKING, але рекомендую).

## H. Per-seed variants механіка — ✅ з нотатками

- **Позиційний артефакт:** ротація детермінована і однакова для обох арм → позиційні ефекти спільні й скасовуються в парній дельті. V5 на rendered-мультисеті: 120 проб, позиції [0..5], max share 0.18 (`fixture-validation-v3i.json`). По переглянутих фікстурах (cr-3001/3007/3008, rt-3201, gc-3501) порядки — циклічні зсуви на 1 по сідах; «pairwise distinct» виконано, позиція expected пробігає ≥5 слотів.
- **Складність варіанта:** спільна між армами за побудовою (рендер арм-незалежний) — саме це легітимізує eps-скасування. Довжина промпта трохи пливе між сідами (tadpole/otter/minnow...), але однаково в обох армах → не конфаунд для парного контрасту.
- **Leakage між сідами:** кожен arm-seed — окремий прогін; V3 тепер покриває rendered-тексти всіх сідів обох напрямків. ОК.
- **Колізія ключів seed:** {2001..2005} — одночасно sampler seed і ключ варіант-таблиці, тобто контент і sampler-сід ідеально конфаундяться. При temp 0.0 sampler-сід інертний, а для парного контрасту обидві арми ділять той самий сід — колізія безпечна; але розділити «ефект контенту» від «ефекту сампл-сіда» в цьому дизайні неможливо в принципі — варто визнати одним реченням.
- **5 варіантів для spread:** sd з n=5 (df=4) має ~[0.6×, 2.9×] мультиплікативну невизначеність — поріг «sd ≤ 0.25» у GO/NO-GO №2 буде шумним; добре, що провал веде лише до stress row + sign-off, а не до смерті дизайну.
- V15 у v3i сидить рівно на межі 0.50 ідентичних тернів — проходить, але без запасу.

## I. Ризик поверхні циклу-1 (CR-флор + CU-стеля) — ❌ у поточній редакції

Цикл 1: T0 CU error = 0.0 на всіх 4 кластерах (`results-summary.json` per_cluster). v3i CU — та сама R5-структура з near-miss опціями (cu-3101: supersession «Correction for the records»), і T0/T1 обидва проходили CU у циклі 1 майже ідеально. Реалістичний сценарій: CU знову мертвий (обидві арми ~0.0) → ефект може жити лише у 8 CR-кластерах → це рівно P5-рядок 8/12 з power 0.705, а не заявлені 0.842. Головне: **GO/NO-GO №1 цього НЕ ловить** — pooled mean (0.15, 0.85) проходить і на повністю бімодальній поверхні (цикл-1 T0 = 0.50 — ідеальний прохід). Заявлені запобіжники в сукупності (headroom pooled + spread + echo) не закривають саме той механізм, який зʼїв цикл 1. Потрібен per-family headroom або поріг кількості дискримінуючих кластерів.

---

## ВЕРДИКТ: **NO-GO** (до FREEZE-A; усі фікси — редакторські, нуль GPU)

### REQUIRED CHANGES

1. **§2 GO/NO-GO №1 (headroom) — зробити per-family:** headroom-критерій обчислюється окремо для CR (8 кластерів) і CU (4 кластери) в обох primary-армах (обидві family-середні строго в (0.15, 0.85), або еквівалент через мінімум дискримінуючих кластерів); pooled-mean формулювання прибрати. Поточна редакція пропускає точну копію патології циклу 1 (T0 pooled 0.50 при 6/8 CR-флорі та 4/4 CU-стелі).
2. **§10 FREEZE-A — додати до маніфесту pilot GO/NO-GO analysis script** (скрипт, що обчислює headroom/per-seed sd/echo-rate), на виконання PREREG-REQUIREMENTS-V2 §1 («every analysis/scoring script the results pass through»). Зараз заморожений лише «pilot run script».
3. **§5/§2 — привʼязати пре-декларовану дію до концентрації (P5):** якщо пілотний per-cluster звіт показує <8 дискримінуючих кластерів, керує P5-рядок power-артефакту + owner sign-off перед FREEZE-B (дзеркально до spread-клаузи §2.2). Зараз перевірка є, правила — немає.
4. **§12 guess band — зняти суперечність із шаблоном §9:** або явно записати прочитання «MME 0.25 ≥ 0.15 задовольняє design-time вимогу §9; in-run band → caveat за v2-прецедентом», або чесно амендувати шаблонну вимогу через owner. Поточне «reported, never used to move the MME» прямо суперечить «the MME must clear the guessing band» binding-документа — при cycle-1 band 0.333 це не схоластика.
5. **§2 — виправити твердження «assembly gate G1-G6 PASS on all five seeds at this draft» або закомітити докази:** закомічений `experiments/suite-v3/assembly-gate-v3i.json` містить вердикт лише для `"seed": 2001`; gate-скрипт рендерить один сід за виклик і сам інструктує «run it for every predeclared seed at freeze time». LOG (рядок 1578) стверджує всі пʼять, але артефактів немає, і моя спроба перегнати сіди 2002–2005 була заблокована пісочницею. Мінімальна правка: або 5 per-seed артефактів у репо, або формулювання «PASS on seed 2001; all five seeds re-run at FREEZE-A with per-seed verdict files».

### NON-BLOCKING NOTES

- **N1.** Додати в гейт-інструкції §12 пункт арм-нейтральності формулювань v3j-corrections (єдиний незакритий канал однієї руки після пілотної експозиції; див. G).
- **N2.** Визнати одним реченням конфаунд «variant seed = sampler seed» (інертний при temp 0.0, нерозділюваний у цьому дизайні; див. H).
- **N3.** sd per-seed з n=5 має df=4 — поріг 0.25 шумний; варто репортувати sd з довірчим інтервалом, а не точкою.
- **N4.** Деталь G3 в `assembly-gate-v3i.json` каже «14 primary scenarios», тоді як суми категорій дають 12 і primary v3i = 12 — схоже на застарілий текст у detail-рядку gate-скрипта; перевірити при FREEZE-A.
- **N5.** Кліпінг (0.02, 0.98) ламає точність eps-скасування при сильно негативних eps для T1 (base 0.25); на заявлених параметрах ефект у межах MC-шуму (P2−P1 = 0.011 ≈ 1.7 SE), але якщо пілотний sd вийде >0.25, power-перерахунок на FREEZE-B має переконатись, що підлога не зʼїдає дельту.
- **N6.** У power-моделі eps спільний для всіх 12 кластерів у межах сіда (power_calc_v3.py:75), реальна варіант-складність — per-scenario; до кліпінгу байдуже, після — легка пост-кліп кореляція між кластерами. Косметика, зафіксувати в коментарі скрипта при FREEZE-B.
- **N7.** «T1 top overall score 0.45» — формально нічия з T3 (0.45 = 0.45, results-summary `t1_t3_exploratory_overall`); у §1 краще «tied-top».
- **N8.** V15 у v3i проходить рівно на межі 0.50 — для v3j закласти запас (ціль ≤0.45), інакше одна дрібна правка тексту завалить гейт.

### Головний ризик дизайну

Найбільша загроза — повторення нуль-результату не через відсутність ефекту, а через мертву поверхню: CU-сімʼя, в якій T0 уже в циклі 1 сидів на стелі (error 0.0 на 4/4 кластерах), перенесена у v3i структурно тією самою (R5-supersession + near-miss опції), і якщо обидві primary-арми знову пройдуть CU ідеально, весь контраст T0−T1 муситиме народитися у 8 CR-кластерах — це рівно P5-режим із power 0.705 замість заявлених 0.842, причому пропонований pooled-headroom гейт пілоту таку бімодальність пропускає мовчки (цикл-1 T0 pooled 0.50 — ідеальний прохід). Без per-family headroom-критерію і пре-декларованого правила на концентрацію дворазова фриз-архітектура лише легалізує перенесення цієї сліпої плями з пілоту в конфірматорний прогін.

---

## Appendix — disposition of required changes (implementing agent, 2026-10-06)

| # | Required change | Disposition |
| --- | --- | --- |
| 1 | Per-family headroom gate | DONE — §2 GO/NO-GO №1 rewritten: CR family-mean AND CU family-mean strictly inside (0.15, 0.85) in BOTH primary arms; pooled formulation removed; the cycle-1 bimodal T0 pooled 0.50 pathology named in the text as the motivating case |
| 2 | Pilot GO/NO-GO analysis script in FREEZE-A manifest | DONE — §10 FREEZE-A now includes `analyze_pilot_v3.py` alongside the pilot run script; §2 preamble states the GO/NO-GO numbers are "computed by the FROZEN pilot analysis script" |
| 3 | Pre-declared action for concentration (P5) | DONE — new GO/NO-GO clause 3: live clusters = both primary arms' cluster error strictly inside (0.10, 0.90); < 8/12 live → P5 row governs + owner sign-off before FREEZE-B; §5 cross-references the clause |
| 4 | Resolve guess-band contradiction with template §9 | DONE — §12 "Design-time reading of template §9" block: MME 0.25 ≥ 0.15 satisfied at design time; the 2×-measured-deviation arm operationalized per the accepted v2 precedent (PR-REVIEW-v2 RC4 → EVALUATION-PREP-v2 §12) as a mandatory in-run caveat, not an MME veto; cycle-1 band inflation (30 effective 6 guess probes) noted; owner may re-bind the template text — both facts travel into the run record |
| 5 | Evidence for "gate PASS on all five seeds" | DONE — five per-seed verdict files committed (`assembly-gate-v3i-seed2001..2005.json`, each PASS with its seed recorded); stale single-seed artifact deleted; §2 wording now "with committed per-seed verdict files for all five seeds" |

Non-blocking notes: N1 (arm-neutrality check in §12 gate instructions) — FOLDED; N2 (variant seed = sampler seed confound sentence in §2) — FOLDED; N3 (sd with n=5/df=4 CI, clause 2 + §8) — FOLDED; N4 (hardcoded "14 primary" in G3 detail) — FIXED (dynamic count, now reports 12); N5+N6 (clipping + shared-eps scope caveats recorded in `power_calc_v3.py` simulate() docstring incl. the FREEZE-B re-check obligation) — FOLDED; N7 (§1 "tied-top overall score 0.45 with T3") — FOLDED; N8 (v3j V15 identical-share target ≤ 0.45 in §2) — FOLDED.

---

## Verify-pass (Fable, same day, read-only, fresh context)

| Required change | Verdict | Evidence |
|---|---|---|
| RC1 Headroom per family | **SATISFIED** | §2 cl.1: "Headroom, PER FAMILY (not pooled — a pooled mean passed the exact cycle-1 pathology: T0 pooled 0.50 = 6/8 CR at 1.0 + 4/4 CU at 0.0)"; pooled formulation absent from the document |
| RC2 Frozen pilot analysis script | **SATISFIED*** | §10 FREEZE-A: "the pilot run script AND the pilot GO/NO-GO analysis script `analyze_pilot_v3.py`"; §2 "computed by the FROZEN pilot analysis script". *The file does not exist in the repo yet — legal for a draft, but FREEZE-A is impossible until the script is written and digested |
| RC3 Concentration (live clusters) | **SATISFIED** | §2 cl.3: LIVE clusters (both primary arms inside (0.10, 0.90) per cluster); < 8/12 → P5 row governs + owner sign-off; §5 cross-reference present |
| RC4 Guess-band design-time reading | **SATISFIED** | §12 "Design-time reading of template §9" block; v2 precedent confirmed in PR-REVIEW-v2.md (RC4 rows) |
| RC5 Per-seed gate artifacts | **SATISFIED** | 5 files seed2001..2005 exist, each with its own `"seed"` and `"verdict": "PASS"`; stale single-seed artifact deleted; §2 wording updated; G3 detail now dynamic ("12 primary scenarios") |

Non-blocking N1-N8: all **FOLDED** (verified in §2/§8/§12, `assembly_gate.py`,
`power_calc_v3.py` docstring).

**VERDICT: GO for FREEZE-A.** Single execution condition (a consequence of
RC2, not a new note): `analyze_pilot_v3.py` must actually be written and
included in the digest manifest AT FREEZE-A — freezing without it would
violate the just-adopted §10.
