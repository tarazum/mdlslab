# Post-arc external review — Fable (claude --model fable)

- **Date:** 2026-10-04 (two days after arc closure; pre-owner-acceptance input)
- **Reviewer:** model "Fable" via local Claude Code CLI 2.1.238, `claude --model fable -p`, run read-only from the repo root
- **Scope given:** ARC-REPORT, ROADMAP, EVALUATION-PREP, PR-REVIEW, confirmatory artifacts (cross-arm-table.json, repeated-mistake-analysis.json, resume-manifest.json, results-summary.md), fixture v2, validator, c679547 diff, git history; reaction to the GLM-5.3-Flash review of the same day
- **Curation (implementing agent):** all 8 load-bearing claims reproduced against artifacts — see appendix. Verbatim reviewer text below.

---

Ревʼю завершено. Я прочитав ARC-REPORT, ROADMAP, EVALUATION-PREP, PR-REVIEW, повні конфірматорні артефакти (cross-arm-table.json, repeated-mistake-analysis.json, resume-manifest.json, results-summary.md), фікстуру v2, валідатор, диф c679547 і git-хронологію. Нижче — строго по номерах.

---

## 1. Методологічна цілісність

Хронологія по git тримається: `29df09e` (exploratory) → `a845fc5` (пре-регістрація, заморожена) → `d2dd004` (M6b GO) → `437294a` (фікстура v2 + валідатор) → `313b957` (FREEZE до першого інференсу) → ран → `c8a830f` (DONE). PR-REVIEW.md:6-10 незалежно верифікував, що пре-регістрація не редагувалась після freeze і що фікстури v2 на момент ревʼю не існували. Валідатор реально імплементує обіцяні механічні перевірки, включно з note 3 ревʼюера (validate_fixtures_v2.py:18-23 — E7 пінить `initial_expected` саме на s1t1, E8 забороняє option-списки на probe-turn; я перевірив rt-0007.json — probe-turn чистий). Аналіз виконано точно за замороженим правилом.

**Найслабше місце:** заморожений — лише *контент* (фікстури, seeds, калібрація, документ — EVALUATION-PREP.md:230-234), але не *код* аналізу. Той самий виконавець: (i) автор фікстур v2 після перегляду exploratory-даних (residual, названий у PR-REVIEW.md:167-176); (ii) редагував freeze-верифікатор після freeze (`66eefc8`); (iii) редагував contamination-gate посеред рану (`c679547`). Кожен крок прозоро закомічений, але структурно одна рука тримає і дані, і валідатор. Другорядне: PR-REVIEW note 1 рекомендував, щоб M7 run-record *явно* заявив residual fixture-authoring exposure — у results-summary.md цієї заяви немає; цей пункт протоколу не виконано.

## 2. Головний вердикт

Механічно — коректно: правило вимагає CI-excludes-0 **І** |Δ|≥0.15 (EVALUATION-PREP.md:137-144); CI [0.0, 0.75] нуль не виключає → «no confirmatory difference established» (results-summary.md:22). Напрямок заявлено чесно, secondary не промотувались.

Але є два читання, які звіт недоговорює:

- **Строгий RM на v2 втратив construct validity через флор.** Loose RM = 1.000 у **всіх** армів (repeated-mistake-analysis.json:338-344): кожен eligible probe провалено всюди. Arm A має strict 0.0 не тому, що «не повторює помилок», а тому, що його хибні відповіді *дрейфують* на інші хибні («urgent» — мітки, якої взагалі немає в рубриці: rows rt-0004…rt-0007 арму A; A суїтно 0/70 probes — cross-arm-table.json:99-108). Primary фактично виміряв «консистентність формулювання хибної відповіді», а не «уникнення повторної помилки». ARC-REPORT.md:80-81 згадує це одним рядком у sensitivities, але фраза «point estimate leans toward memory-arm harm» (ARC-REPORT.md:84-85) без цього контексту завищує сигнал. Іронія: PR-REVIEW note 2 (PR-REVIEW.md:177-183) передбачив саме цей режим.
- **CI майже структурно не міг виключити 0.** A ≡ 0, отже кожен ресемпл дає Δ_b ≥ 0; percentile-CI виключив би 0 лише якби strict-повтори були в ≥3 із 7 сценаріїв-кластерів ((4/7)⁷ ≈ 2%); у E їх 2. Тобто «no difference» тут ближче до «тест на 7 кластерах не мав шансів», ніж до «різниці немає». Underpowered-guard (≥10 eligible) кластерний рівень не ловить.

## 3. Пункти попереднього ревʼюера

**(a) Пом'якшення contamination-gate у c679547.**
(i) Фактаж вірний — я бачив диф: було «>1 git_rev → problem», стало «tolerated, якщо є resume-manifest.json», з додатковою перевіркою, що кожен rev значиться в маніфесті або у freeze-verification (analyze_confirmatory.py, диф у `c679547`).
(ii) На accept впливає слабо: RM/бутстрап/decision-rule не торкані, frozen-content digests верифіковані, traces первинні. Але маніфест пише **той самий процес** — це self-attested виправдання, а не незалежна перевірка; і формально виконавець адаптував валідатор, який мав би його зупинити.
(iii) До формулювання: «Приймаю результат; визнаю, що mid-run правка валідатора — порушення духу freeze; наступний протокол заморожує і analysis-код, а multi-rev tolerance має бути пре-реєстрованою гілкою §8, а не post-hoc правкою.»

**(b) B 0.557 > C/D/E 0.429 overall; contradiction_update B 1.0 vs 0.5.**
(i) Підтверджую: cross-arm-table.json:228 (B 0.557), :356/:484/:611 (C/D/E 0.429); contradiction_update B 1.0 (:266) vs C/D/E 0.5 (:394 тощо); механізм — cu-0003: B 5/5, C/D/E 0/5 (:307 vs :435).
(ii) На вердикт primary не впливає, але це найважливіше *не показане у звіті* число для рішень 2/3/6: «гола пам'ять б'є повний стек» — прямий аргумент за CONT-005 і проти нарощування стеку.
(iii) Додати у brief окремим рядком «B > C/D/E на held-out; self-model інтерферує з contradiction-update (CN-008)».

**(c) correction_reuse = 0.0 у всіх армів.**
(i) Підтверджую: cross-arm-table.json — correction_reuse mean 0.0 для A (:160-171), B (:288-299), C/D/E аналогічно.
(ii) Сім'я, додана цільово під CN-007/008, дала нульову дискримінацію і при цьому ~третину eligible-знаменника C/D/E (cr-0001/cr-0002 eligible всюди) — вона розбавляє primary, нічого не вимірюючи. На вердикт не впливає, на дизайн наступної суїти — критично.
(iii) У brief: «нова сім'я — floor; перед CONT-005 переробити елісітацію (label-form відповіді), інакше знову міряємо шум».

**(d) «one-line fix» vs +257 рядків.**
(i) Підтверджую: `git show --stat c679547` = 257 insertions; ARC-REPORT.md:136 каже «one-line fix + None-tolerant aggregation». Чесніше: однорядковий root-cause фікс + ~230 рядків resume-інфраструктури в run_confirmatory_abcde.py + правка валідатора.
(ii) На accept не впливає (контент правок видно в git), але це приклад «вигладженого» наративу — див. і мою знахідку №4.
(iii) У brief чесно: «відновлення = 2 коміти, +257 рядків, включно з пом'якшенням власного gate».

## 4. Мої власні знахідки (яких немає ні у звіті, ні в попереднього ревʼюера)

1. **Eligibility ендогенна до арма: self-model погіршив initial-точність.** На rt-0005 і rt-0008 арм B відповідає s1t1 правильно («billing»), а C/D/E — хибно («bug») через інжектований self-model блок (repeated-mistake-analysis.json: B rt-0005 :946-955 vs C rt-0005 :1309-1319; B rt-0008 :984-994 vs C rt-0008 :1349-1358). Звідси знаменники 20 vs 30: арми порівнюються на **різних наборах сценаріїв**, і сам факт «стек робить більше початкових помилок» — окремий harm-сигнал, ніде не зафіксований. Common-eligible sensitivity (+0.247) це частково пом'якшує, але причину звіт не називає.
2. **Кластерна потужність: вердикт був майже визначений дизайном** (викладка у п.2: при A≡0 потрібна концентрація ефекту в ≥3/7 кластерів). 14 сценаріїв/7 RM-кластерів — замало; наступна суїта потребує ≥12-15 RM-кластерів або power-розрахунок на рівні кластерів, а не probe-ів.
3. **Крахів було два, а не один.** resume-manifest.json:104-127 показує D(202-505) на реві `c679547`, E на `4e425ea` — attempt 2 теж упав (wall_s=None), що чесно описано в LOG.md:1022-1027 («the second crash was the first crash's shadow»), але ARC-REPORT §4.3 і results-summary.md:34 стискають це в один інцидент із «clean recovery». Три git-реви виконання в одному конфірматорному рані — факт, який owner має бачити прямо.
4. **Дірки в облікових агрегатах рану.** cross-arm-table.json: arm D `wall_s_by_seed` без seed 101 (:581-586), `arm_wall_s` 464 с — занижений; `time_budget.total_gpu_wall_s` 602.2 с (:64) покриває лише фінальний процес, тоді як сума армів ≈ 2 750 с. Бюджети не порушені (LOG.md:965 рахує чесно ~55 хв), але сам артефакт рану внутрішньо неконсистентний.
5. **Строгий сигнал — специфічний для reflection, а не для «пам'яті».** C (memory+self-model) має strict RM 0.0, як і A/B; strict з'являється лише на D (0.5) і E (0.333). Заголовне протиставлення «E vs A (memory harm)» маскує те, що єдине реальне джерело повторів — reflection-саммарі (D−C CI [0.14, 0.86] — єдиний інтервал у всьому рані, що виключає 0). Звіт це каже у §3.4, але brief має вести саме цим, бо воно визначає CONT-005.

## 5. Рекомендації по morning list

1. **Accept M7** — прийняти як «no confirmatory difference established» із приміткою про флор строгої метрики та кластерну потужність; виконання чесне, дані первинні, re-run нічого не додасть на цій суїті. **Впевненість: висока.**
2. **CONT-002** — механіка доведена (5/5), формат стабільний; запускати behavioral-програму можна, але після переробки елісітації probe-ів (інакше знову все у флорі). **Середня.**
3. **CONT-005 як наступна арка — так.** Це найкраще обґрунтоване продовження: B>C/D/E, cu-0003-інтерференція, reflection-парротинг — усе вказує на «менше довіри до власних артефактів пам'яті». Передумова: редизайн суїти (п.4.2 вище). **Висока** щодо напрямку, **середня** щодо негайного старту.
4. **CN-005 GPU-тулінг** — budgeting-only, нічого в арці не зіпсував; рішення дешеве, не пріоритет. **Висока.**
5. **Публікації/зовнішні дії — ні.** Конфірматорного результату немає; єдиний CI, що виключає 0 — secondary. Публікувати нічого, крім, можливо, методологічної нотатки про протокол. **Висока.**
6. **Scope-зміни:** додати до протоколу (а) freeze analysis-коду, (б) label-form елісітацію probe-ів, (в) кластерний power-розрахунок, (г) незалежний (не-виконавцем) пост-хок прогін contamination-gate. **Середня.**

## 6. Формат для власника

Пропозиція GLM-5.3-Flash (≤80 рядків, «рішення нагорі») — правильна; приймаю скелет. Що б я покращив: (1) VERDICT має бути двома рядками, а не одним — другий рядок зобов'язаний нести caveat («строга метрика у флорі; тест на 7 кластерах малопотужний»), інакше «no difference» читається як «пам'ять не шкодить/не допомагає», чого дані не кажуть; (2) блок НЕГАТИВИ повинен явно містити «2 крахи, 3 git-реви виконання, +257 рядків, пом'якшений власний gate» — без вигладжування; (3) ЧИСЛА — не більше 6, і серед них обов'язково B 0.557 > C/D/E 0.429 та D−C [0.14, 0.86] (єдиний ненульовий інтервал); (4) до кожного з 6 рішень — дефолтна рекомендація одним словом, щоб із телефона можна було відповісти «ok to all / ok крім №N». Скелет:

```
VERDICT (2 рядки: формальний результат + головний caveat)
ВАМ НА РІШЕННЯ (6 пунктів × 1 рядок + дефолт: accept/так/так/відкласти/ні/так-з-умовами)
ЩО СТАЛОСЬ (4-5 рядків: арка, ран, крахи чесно)
ЧИСЛА (≤6 рядків)
НЕГАТИВИ Й ВІДХИЛЕННЯ ВІД ПРОТОКОЛУ (gate, 2 крахи, невиконана note-1-заява)
ЩО НЕ ДОВЕДЕНО / ЩО ЦЕ НЕ ОЗНАЧАЄ (разом, 3 рядки)
ЛІНКИ (file:line)
```

**Підсумкова позиція ревʼюера:** виконання приймати можна — дисципліна реальна, негативи задокументовані, дані відтворювані. Але інтерпретаційна рамка звіту («memory-arm harm, не сертифікований») слабша за дані: фактичний сигнал — (а) все у флорі на free-form probes, (б) повтори породжує саме reflection, (в) простіша пам'ять B обіграє повний стек. Саме ці три речі мають визначати наступну арку.

---

## Appendix — curation by the implementing agent (2026-10-04)

Per house practice (verify, don't trust labels), every load-bearing Fable claim was reproduced from the repository before relay:

1. **Contamination-gate softening in c679547** — diff inspected: `if len(run_revs) > 1` → tolerated when `resume-manifest.json` exists (`git show c679547 -- .../analyze_confirmatory.py`).
2. **+257 lines, not a "one-line fix"** — `git show --stat c679547`: 257 insertions across 3 files.
3. **B 0.557 > C/D/E 0.429; contradiction_update B 1.0 vs C/D/E 0.5** — cross-arm-table.json per-arm/family extraction.
4. **correction_reuse = 0.0 in every arm** — same extraction.
5. **Two crashes, not one** — LOG.md same-day lesson: "attempt 2's aggregate then crashed on wall_s=None … the second crash was the first crash's shadow"; resume-manifest shows D(202–505) on rev c679547, E on 4e425ea.
6. **Run-record aggregates internally inconsistent** — cross-arm-table.json: arm D `wall_s_by_seed` lacks seed 101, `arm_wall_s` 464 s; Σ arm_wall_s ≈ 2752.6 s vs `total_gpu_wall_s` 602.2 s (final process only).
7. **PR-REVIEW note 1 (fixture-authoring exposure) statement absent from results-summary.md** — grep found no author/exposure/residual declaration.
8. **Eligibility endogenous to arm (self-model induces the initial error)** — repeated-mistake-analysis.json rows: rt-0005 and rt-0008 initial answers A/B "billing" (correct, 0 eligible seeds) vs C/D/E "bug" (wrong, 5 eligible seeds each).
9. **Cluster-power bound (CI could exclude 0 only with repeats in ≥3/7 clusters)** — verified by derivation: with A pinned at 0, P(all-zero resample) = (5/7)^7 ≈ 9.5% > 2.5% with 2 nonzero clusters; (4/7)^7 ≈ 0.2% < 2.5% with 3.
