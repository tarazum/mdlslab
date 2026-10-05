# REVIEW-FABLE-RESULTS — independent post-result audit (CONT-005 confirmatory)

- **Reviewer:** model "Fable" via Claude Code CLI, fresh context, read-only (owner requested the second look: "може не все так однозначно")
- **Date:** 2026-10-05, after the owner brief (commit b170ffc), BEFORE owner acceptance
- **Audited:** the frozen verdict, per-cluster numbers, the two "new signals" of the brief, the analysis hotfix, and the wording
- **Implementing-agent curation:** headline claims re-verified against the traces (see appendix); all reproduced.

---

Аудит завершено. Все перерахував незалежно з трас (120 primary-проб, обидві гілки, 5 сідів), перевірив фікстури, хотфікс через git-історію та digest-и, і розкопав trap-механіку. Головні числа виконавця відтворюються точно, але два "нові сигнали" з brief-у потребують корекції.

## ТАБЛИЦЯ 1–7

| # | Статус | Висновок |
|---|--------|----------|
| 1. Перерахунок primary | **OK** | Мій незалежний підрахунок з trace.jsonl збігається з results-summary.json по всіх 12 кластерах × 2 гілки × 5 сідів: T0 помилки лише на cr-2001/02/04/05/06/08 (1.0), T2 те саме + cr-2007 0.2 + cu-2004 1.0; delta = −1.2/12 = **−0.100** точно; CI відтворюється аналітично (верхня межа 0.000 — бо 0 є максимумом розподілу deltas: 10 кластерів по 0, один −0.2, один −1.0; P(всі нулі в ресемплі) ≈ 0.11 > 2.5%). |
| 2. cu-2004 | **OK (систематика, не збій)** | T2 і T3 у **всіх 5 сідах** відповіли голе `"6"` (superseded trap); T0/T1 у всіх сідах — `"10"`. Це не рендер-глюк одного сіда: у сегменті cu-2004 T2-траси **немає жодного supersession/RESOLVED-маркера** (supersession не спрацював на числовому конфлікті), модель ще до проби (s3t1) казала "6 slots", а на s2t1 взагалі відповіла "I don't understand what you mean by 'Correction for the records'". Важливо: **A (без памʼяті) теж відповіла "6"** — trap збігається з дефолтним вибором моделі; T0/T1-рендер цей дефолт перебиває, T2/T3-рендер — ні. |
| 3. Strict trap repeats 5/60 | **ISSUE** | Усі 5/60 у T2 і в T3 — це **один кластер cu-2004 × 5 сідів**. А "0 в інших гілках" — частково **артефакт strict-порівняння** `observed_normalized == trap`: A відповіла trap як `"6"` у лапках (`"\"6\"" ≠ "6"` — не зараховано), T0 на label-рівні повторила trap на cr-2001 ("the request is for a **reference**.", trap=reference) і cr-2005 (observed_label "**media**", trap=media) — у реченнях, тому strict не ловить. Метрика зараховує лише лаконічні відповіді → конфаунд вербозності по гілках. "Anchoring-by-flagging" як "найчистіший сигнал" — перебільшення. |
| 4. Guess-band / position | **OK з оговоркою** | Caveat майже тривіальний: |−0.1| < 2×0.333 спрацьовує автоматично, але вердикт і так падає на CI, тож практичної ваги мало. Position-bias не пояснює cu-2004 (відповідь "6" семантична — модель і у free-text казала "6 slots"), але A-гілка показує, що "6" — дефолтний вибір і без памʼяті, що розмиває інтерпретацію "T2 згадав trap з памʼяті". |
| 5. Хотфікс | **OK** | `git diff a6a0529→859e6fc`: рівно 2 рядки у secondary-блоці `t1_t3_exploratory_overall` (flatten списків для fmean, до фіксу — крах TypeError, жодного виводу). Digest-и збігаються: frozen `9ac16cd5…` = запис у манифесті, поточний файл `db78d9ac…` = digest_after. Primary/bootstrap/verdict-код (рядки 135–170) не торкнуто. На primary вплинути не міг. |
| 6. Формулювання | **OK** | За замороженим §6 CI включає 0 → єдине дозволене формулювання саме "no confirmatory difference established". Дозволене (і чесне) **сильніше** доповнення: верхня межа CI = 0.000 < MME 0.25, тобто дані не просто "не підтвердили", а **виключають** пре-зареєстрований позитивний ефект ≥0.25; напрям реверсований. **НЕ можна** казати "T2 значимо гірший" (CI торкає 0, two-sided) і не можна промоутити trap-repeat як підтверджений ефект. |
| 7. Однозначність | **OK/ISSUE** | Див. нижче. |

## Що робить результат неоднозначним
- **Один кластер несе все**: без cu-2004 delta = −0.0167 (тільки cr-2007). З n=12 один кластер = 8% ваги, але 83% ефекту.
- **Сіди вироджені**: temp 0.0 + ідентичні промпти (опції НЕ ротуються між сідами — перевірено: текст проби cu-2004 байт-у-байт однаковий у всіх 25 arm-seeds) → відповіді ідентичні по сідах скрізь, крім одного відхилення (cr-2007 T2 seed-1001). Ефективне n ≈ 12 бінарних спостережень, а не 60; power-розрахунок "5 obs/cluster" був оптимістичним. (Протокол §14 цей determinism-caveat чесно декларує.)
- **CR-кластери без дискримінації**: 6/8 на error 1.0 в ОБОХ гілках (підлога) — primary фактично вирішували 2 кластери.
- Частина T2-помилок — **формат, не памʼять**: T2/T3-рендер лікає маркап `[s1t2|environment|source:…]`/`[RESOLVED:…]` у відповіді → invalid_format (cr-2007 seed-1001: модель по суті сказала "reference", але луною відтворила рендер).
- Одна модель (granite-code:8b), синтетичний контент.

## Що результат встановлює твердо
- Пілотний ефект (+0.36) **не реплікувався** — напрям реверсований; ефект ≥ MME виключений верхньою межею CI.
- Памʼять як така працює: A→T0 на CU 0.0→1.0 (3/4 кластери), delayed_recall 0→0.67; A на рівні вгадування (0.208).
- T2/T3 на cu-2004 систематично (5/5 сідів, обидві гілки) програють T0/T1 — це реальний, відтворений факт про trust-рендерер, незалежно від інтерпретації.

## ВЕРДИКТ: **МІЦНИЙ З ОГОВОРКАМИ**
Primary-вердикт "no confirmatory difference established" повністю відтворюється з сирих трас і за замороженим правилом є єдино коректним; він навіть сильніший, ніж звучить (позитивний ефект ≥0.25 виключений). Оговорки: (а) заявлений у brief "найчистіший новий сигнал" (trap-repeats T2/T3 5/60 **vs 0 в усіх інших**) — частково артефакт strict-нормалізації і вербозності, всі 5 — один кластер; (б) 5 сідів при temp 0.0 — фактично один прогін.

## Що сказати власнику
"Вердикт міцний і перерахований незалежно з трас: ефекту немає, пілот не реплікувався, і дані виключають заявлений MME-ефект (верхня межа CI = 0). Але 'найчистіший новий сигнал' у brief слід понизити: всі trap-repeats — один кластер cu-2004, а 'нуль в інших гілках' — артефакт strict-порівняння (A відповідала той самий trap '6', лише в лапках; T0 повторювала trap-слова у реченнях на cr-2001/cr-2005). Реальний і цікавий факт вужчий: на cu-2004 trust-рендерер T2/T3 систематично програв плоскому T0/T1, причому supersession на числовому конфлікті не спрацював, а рендер-маркап T2 лікає у відповіді й псує формат."

## Рекомендації по рішеннях 1–3
1. **Accept** конфірматорний результат — так, верифіковано незалежно.
2. **Accept хотфікс** — так: diff мінімальний, лише secondary, digest-и збігаються, primary недоторканий.
3. **Next step — змінити формулювання**: перед новою inference-кампанією "anchoring-by-flagging" зробити **безкоштовний ре-аналіз** наявних трас з label-рівневим trap-repeat (observed_label == trap) по всіх гілках — він, за моїми вибірками, суттєво змінює картину (T0/A теж повторюють trap). Паралельно: полагодити лік рендер-маркапу у відповіді T2/T3 (джерело invalid_format) і неспрацьований supersession на числових конфліктах; у наступному дизайні варіювати контент/позиції між сідами, бо при temp 0.0 сіди не дають реплікації.

---

## Appendix — curation + the free label-level re-analysis (implementing agent, 2026-10-05)

Verified against traces: (1) all 5 strict T2/T3 trap-repeats originate from
cu-2004 x 5 seeds; (2) arm A answered the same trap on cu-2004 as a quoted
'"6"' (label-extraction reads it as 6; strict normalization did not);
(3) T0 repeated trap words inside sentences on cr-2001/cr-2005.

Label-level trap repeats (observed_label == trap; all 18 trap-bearing
scenarios x 5 seeds, n=90/arm; zero GPU, existing traces):

| Arm | repeats | clusters |
| --- | --- | --- |
| A | 25/90 | cu-2004, rt-2002, rt-2005, cr-2001, cr-2002 |
| T0 | 15/90 | rt-2001, rt-2005, cr-2001 |
| T1 | **0/90** | - |
| T2 | 10/90 | cu-2004, cr-2001 |
| T3 | 10/90 | cu-2004, cr-2001 |

Reading (exploratory): the strict metric's "T2/T3 only" pattern was a
verbosity artifact; at label level every arm repeats traps and **T1 (source
annotations only) is the only arm with zero repeats** - consistent with T1's
top overall score. T2/T3's residual cu-2004 failure is real and reproduced
(the trust renderer does not override the model's default answer on the
numeric conflict, where supersession has no typed sources to act on).
