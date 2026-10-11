# REVIEW (verify-pass) — PREREG-CONT006-PLT draft

Provenance: reviewer = Opus via Claude Code CLI (`claude --model opus -p`,
stdin prompt, repo root, 2026-10-11 later same day); second round — the
same reviewer that produced R-1..R-19 on the design (verify-pass of its
own requested folds). Fable probed again the same day: limit-blocked
("Fable 5 limit"); queue Fable → Opus → Astra → Flash. Prompt:
verify-pass questions 1-5. Raw output verbatim below; curation appendix
follows.

---

# Вердикт: **GO-with-changes** — фолд R-1..R-19 сутнісно виконано (14 OK / 5 PARTIAL / 0 MISSED), але позер-артефакт рахує НЕ те правило, яке пререг оголошує рішенням, і в пререзі 4 аналізо-блокуючі діри. Усі фікси — доc-level, ≤1 сесія, без GPU. Заморожувати в цьому вигляді не можна: фріз закриє саме ті параметри, що недопинені.

Застереження про метод: п.2 я перевіряв аналітично з власних чисел артефакту (median CI width → SE ≈ 0.194/3.92 ≈ 0.0495), бо запуск симуляції в цій сесії був заблокований дозволом. Числа нижче — аналітичні наближення, не симуляція; вони вимагають підтвердження рядком у самому артефакті (це і є фікс V-1).

---

## 1. Verify-pass R-1..R-19

| R | статус | де / що бракує |
|---|---|---|
| R-1 одиниця бутстрапу + power до фрізу + sensitivity + scope | **FOLDED-OK** | design §6 (25 кластерів), prereg §2–3, артефакт існує до фрізу; (a)(b)(c)(d) усі є |
| R-2 trigger-предикат / task-success / no-op rule / paralysis | **FOLDED-PARTIAL** | (a)(b)(d) є; **(c) правило для degenerate no-op епізодів досі немає** — див. V-3 |
| R-3 семантика сідів + пілот-гейт на n | **FOLDED-PARTIAL** | механізм оголошено, але `temperature > 0` **без числа** і «варіація ≈ 0» не операційна — V-5 |
| R-4 baseline-band gate повного рану | **FOLDED-PARTIAL** | гейт + declared-out є (prereg §6.3), але **немає мінімального K, при якому primary ще стоїть** — V-6 |
| R-5 бюджет + GPU-години + staging арм | **FOLDED-PARTIAL** | per-episode бюджет, wall-guard, resumability, staging — OK; **total GPU-hours estimate відсутній** (design §8 його вимагає) |
| R-6 consumption gate переопределено | **FOLDED-OK** | prereg §5, усі три частини + permitted-лексика |
| R-7 explicitness standard історій | **FOLDED-OK** | prereg §4 A1 (lint + spot-check), limitation у design §4 |
| R-8 lesson-quality рубрика | **FOLDED-PARTIAL** | рубрика є, blind оголошено; **хто оцінювач і КОЛИ — не зафіксовано** — V-7 |
| R-9 blind gold механізовано | **FOLDED-OK** | prereg §4 A3 — порядок коміту + digest manifest як доказ |
| R-10 приймальні числа чекерів | **FOLDED-OK** | ≥20 трейсів, 2 лейблери, 100%/≥0.95+EA, held-out, дигест |
| R-11 пілот: роздільність + доля даних | **FOLDED-PARTIAL** | 3×5, excluded from primary — OK; **«≥2/5 flips» після зміни геометрії втратило одиницю**, 2 пілотні класи не названі — V-8 |
| R-12 mid-run invalidation | **FOLDED-OK** | prereg §4 A5 + §6, >10%→halt, no silent re-run |
| R-13 Q35 у пілоті + scoping нуля | **FOLDED-PARTIAL** | Q35-плече є, scoping у §8 є; **але вирішальне правило вилучено** — V-4 |
| R-14 FC-6 out / FC-5 точна рівність | **FOLDED-OK** | design §3 |
| R-15 один confirmatory | **FOLDED-OK** | prereg §2, design §6 («no multiplicity correction needed») |
| R-16 повна localization matrix | **FOLDED-OK** | design §6 — усі 7 клітинок, включно з M+L<max і L>GOLD investigate |
| R-17 instance-vs-instance disjointness | **FOLDED-OK** | prereg §4 A4, автоматична матриця |
| R-18 «cheap repair» числом | **FOLDED-OK** | prereg §4 F: ≤1 сесія / no new module / no freeze-surface change |
| R-19 binding close-out артефакти | **FOLDED-OK** | prereg §6.6, 4 файли |

Окремо: нумерованих R немає, але §C.1/C.3 рев'ю (harness self-test на синтетичних трейсах + **stub-консумер dry-run усього ланцюга**) і §7.7 design (6-gram experience↔transfer) **в дизайні є, а в пререзі відсутні**. Пререг — виконуваний документ; те, чого в ньому немає, не виконається. Див. V-9.

---

## 2. Чесність позер-калькуляції

**Клас-структура: модель чесна.** `delta_class ~ N(d_true, sig_dclass)` — ефект-гетерогенність, що **не** скасовується при паруванні, тоді як `kappa` і `eps` входять у `base`, спільний для обох плечей, і скасовуються. Це структурно правильне відображення «інстанси класу ділять латентне правило». Honesty-рядки на місці: P10/P11 (sig_dclass 0 → .15 дає 0.828 → 0.679), P12/P13 (LOO), P14/P15 (two-level), P16 (відкинута rev-1 геометрія), P17 (seed cut). Відкинуті геометрії збережені в артефакті — це добра практика і вона тут дотримана. Дві прогалини в моделі: **немає instance-level ефект-гетерогенності** (`sig_dinst` ≡ 0 — реальна між-кластерна дисперсія d_c занижена), і рядок, названий «conservative», не є найконсервативнішим із доступних (для d=.20 немає відповідника P11 із sig_dclass .15).

**Compound-правило: FP контролює, але power у пререзі оголошено від іншого правила — це головна знахідка (V-1).** `detect_benefit` у коді = `hi < 0`, тобто **лише CI**. Пререг §3 видає 0.921 як «benefit power» для оголошеного рішення, яке насправді є compound (CI<0 **І** |d|≥0.20). При SE≈0.0495 і d_true=0.20 точкова оцінка перевищує порог 0.20 приблизно в половині реалізацій → power compound-правила на самому MME ≈ **0.5**, не 0.921. FP, навпаки, правило тримає з запасом: при d=0 потрібно d̂ ≤ −0.20, тобто ~4 SE → FP ≈ 10⁻⁴–10⁻⁵, значно нижче 0.073. Але це дві сторони однієї монети: правило конservative настільько, що купує FP за power, і ні того, ні того в артефакті не обчислено.

**MME 0.20 не обґрунтований для оголошеного рішення.** `mme_rule` явно виводить MME на CI-only рядку — тобто на найслабшому з трьох критеріїв, тоді як рішення = перетин трьох (compound ∧ LOO ∧ two-level). Верхня межа «established»-power уже видна з артефакту: 0.773 (P15) — нижче 0.80 — і це *до* накладання точкового порогу. Плюс LOO приблизовано **одним** свіжим раном при K=20 (0.858), а правило вимагає виживання при **всіх 5** викиданнях класу — кон'юнкція строго слабша за одиничний drop, і її не обчислено. Чесна цифра MME для power 0.80 на кон'юнкції, за аналітикою, ~0.25–0.30, не 0.20.

**Downgrade-правило оголошено правильно і на правильному місці** (design §6, prereg §2, `mme_rule` в артефакті — три узгоджені копії): LOO **і** two-level обов'язкові, невиживання → directional, class-level генералізація не виводиться, scope = 5 протестованих класів. Формулювання коректне; проблема лише в тому, що MME не калібрований під цю ж кон'юнкцію.

Дрібніше: BOOT у артефакті 4000, пререг §2 оголошує 10k; RNG аналізу «frozen» без числа; b0-sensitivity покриває .45/.75, але не краї гейт-банду .3/.9, де clipping стискає спостережуваний ефект.

---

## 3. Пререг-повнота для замороженого виконання

**Є:** фази авторингу A1–A5 з **обов'язковим порядком фрізу** (GOLD-L у A3 до існування transfer-інстансів у A4 — це коректна механізація R-9, і саме той порядок, якого вимагало рев'ю); гейти (пілот-скринінг, per-class band, checker-acceptance, per-episode invariants, >10% invalid, live telemetry, analyzer fail-closed); per-episode бюджет (80 turns / 250k / 1800 s) + per-cell wall 4 h + resumability; гілки зупинки (<3 класів у банді, пілот-повтор максимум один і лише за діагностованого багу, difficulty change = freeze); мechanічний критерій stage-2; close-out список із 4 артефактів; non-goals; single EXEC FREEZE із переліком того, що дигестується.

**Пропущено (усе — у пререг, до фрізу):**
1. Total GPU-hours estimate (design §8 вимагає явно).
2. Stub-консумер dry-run + per-class синтетичні трейси з відомою відповіддю (design §7.3) — у пререзі лише «analyzer self-test».
3. 6-gram гейт experience↔transfer (design §7.7).
4. Правило для кластерів із недостатньою кількістю **trigger-eligible** епізодів (включно з 0 — тоді d_c не визначений і одиниця бутстрапу зникає).
5. Мінімальне K, при якому primary ще стоїть після declared-out класів.
6. Естиматор primary назвати явно: незважене середнє 25 кластерних d_c (саме це рахує калькулятор), а не pooled episode rate — це різні числа при нерівній eligibility.
7. Рівень парування: кластер (одна й та сама (class,instance) в усіх плечах), сіди **не** паруються між плечима — модель це припускає, пререг не каже.
8. Температура консумера (число), RNG аналізу (число), BOOT (узгодити 4000/10k).
9. Скільки experience-історій на клас і що є одиницею уроку (див. V-10).
10. Які 2 класи йдуть у пілот.

---

## 4. Нові ризики операционалізації

**V-1 — CRITICAL. Power оголошено від CI-only, рішення — compound; MME 0.20 не витримує власного правила.** Фікс: додати в `power_calc_plt.py` рядок кон'юнкції — `CI<0 ∧ |d̂|≥MME ∧ (усі 5 LOO-drops: CI<0) ∧ two-level CI<0`, обчислений усередині одного репа (не окремими ранами), для d ∈ {.20,.25,.30,.35}; MME = найменший 0.05-крок, де **ця** кон'юнкція ≥0.80; у пререзі §3 перейменувати 0.921 на «CI-only» і поставити поруч compound-число. Якщо MME зсувається до 0.30 — це чесна межа дизайну, і її треба записати, а не обійти.

**V-2 — CRITICAL. Non-inferiority margin −0.10 ≈ пів-ширина CI → гейт-монетка.** При SE≈0.0495 нижня межа при істинній нулевій різниці ≈ −0.097, тобто умова «lower bound > −0.10» проходить ~50% часу. Справжня користь L може бути заблокована випадковістю NI-гейта, і це не буде видно як дефект. Фікс (на вибір, оголосити зараз): margin −0.15 з power-рядком, АБО NI понизити до mandatory-reported descriptive (не блокуючий), АБО блокувати лише при CI повністю нижче −0.10 (тобто доведена шкода task-success замість недоведеної не-шкоди). Третій варіант методологічно найчистіший.

**V-3 — HIGH. Fail-closed consumption gate не має продовження: що в плечі L, якщо урок класу відкинуто.** §5 каже «rejected lesson is never delivered» — і зупиняється. Тоді плече L для цього класу = плече A, L−A механічно розводиться до 0, а це *справжній* результат (провал екстракції), який мусить бути задекларований, а не розмазаний. Фікс: оголосити — відкинутий/невиданий урок = «no lesson delivered», епізоди залишаються в primary (консервативно), **плюс** обов'язкова per-class delivery-status таблиця в close-out і запис у localization matrix (delivery failure ≠ abstraction failure). Сюди ж R-2(c): degenerate no-op епізод — invalid чи trigger-absent? Зараз обидві рамки застосовні до того самого епізоду.

**V-4 — HIGH. Q35-пілот втратив вирішальне значення — повертається рівно та двозначність, проти якої був R-13.** Дизайн: «consumer selection before the main spend». Пререг §1: «consumer selection info for experiment-2 framing; NEVER a mid-run switch». Різниця не косметична: якщо GOLD-L мертвий на G8B і живий на Q35, пререг у чинному вигляді наказує все одно витратити 700 епізодів на G8B і отримати консумер-двозначний нуль. Фікс: оголосити гілку до фрізу — «GOLD-L мертвий на G8B І живий на Q35 (той самий скринінг-критерій) → STOP перед повним раном + owner gate; результат = consumer-capacity localization, cap витрачено на 90 епізодів, не на 700». Це не mid-run switch — це pre-run стоп.

**V-5 — MAJOR. Температура консумера не зафіксована числом.** Весь аргумент R-3 (справжній n = 105, а не 25) тримається на temp>0, а freeze-поверхня містить «> 0». Фікс: пінити значення (і для worker-пасу теж), і зробити «варіація ≈ 0» операційною: напр. «якщо у >70% пілотних cluster-arm усі 5 сідів дають ідентичний recurrence-результат → перерахунок на рівні кластерів».

**V-6 — MAJOR. Немає мінімального K для повного рану.** Пілот має «<3 класів → STOP», повноран-гейт §6.3 — ні. При 2 declared-out класах K=15, тобто рівно геометрія, яку рев'ю R-1 відкинуло і яку артефакт тримає в родині `rejected` (P16, 0.799). Фікс: «≥4 класи в банді, інакше primary → directional; ≤3 → STOP», з посиланням на P16/P13.

**V-7 — MAJOR. Blind-рубрика без суб'єкта і без часу.** Фікс (безкоштовний): рубрикова оцінка виконується **між фрізом L-store і першим consumer-епізодом** — тоді blind-to-outcome не декларація, а властивість порядку; оцінювач = non-executor agent з adjudication, зафіксувати як у R-10.

**V-8 — MAJOR. Пілот-критерій «≥2/5 flips» втратив одиницю після переходу на 3 інстанси.** 2 з 5 сідів усередині інстансу? 2 з 15 епізодів класу? Різниця змінює суворість гейта кратно. Фікс: записати знаменник явно + назвати 2 пілотні класи зараз (інакше вибір класу стає пост-хок ступенем свободи).

**V-9 — MAJOR. Dry-run / self-test / 6-gram є в дизайні, але не в пререзі.** Фікс: внести в §4 як A5-bis і додати їх дигести в перелік EXEC FREEZE (§4 F). Історично арку вбивали саме ці речі (CN-012, positional delivery).

**V-10 — MAJOR. Внутрішня суперечність щодо кількості історій.** §4 A1 в одному рядку: «**5** experience histories» і «spot-check **≥5 histories/class**» — перше дає 1 історію на клас, друге вимагає ≥25. Від цього залежить одиниця уроку (урок з однієї історії vs агрегований по класу) і сенс «multi-trace support» у валідаторі (§5), який при 1 історії на клас нездійсненний. Фікс: пінити N історій/клас (≥3, щоб multi-trace support мав зміст), узгодити §6.2 і §5.

**V-11 — MINOR. Критерій stage-2 перерахований нечітко.** «compound-rule benefit in ≥1 arm, or CI entirely off zero» — «≥1 arm» не перелічено, а «CI off zero» у шкідливому напрямку теж тригерить. Фікс: «iff (L−A) або (GOLD-L−A) має CI95 повністю поза 0 у будь-якому напрямку; NEUTRAL-L−A не тригерить» — інакше зафіксований у цій арці presence effect на NEUTRAL відкриє stage 2 без живого lesson-каналу.

**V-12 — MINOR. Артефактні дрібниці:** `sig_dinst` відсутній; немає d=.20 при sig_dclass .15; немає рядків на краях банду (.30/.90); BOOT 4000 vs «10k» у пререзі; RNG аналізу без числа; P12/P13 позначені `family: "primary"`, хоч це sensitivity-рядки (зчитається як power основного дизайну).

Що **не** є проблемою, хоча могло б здатися: staging M/M+L формально вужчий за ROADMAP item 4 (A/M/L/M+L), але owner accept 2026-10-11 стосувався саме rev 2 зі staging-ом — відхилення авторизоване, окремого гейта не потрібно. CI-only FP 0.073 > 0.05 — це недопокриття percentile-бутстрапу при K=25, і воно **честно показане** в артефакті, а не приховане.

---

## Підсумок

1. Фолд виконано добросовісно: 3 блокери попереднього рев'ю (R-1 одиниця бутстрапу, R-2 валідність endpoint'а, R-3 сіди) закриті по суті; жодна знахідка не MISSED. Freeze-ordering GOLD-L і per-episode invariants — найсильніші частини пререгу.
2. Нова категорія ризику — не дизайн, а **розрив між оголошеним правилом рішення і тим, що порахував калькулятор** (V-1) та **гейти, калібровані на пів-ширину власного CI** (V-2). Обидва роблять «established»-висновок справою удачі при оголошеному MME.
3. Блокери до EXEC FREEZE: V-1, V-2, V-3, V-4. Решта (V-5..V-12) — обов'язкові до фрізу, але не вимагають перерахунку рішення; усі вони про те, що фріз закриє недопинений параметр.
4. Найдешевше підсилення: кон'юнкційний power-рядок (одна функція в наявному скрипті), рубрика між фрізом L-store і першим епізодом (нуль коштів), pre-run Q35-стоп-гілка (90 епізодів замість 700 у найгіршому сценарії).
5. Після фіксів V-1..V-4 і допину §3 — на мій погляд це GO без дальшого рев'ю-кола: решта змін механічні й не торкаються дизайну.


---

## Curation appendix (implementing agent, 2026-10-11)

1. V-1 analytic claims — CONFIRMED numerically: median CI width 0.194
   → SE ≈ 0.0495; the reviewer's "compound power ≈ 0.5 at the MME"
   reproduces exactly in the regenerated artifact (C1 row, claim m=.20,
   d_true .20 → conjunctive 0.472); its predicted honest MME "~0.25-0.30"
   → measured **0.30** (0.899 power; 0.733 at .25). The artifact was
   regenerated (v3) with the conjunctive rule computed inside one
   replication, claim threshold decoupled from the true-effect ladder
   (the first coupling attempt produced a structural ~0.5 ceiling —
   exactly the median-event the reviewer described).
2. V-2 NI coin-flip — CONFIRMED analytically (LB ≈ −0.097 vs margin
   −0.10); folded as the reviewer's cleanest option (block only on
   PROVEN harm; margin reported descriptively).
3. V-10 contradiction — CONFIRMED: prereg rev 1 §4 A1 said "5
   experience histories" and "spot-check ≥5 histories/class" in one
   line; fixed to ≥3 per class (15+), multi-trace support meaningful.
4. P12/P13 mislabeled family "primary" — CONFIRMED in v2 artifact;
   relabeled "sensitivity" in v3.
5. LOO conjunction strictly weaker than a single drop — logically
   sound; the v3 conjunctive rule computes all five drops inside each
   replication (not the single-drop approximation).
6. All 12 V-findings folded into PREREG-CONT006-PLT.md rev 2 (this
   commit); the 10 completeness items folded into §2/§3/§4/§6
   (estimator + pairing, temperatures 0.3/0.2, BOOT/RNG numbers,
   trigger-min rule, min-K gate, pilot classes FC-1/FC-3 + flips
   denominator, GPU-hours estimate, A5-bis dry-run + known-answer
   traces + 6-gram gate, ≥3 histories/class, stage-2 criterion
   precision).

No refuted claims. The reviewer's "GO without another review round
after V-1..V-4 + §3 pinning" is accepted: both are done; the next
independent check is the non-executor gate on the FROZEN artifacts
(prereg §4 G) before any GPU.
