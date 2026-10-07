# PR-REVIEW-CONT002 — independent pre-registration review (EVALUATION-PREP-CONT002)

- **Reviewer:** model "Fable" via Claude Code CLI (`claude --model fable -p`), fresh context, read-only, run from the repo root (first in the standing queue Fable → Opus → local GLM 5.3 Flash, owner directive 2026-10-07; no substitution needed)
- **Date:** 2026-10-07, BEFORE any v3k inference (FREEZE not yet executed)
- **Reviewed artifact:** `docs/EVALUATION-PREP-CONT002.md` (DRAFT) against `docs/PREREG-REQUIREMENTS-V2.md` (all 9 template items), `docs/CONT-002-DESIGN.md`, `docs/research-proposal.md` (CONT-002 clause), `docs/SESSION-BRIEF-CONT002.md`, `experiments/suite-v3/power_calc_cont002.py` + `power-results-cont002.json`, `fixtures/v3k` (manifest + dr-5301/dx-5401/gc-5501 sampled), `build_v3k.py`, `validate_fixtures_v3.py` + `fixture-validation-v3k.json`, `SUITE-V3-DESIGN.md` §3, the M2b artifacts (`results/CONT-000/cont002-mechanics-20261001-225738/`), and the validator git-diff d075872..afb2178
- **Verdict: GO-with-changes — 5 required changes (RC-1..RC-5), all document/validator-level, zero GPU.** All RC folded the same day by the implementing agent (disposition below) + verify-pass. This file is the frozen review record.

---

## Raw review (Fable, verbatim)

Всі матеріали прочитані й перехресно звірені. Нижче повний звіт рев'ю (пісочниця заблокувала виконання Python — валідатор, детермінізм білдера і перерахунок digest перевірені лише документально; це явно позначено).

---

# PR-REVIEW-CONT002 — приймальний огляд EVALUATION-PREP-CONT002 (DRAFT) до FREEZE

- **Рев'юер:** модель "Fable" (Claude Code CLI), свіжий контекст, non-executor, read-only, запуск з кореня репо.
- **Дата:** 2026-10-07, ДО фризу і до будь-якого CONT-002 інференсу.
- **Об'єкт:** `docs/EVALUATION-PREP-CONT002.md` (DRAFT) проти `docs/PREREG-REQUIREMENTS-V2.md` (9 пунктів), `docs/CONT-002-DESIGN.md`, `docs/research-proposal.md` (CONT-002), `docs/SESSION-BRIEF-CONT002.md`, `power_calc_cont002.py` + `power-results-cont002.json`, `fixtures/v3k` (manifest + dr-5301, dx-5401, gc-5501 вибірково), `build_v3k.py`, `validate_fixtures_v3.py` + `fixture-validation-v3k.json`, `SUITE-V3-DESIGN.md` §3, M2b-артефакти (`results/CONT-000/cont002-mechanics-20261001-225738/`), git-дифф валідатора `d075872..afb2178`, LOG.md tail.
- **Обмеження виконання:** sandbox заблокував запуск `validate_fixtures_v3.py` (v3k та регресії) і повторний прогін білдера/digest — ці пункти верифіковані документально (закомічений вердикт + дифф коду), не виконанням.
- **Вердикт: GO-with-changes — 5 обов'язкових змін (RC-1..RC-5), усі документ/валідатор-рівня, нуль GPU.**

---

## A. Вимірність — ✅

- Endpoint вимірюється наявним harness: `src/continuity/runner.py:94` (`extract_label`) + `score_probe` (:112) реалізують правило, заморожене посиланням у §9 драфту на SUITE-V3-DESIGN §3 (декларація 2026-10-05: standalone-мітка, PASS iff рівно одна відмінна мітка і вона очікувана). Посилання коректне, digest обіцяно записати при FREEZE.
- Чотири клітинки визначені операційно (§1, таблиця), digest обох ядер збігаються з `model-digests.json` M2b (granite `36c3c3b9683b…`, qwen `8a0fd5da454e…`). Механіка export→import→render-into-context доведена M2b 5/5 (`checklist.json`).
- Урок PR-REVIEW-v3 REQUIRED #2 засвоєний: freeze-маніфест (§10) явно включає І pilot GO/NO-GO-скрипт, І confirmatory-скрипт, «written FIRST, before any v3k inference». Розрив іншого роду — ніхто не перевіряє, що ці скрипти коректно реалізують §2/§4–§6 (див. RC-4).

## B. Відтворення клаузули інспірера — ✅ (з одним каналом, закритим у RC-2)

- **Дослівність:** blockquote у CONT-002-DESIGN §1 звірений слово-в-слово з `research-proposal.md:126` — ідентичний, включно з фінальним «do not cherry-pick another denominator or claim successful transfer». Пререєстрація відтворює його за змістом у §4 з прямим маркером «verbatim intent of the inspirer's clause».
- **Повнота вимог клаузули:** «Pre-register aggregation» — §3/§7 ✓; «minimum meaningful ΔA» — 0.30 ✓; «target ratio/uncertainty criterion» — MME R=0.25 + 95% cluster-bootstrap CI ✓; «treatment of negative values» — reported as-is, never clamped, harm-гілка окремим вердиктом ✓.
- **Числовий estimability gate** (ΔA ≥ 0.30 AND CI виключає 0) — легітимна операціоналізація «zero or too close to zero»; додатковий запобіжник unstable-denominator (ΔA* ≤ 0.05 у >10% дро) сильніший за мінімум клаузули.
- **Канали denominator cherry-picking:** головний текст чистий (гілка 1 §6: «no ratio, no transfer claim, no alternative denominator»). Але §8 беззастережно обіцяє «Per-family R (DR-only vs DX-only)» як secondary: якщо pooled ΔA не пройде гейт, а ΔA_DR пройде, опублікований R_DR — це де-факто альтернативний знаменник у тому ж run record. Формально «not promotable», але клаузула інспірера забороняє саме цей клас звітування → RC-2.
- **Чесність non-estimable гілки:** так — пілотний критерій 3 заздалегідь декларує ризик власнику ДО confirmatory, прогін «for diagnostic deltas» — owner decision, recorded either way. Також звірено: «Clean controls … differ only in the learned persistent state / match context budgets» з клаузули — обмеження «no length-matched control» чесно задеклароване (§8, §14).

## C. Статистична честність — ⚠️ (модель чесна, але є задекларовані межі; одна темпоральна суперечність → RC-1)

**(a) Ratio of means — коректно.** R = (mean ΔB_c)/(mean ΔA_c), «never a mean of per-cluster ratios» (§3) — правильний вибір: per-cluster відношення вибухають на малих ΔA_c (при 7 бінарних пробах ΔA_c ∈ {−1…1} з кроком 1/7, нулі ймовірні). Повторне використання тих самих resample-індексів для CI(ΔA) і CI(R) (§4.2) зберігає кореляцію чисельника і знаменника — чисто. Degenerate-guard задекларований і відтворений у симуляції (`power_calc_cont002.py:86-89`).

**(b) Де модель power_calc може обманювати.**
- *Спільний eps per cluster-seed* (рядок 71-75): виправдання реальне — всі чотири клітинки бачать той самий рендерений контент (`render_seed_variant` без аргументу ядра, fixtures.py:89 — підтверджено кодом). До кліпінгу eps скасовується всередині ΔA і ΔB точно. Два чесні застереження: (i) кліпінг ламає скасування: при bAs=0.90 зі сумарним sd ≈0.224 стеля 0.98 стискає реалізовану ΔA нижче латентної 0.75 (≈0.69), тоді як ΔB-латент фіксований абсолютно (r·0.75) — реалізоване відношення трохи ВИЩЕ номінального 0.25, тобто «power at R 0.25» містить невелику оптимістичну домішку; (ii) повне розділення eps між ядрами — припущення: якщо профіль складності контенту для B відрізняється від A, кореляція ΔA–ΔB у реальності нижча, R-CI ширший, power завищений. Декомпозицію shared-vs-cell двосідовий пілот ідентифікувати не може — re-check по spread це покриває лише частково. → N-1 (у final record).
- *eta per cell* названа power killer чесно і керує стрес-рядами (R6/R7 → 0.767/0.720) з pre-declared governance (владний sign-off). На відміну від старого power_calc_v3 (зауваження мого PR-REVIEW-v3 п. B3), eps тут per cluster-seed, не спільний на всі кластери — покращення.
- Біноміальний шум n=1 на cluster-seed-cell змодельований явно (rng.binomial) — головне джерело недорозмірності К12×5 ідентифіковане правильно.

**(c) Established ≈0.5 на MME і false positive — задекларовано чесно.** §5: «bounding that branch near 0.5 at exactly the MME (0.477 in the artifact) — declared openly»; артефакт R2 підтверджує 0.477, R9 — 1.000 при R=0.5, R11 — detection 0.033 / established 0.002 при R=0. Усі числа драфту звірені з `power-results-cont002.json` — збігаються (R2 0.801, R6 0.767, R7 0.720, R3 0.604, R4 0.692, R5 0.735, R13 0.819, R14 0.617, R12 harm 0.697). Цикл-2 прецедент дотримано.

**(d) Sizing 12×5 → 15×7 — легітимний design-time sizing, не reverse-engineering.** Критерій: MME зафіксований змістовно (0.25 = house convention, обґрунтування «justifies importing state as the default over re-telling») і НЕ рухався; нарощено розмір вибірки (кластери до стелі amendment-c + сіди), недорозмірені рядки R3–R5 збережені в артефакті «for the record»; все зроблено до будь-яких даних (zero GPU milestone). Це рівно те, чого вимагає шаблон §6 («fails template review» при <80% на MME). Жодних слідів підгонки MME під досяжну потужність.

**Темпоральна суперечність (головна знахідка):** §10 фіксує ОДИН freeze, §13 ставить його ДО пілоту — але §5 обіцяє «R_MME is re-derived **at freeze** so that R_MME × ΔA_measured clears the band» на основі **pilot-measured ΔA**, і «**Freeze-time** power re-check … with the pilot-measured ΔA and per-cell between-seed spread». Дані пілоту при freeze не існують. Додатково тригери конфліктують: §2 критерій 3 — «if ΔA < 0.45 the MME re-derivation path of §5 fires at freeze», §5 — «if the pilot ΔA < 0.60». → RC-1.

## D. Контамінація / дизайн-луп — ⚠️ (схема в цілому закрита; залишковий канал = RC-1)

Схема «пілотні сіди {5001,5002} у фінальному датасеті при одному freeze» захищена трьома механізмами, і всі три реальні: (i) весь аналітичний код (pilot + confirmatory) у freeze-маніфесті ДО будь-якого інференсу — пілотні дані не можуть сформувати аналіз; (ii) NO post-pilot fixture edits, rebalance = новий суіт + нове рев'ю (§2) — не можуть сформувати стимули; (iii) GO/NO-GO = стоп на owner gate, «never triggers re-authoring» (§2). Залишкові канали:

1. **MME-re-derivation (§5)** — єдиний протокольний параметр, що легально рухається після пілоту, на даних, які входять у фінальний датасет. Напрямок руху конструктивно консервативний (R_MME лише зростає, щоб ΔB-кліренс guess band виконувався — підняття планки, не опускання), але формула не зафіксована точно («so that … clears the band» лишає свободу) і момент названий «at freeze» — суперечність п. C. Закривається RC-1 (точна формула + checkpoint пілотного гейту + owner-visible).
2. **Селекційний зсув GO-умови:** confirmatory відбувається лише якщо 2-сідова ΔA ≥ 0.45 → фінальна оцінка ΔA умовно завищена (сіди, що пройшли поріг, лишаються в датасеті). Для R це консервативно (більший знаменник → менший R), для проходження estimability gate — антиконсервативно. Малий ефект, але має бути acknowledged → N-2.
3. Виконавець бачить пілотні виводи до confirmatory, але не має легального важеля: run-скрипт, фікстури, аналіз — усе заморожене, hotfix-класи §11 перелічені вузько, relaxation гейтів іде через non-executor сесію. Закрито.

## E. Сюіт і валідатор — ✅ (одна stale-документація у файлі, що буде заморожений → RC-3; регресії — виконавче самосвідчення → RC-4a)

- **dr-5301:** s1 — код + NON-label companion (анти-echo збережений), s2 — chore, s3 — ack + label-form проба k=6; по 7 сідах коди/companion/chore/role відмінні, порядки міток попарно різні, позиція expected гуляє (слоти 0,5,4,3,2,1,0) — відповідає V15/V16. ✓
- **dx-5401:** lure заявлений у s1 learning-повороті («the trap room crate code is {lure}»), присутній в опціях кожного сіда, ≠ expected; `lure_value` задекларований для V8R. ✓
- **gc-5501:** never-stated, expected null, 7-словні пули зі сковзним 6-словним вікном — k=6 збережене, набори та порядки опцій відмінні per seed (рішення під «7 сідів > 6 ротацій» пояснене в коді білдера :302-304). ✓
- **Клас `transfer_eligible`** на пробі, остання сесія, рівно одна проба — V11 параметризований через `PROBE_CLASS` (validate_fixtures_v3.py:118-124, :500). ✓
- **Чи не ослабило розширення старі чеки — перевірено git-диффом `d075872..afb2178`:** V1 `expected_families` тепер зі `FAMILY_PLANS` — для v3/v3h/v3i/v3j множини ідентичні старій формулі; V7 замість трьох часткових умов — `fam_counts == family_plan` (строго сильніше); маршрутизація V8/V8R через `primary_families <= TRAP_PRIMARY_FAMILIES` лишає старий V8-код байт-у-байт для trap-суітів. Ослаблення немає; V7 посилений.
- **Але:** (i) docstring валідатора (:25-26) і коментар (:57-58) кажуть «DR x6 + DX x6 = 12 recall clusters», тоді як код і суіт — 7+8=15 — застаріла自-суперечність у файлі, що входить у freeze-маніфест → RC-3; (ii) «регресії v3/v3h/v3i/v3j PASS» існують лише як заява в LOG: закомічені `fixture-validation-v3*.json` старих суітів датовані d075872/a6a0529 (до зміни валідатора) і не можуть бути перезаписані (заморожені записи). За шаблоном §4 самосвідчення виконавця гейтом не є → RC-4a. Сам я прогнати регресії не зміг (sandbox).
- `fixture-validation-v3k.json`: PASS 16/16, 126 інстансів, V5 max share 0.18, suite sha256 `06b897f6…` — узгоджено з LOG; перерахувати digest самостійно не зміг (sandbox).
- Білдер `build_v3k.py`: RNG-вільний, explicit tables, «re-running overwrites byte-identically» — grep на random/time/uuid чистий; детермінізм повторним прогоном не перевіряв (sandbox).

## F. Покриття шаблону PREREG-REQUIREMENTS-V2 — 9/9, з них 2 з натяжками

| Пункт шаблону | Де в драфті | Статус |
|---|---|---|
| §1 frozen analysis code | §10 (обидва скрипти + run-скрипт + runner/provider/memory/fixtures + сіди) | ✅ чисто (урок PR-REVIEW-v3 #2 враховано); гейт не перевіряє коректність скриптів → RC-4b |
| §2 infrastructure clause | §11 (класи перелічені; rendering-фікси лише до інференсу стадії; relaxation → гейт-сесія + header) | ✅ чисто |
| §3 multi-rev pre-declared | §11 («attempt counts and revs stated exactly») | ✅ чисто |
| §4 non-executor gates | §12 + черга Fable→Opus→GLM; verdict files до читання результатів | ✅ чисто; склад гейт-інструкцій доповнити (RC-4) |
| §5 wall-time reconciliation | §11 (cell = Σ attempts, cluster = Σ cells, run = Σ clusters per core; `summary_rebuilt_offline`) | ✅ чисто, навіть деталізованіше за шаблон (per-cell) |
| §6 power section | §5 + артефакт (K=15, n=7, метод ≥ power_calc.py, MME, 0.801 на MME) | ✅ чисто; числа звірені з артефактом |
| §7 droppable-secondary | §2 крит.2 + §7 (GC droppable, primary untouchable) + §13 primary-first | ✅ чисто |
| §8 carried-over notes | §12 останнє речення («every PR-REVIEW-CONT002 note reappears…») | ✅ чисто |
| §9 guessing band | §5 (ΔB-scale clearance: 0.25×ΔA ≥ max(0.15, 2×band)) + §12 (empirical rate поруч із числами; caveat не рухає MME) | ⚠️ натяжка: сам механізм правильний (MME на шкалі R потребує трансляції в ΔB — зроблено), але re-derivation прив'язана «at freeze» до пілотних даних — темпоральний розрив RC-1 |

Друга натяжка — §1: аналітичні скрипти в маніфесті Є, але на момент рев'ю не існують (авторинг при freeze); шаблон це дозволяє, однак це означає, що найважливіший код проходить повз незалежне рев'ю — компенсується RC-4b.

## G. Feasibility (B-ядро) — ✅ з однією чесністю, яку треба сказати прямо (N-3)

- Базові числа M2b підтверджені артефактами: B load+warmup 39.6 s, B+state проба 8.9 s (318 ток.), B+clean ramble 73.5 s (2726 ток., `num_predict` 256), A learn 8.8 s (per-cell `summary.json`, `model-digests.json`). Аргумент «73.5 s — це v1-ера contains-проба без опцій; v3k label-form з опціями дасть коротші відповіді» — правдоподібний, але неперевірений; дизайн чесно делегує це пілоту.
- Моя арифметика гіршого випадку: B-side no-record поворотів 42/сід (B+clean 30 + GC-B 12); якщо ВСІ ramble на капі (73.5 s) → ≈54 хв/сід лише B-side → ≈6.3–6.6 год на 7 сідів, плюс A-side ~1–1.75 год — **кап 5.5 год пробито**, а задекларований трим GC-B (сіди 5005–5007, ~36 поворотів) економить лише ~40-45 хв і не рятує. Отже реальний backstop гіршого випадку — NO-GO пілотного критерію 2, не трим. Механізм у драфті Є (екстраполяція → трим або NO-GO), але риторика «declared trims are applied» створює враження, що трим достатній → N-3 (сказати прямо).
- Некомплаєнтний B (пілотна клаузула 1): NO-GO на owner gate, prompt-template фікси — owner-gated decision class, ніколи in-place after inference; ratio «voided of meaning» — вердикт не видається, арка стоїть. Чесно. Проміжний випадок (invalid 0.10–0.29, гейт пройдено) атенуює ΔB і тисне R вниз — консервативний напрямок, декомпозиція §8 це зробить видимим. Прийнятно.

## H. Порожнини — що драфт НЕ покриває і треба до/при фризі

1. **Run-скрипт** (learn/probe split, store preload, model pinning, budget stops, wall-accounting) — не написаний; у маніфесті є, гейт перевіряє «four-cell wiring», але не перевіряє, що **A+clean і B+clean справді стартують з порожнього store** (ізоляція клітинок) — додати в гейт-інструкції §12 (вміщено в RC-4b/N-5).
2. **Коректність аналітичних скриптів** — жоден гейт не звіряє frozen pilot/confirmatory скрипти з §2/§4–§6 (RC-4b).
3. **Визначення «invalid-format share»** для пілотного критерію 1 не зафіксоване в тексті пререєстрації (RC-5).
4. **Поводження виродженых bootstrap-дро** (ΔA* ≤ 0 → inf/nan у R*; до 10% дегенератів допустимі й можуть торкнутись 2.5%-перцентиля) — має бути специфіковане у frozen-скрипті (N-4).
5. **Environment pin:** Ollama 0.34.2 зафіксований у M2b, але пререєстрація не обіцяє записати версію Ollama/offload-конфігурацію у freeze/run record (N-5).
6. State-integrity guard («zero probe-session content in exports») — реалізовний: export-схема несе `episode_refs` виду `s1t1|environment` (M2b check 2), структурна перевірка can be mechanical. Wall-time per-cell — `duration_s` у summary вже існує. Обидва реалізовні, порожнин немає.

## I. Вердикт

### **GO-with-changes** — усі зміни документ/валідатор-рівня, нуль GPU, до FREEZE.

**Обов'язкові зміни:**

- **RC-1 (темпоральна узгодженість MME-механіки; §2 критерій 3, §5).** Замінити обидва «at freeze» для дій, що залежать від pilot-measured ΔA/spread, на явний **pilot-gate checkpoint** (після пілотного аналізу, до confirmatory, owner-visible); узгодити тригер re-derivation (зараз §2 каже ΔA < 0.45, §5 — ΔA < 0.60 — лишити один, із поясненням зв'язку порогів 0.30/0.45/0.60); зафіксувати точну формулу, напр. `R_MME' = max(0.25, max(0.15, 2×band_max)/ΔA_measured)`, з явною нормою, що MME може рухатися **лише вгору** (консервативно) і що це pre-declared adjustment path, а не post-hoc. Обґрунтування: при одному freeze до пілоту (§10, §13) теперішнє формулювання або нездійсненне, або легалізує post-freeze зміну вирішального параметра на даних фінального датасету.
- **RC-2 (закрити backdoor знаменника; §8, перший bullet).** Додати: у гілці non-estimable НЕ обчислюється і не звітується жодне відношення, включно з per-family R; per-family R видається лише якщо pooled estimability gate пройдено (і бажано — з тим самим degenerate-flag правилом per family). Обґрунтування: клаузула інспірера прямо забороняє альтернативні знаменники; R_DR при проваленому pooled-гейті — саме такий канал.
- **RC-3 (самосуперечність у замороженому файлі; `validate_fixtures_v3.py:25-26, 57-58`).** Виправити docstring/коментар «delayed_recall x6 + distractor_recall x6 (12 recall clusters)» → «x7 + x8 = 15» до фризу. Обґрунтування: файл входить у freeze-маніфест; гейт-сесія звірятиме суіт проти документації валідатора — заморожена суперечність провокує хибні тривоги або, гірше, звичку їх ігнорувати.
- **RC-4 (гейт-інструкції §12, два доповнення).** (a) Гейт-сесія повторно проганяє регресії `--suite v3/v3h/v3i/v3j` і комітить НОВИЙ зведений regression-verdict артефакт (не перезаписуючи заморожені `fixture-validation-*.json`): зараз «regressions PASS» існує лише як запис виконавця в LOG, а закомічені вердикти старих суітів датовані до зміни валідатора — за шаблоном §4 це самосвідчення, не гейт. (b) Гейт верифікує, що заморожені pilot GO/NO-GO і confirmatory скрипти реалізують правила §2/§4–§6 (мінімум — dry-run на синтетичному вході з відомою відповіддю), і що run-скрипт стартує clean-клітинки з порожнього store. Обґрунтування: обидва скрипти авторяться ПІСЛЯ цього рев'ю — єдиний незалежний погляд на них інакше не відбудеться ніколи.
- **RC-5 (визначення критерію GO/NO-GO №1; §2).** Зафіксувати в тексті пререєстрації числове визначення «invalid-format share»: частка проб, де `extract_label` повертає нуль або більше однієї відмінної standalone-мітки (формат-miss за декомпозицією §8), на знаменнику 15 кластерів × 2 сіди = 30 проб/клітинку. Обґрунтування: це стоп-критерій усієї арки; його визначення не може жити лише в тілі скрипта, який ще не написаний.

**Необов'язкові нотатки (за шаблоном §8 мають повторитися у фінальному run record):**

- **N-1.** Power-модель: (i) кліпінг [0.02, 0.98] при bAs 0.90 стискає реалізовану ΔA (≈0.69 проти латентної 0.75), тож реалізоване відношення на «рядку R 0.25» трохи вище номінального — невелика оптимістична домішка в headline 0.801; (ii) повний shared-eps між ядрами — припущення, що завищує кореляцію ΔA–ΔB (вужчий R-CI); двосідовий пілот не ідентифікує декомпозицію shared-vs-cell. Обидва застереження — у final record поруч із power-числами.
- **N-2.** GO-умова пілоту (ΔA ≥ 0.45 на 2 сідах, що входять у фінальний датасет) створює малий селекційний зсув ΔA вгору: консервативно для R, антиконсервативно для проходження estimability gate — acknowledged у final record.
- **N-3.** Гірший випадок B-side (усі 42 no-record повороти/сід на капі 73.5 s) ≈ 6.3–6.6 год — перевищує кап 5.5 год, і трим GC-B (~40-45 хв) його не закриває; сказати в §2/§13 прямо, що backstop гіршого випадку — NO-GO, а трим покриває лише помірний перебір.
- **N-4.** Frozen-аналіз має специфікувати поводження bootstrap-дро з ΔA* ≤ 0 (inf/nan/зміна знаку R*) — при допустимих до 10% дегенератів вони можуть сягати 2.5%-перцентиля.
- **N-5.** Зафіксувати у freeze/run record версію Ollama (M2b: 0.34.2) і offload-конфігурацію B-ядра — wall-time-висновки і феноменологія ramble чутливі до них.
- **N-6.** Межі цього рев'ю: sandbox заблокував виконання — валідатор (v3k + регресії), детермінізм `build_v3k.py` і перерахунок suite sha256 перевірені документально (закомічений вердикт 16/16, git-дифф валідатора, grep білдера), не прогоном. RC-4a конвертує цю прогалину в механічну перевірку гейтом.

**Підсумок одним рядком:** дизайн і пререєстрація — найчистіші в лабораторії на сьогодні (клаузула інспірера відтворена дослівно і операціоналізована чесно, sizing легітимний, контамінаційна схема одного freeze майже закрита); єдина змістовна вада — MME-re-derivation, «прибита» до неіснуючого моменту часу, плюс чотири дешеві документальні закриття. Після RC-1..RC-5 — GO на owner gate.

---

## Executor curation of the review's load-bearing claims

Standing rule (owner directive 2026-10-07: curatorial verification of reviewer claims is mandatory). Every load-bearing claim re-verified by the implementing agent against the repo before folding:

1. **RC-3 (stale validator documentation): CONFIRMED.** `validate_fixtures_v3.py` docstring (lines 25-26) and the EXPECTED_PRIMARY comment (line 58) said "DR x6 + DX x6 (12 recall clusters)" / "DR+DX=12" while the code and suite are 7+8=15 — the resize to 15×7 missed the prose. Fixed.
2. **RC-1 (temporal contradiction): CONFIRMED.** Prereg §2 clause 3 anchored the ΔA<0.45 path "at freeze", §5 anchored the ΔA<0.60 re-derivation "at freeze"/"freeze-time power re-check", while §10/§13 put the single FREEZE before the pilot — pilot-dependent actions could not legally execute at freeze. The two thresholds also stood unexplained next to the 0.30 gate floor. Fixed via the threshold ladder (0.30/0.45/0.60) + the pilot-gate checkpoint + the frozen upward-only formula.
3. **RC-4a (regression evidence is executor self-attestation): CONFIRMED.** The committed `fixture-validation-v3.json`/`-v3h`/`-v3i`/`-v3j.json` are dated d075872 (2026-10-06, before the v3k validator extension at afb2178); the post-extension PASS runs existed only in the executor's LOG/console. The gate instruction (a) now assigns the regression artifact to the non-executor gate session.
4. **RC-2 (per-family R backdoor): CONFIRMED** by reading prereg §8 first bullet as drafted — it promised per-family R unconditionally; under a failed pooled gate an R_DR would have been an alternative denominator in the same run record. Gated.
5. **RC-5 (undefined stop criterion): CONFIRMED** — "invalid-format share" appeared in §2 clause 1 without a definition in the prereg text. Defined.
6. **Artifact numbers:** R2 0.801 / estab 0.477 / FP 0.033 / harm 0.697 / R3-R5 sizing rows / R13 0.819 / R14 0.617 — all reproduce from `power-results-cont002.json` (the reviewer read the committed artifact; the implementing agent re-read it alongside).
7. **N-3 arithmetic:** 42 no-record B turns/seed × 73.5 s ≈ 51.4 min/seed → ≈6.0 h over 7 seeds (reviewer said 6.3–6.6 including per-process load overheads) — exceeds the 5.5 h cap; GC-B trim (~40–45 min) does not close it. Reproduced; the NO-GO-is-the-backstop wording now states it plainly.
8. **M2b numbers** (39.6 s load, 8.9 s B+state, 73.5 s B+clean 2726 tokens, 8.8 s A learn): reproduce from `model-digests.json` + per-cell `summary.json`.
9. **Reviewer execution limits (N-6):** the reviewer's sandbox blocked running the validator/builder/digest recomputation — those verifications remain documentary here and are converted into mechanical gate checks by RC-4a/(b). The implementing agent's own post-fold run: validator v3k + v3/v3h/v3i/v3j all PASS (console, exit 0 each).

## Disposition of RC / N (fold record)

| Item | Change folded | Where |
| --- | --- | --- |
| RC-1 | "at freeze" pilot-dependent actions → pilot-gate checkpoint (after frozen pilot analysis, before confirmatory, owner-visible); threshold ladder 0.30 (gate floor) / 0.45 (pilot GO floor) / 0.60 (re-derivation trigger) stated once; frozen formula R_MME' = max(0.25, max(0.15, 2×band_max)/ΔA_measured), upward-only | prereg §2 clause 3, §5; design §4 synced |
| RC-2 | per-family R computed/reported ONLY if the pooled estimability gate passed; non-estimable branch computes NO ratios of any kind | prereg §8 first bullet |
| RC-3 | docstring "x6 + x6 (12)" → "x7 + x8 (15)"; comment "DR+DX=12" → "=15" | validate_fixtures_v3.py (pre-freeze file edit; suites re-validated PASS) |
| RC-4 | gate instructions extended: (a) non-executor re-runs regressions v3/v3h/v3i/v3j and commits a NEW consolidated regression artifact (frozen per-suite JSONs untouched); (b) gate verifies frozen pilot/confirmatory scripts against §2/§4–§6 via synthetic-input dry-run + clean-cell empty-store isolation | prereg §12 |
| RC-5 | invalid-format share defined in the prereg text (zero or >1 distinct standalone label under extract_label; denominator 15×2=30 probes/cell) | prereg §2 clause 1 |
| N-1, N-2 | carried-note obligations named explicitly (power-model caveats beside power numbers; pilot-GO selection bias in run-record header) | prereg §12 |
| N-3 | worst case (~6+ h B-side) stated plainly; NO-GO is the backstop, trim covers only moderate overrun | prereg §2 clause 2 |
| N-4 | degenerate-draw handling specified for the frozen script (ΔA*≠0 rule, non-finite count recorded) | prereg §4.2 |
| N-5 | environment pin: Ollama version + core-B offload config in freeze manifest and every run record | prereg §10 |
| N-6 | acknowledged; converted to mechanical gate checks via RC-4 | this appendix |

## Verify-pass (post-fold)

- Validator: v3k + regressions v3/v3h/v3i/v3j — **PASS ×5** after the RC-3 file edit (docstring-only; no logic change).
- Grep: no pilot-dependent "at freeze" remains in the prereg (remaining occurrences: digest/RNG/wording freezes and the RC-1 clarifying text itself).
- RC-2/RC-5 text present verbatim in §8/§2; RC-1 ladder + formula present in §2/§5; RC-4 (a)/(b) present in §12; N-3/N-4/N-5 folded at §2/§4.2/§10.
- No frozen artifact touched: fixture-validation-*.json for v3/v3h/v3i/v3j unmodified; fixtures/v3k unmodified (suite sha256 06b897f6e727a0cc… unchanged).

**Post-fold verdict: GO — the pre-registration proceeds to the owner gate** (explicit owner acceptance before ANY behavioral run; never-autonomous clause).
