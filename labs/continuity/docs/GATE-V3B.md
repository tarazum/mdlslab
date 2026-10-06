# GATE-V3B — non-executor gate verdict (FREEZE-B, перед confirmatory v3j)

> Процедурна замітка: гейт виконано на **Opus** (claude --model opus -p, fresh
> context, read-only) — **Fable limit-blocked** на момент гейту (перевірено
> двічі: "You've reached your Fable 5 limit"). Заміна задекларована в LOG.md;
> власник може перев'язати гейт на Fable. Куративна перевірка тверджень гейту
> виконана executor-ом (додаток внизу).

# GATE-V3B — non-executor gate, FREEZE-B (CONT-005 cycle-2)

> Процедурна примітка: гейт виконано на **Opus** (Fable limit-blocked, перевірено двічі; заміна задекларована в LOG.md). Власник може перезапустити на Fable.
> Жодного GPU/інференс-виклику не зроблено. Жодного файлу не змінено (`git status` порожній).

---

## 1. COMPLETENESS §10 FREEZE-B — ⚠️ PASS з двома зафіксованими пропусками (не блокуючі)

| §10 FREEZE-B вимога | Статус | Доказ |
|---|---|---|
| analysis script FIRST, дайджест у маніфесті | ✅ | `analyze_confirmatory_v3.py` = `dc288763…` (frozen-config-v3b.json:53); LOG.md «1) analysis script FIRST»; коміт 10f2a8d додає його разом із фікстурами |
| `fixtures/v3j` suite + 5 per-seed rendered дайджестів | ✅ | ключі `fixtures/v3j_suite` + `…_rendered_seed3001..3005` (рядки 68–73) |
| predeclared seeds {3001..3005} | ✅ | manifest `seeds_predeclared` (8–14); `fixtures/v3j/manifest.json:17-23`; `run_confirmatory_v3.py:64`; `analyze_confirmatory_v3.py:62` |
| новий run script | ✅ | `run_confirmatory_v3.py` = `ea8a292a…` (рядок 54) |
| refreshed дайджести **кожного** шляху з FREEZE-A | ⚠️ | 11 з 13 спільних шляхів присутні; **відсутні 2**: `experiments/suite-v3/analyze_pilot_v3.py` і `experiments/suite-v3/run_pilot_v3.py` (вони явно названі в §10 FREEZE-A) |

Пропуск нешкідливий і перевірений: обидва пілотні скрипти **байт-ідентичні** FREEZE-A, тож «refresh» нічого б не змінив:
```
a044e220002fe84c21733f7fae8f08b0a2d0e7a7bc359fa9ae830046f58c60b1  analyze_pilot_v3.py   (== v3a:34)
05594724804880b6a9557cb2ffda60de1ab05b9f2e2462770d3abca12ebc4f34  run_pilot_v3.py       (== v3a:35)
```
Також `fixtures/v3i_*` дайджести не перенесені у v3b — коректно, вони лишаються історичним записом у frozen-config-v3a.json (stage-1 артефакт).

Додатково присутні понад мінімум §10: `PREREG-REQUIREMENTS-V2.md`, `PR-REVIEW-v3.md`, `memory.py`, `fixture-validation-v3j.json` + 5 `assembly-gate-v3j-seed300*.json` — тобто gate-артефакти заморожені разом із контентом. Разом 25 ключів.

Нюанс конвенції: `frozen_at_git_rev_before_any_v3j_inference = 10fb461`, тоді як заморожений контент фізично існує з **10f2a8d**. Це та сама конвенція, що у FREEZE-A (`2d92621` = батько коміту маніфесту `7b8cb00`) — не порушення, але executor має записати в заголовок прогону реальний rev виконання (`10f2a8d` або нащадок).

---

## 2. DIGEST RE-HASH — ✅ 19/19 файлових шляхів; ❌ 6 контент-похідних заблоковано sandbox

Незалежний перерахунок усіх 19 файлових шляхів (`sha256sum`, окрема від маніфеста ітерація):

```
8276286b087262ec61ea03e90b90eadad42aaa36f3c8dfe4556c4031b0f21c27  docs/EVALUATION-PREP-v3.md
442d438526b7985704d97bf2fda9a6a14ee5b6119f2a3e10c771c98aa83535d0  docs/SUITE-V3-DESIGN.md
b843888eab0934583270a5b0b7b12cab697fba779c0314a1a5ee4af5605ef2cc  docs/PREREG-REQUIREMENTS-V2.md
6c48b21880db48ffd5210fac1e8543b1ab12c104547d217f2de797d2e14ffc89  docs/PR-REVIEW-v3.md
dc288763e9d8a54e57212f14c2522344265eb02a79c57b1ae39f074d24939314  analyze_confirmatory_v3.py
ea8a292a786064bfd88371383c934a5e0723f38fd805689f12ab4e95c994868f  run_confirmatory_v3.py
cadb45527689a0dfb59570489dcfebee67d8339680a02d8d49cfcd415f63102d  validate_fixtures_v3.py
01061a3cbf51cef257e9d3811aa514075cfab80a2546258993ff859da01ae6ab  assembly_gate.py
9c2758bcb453a4965af3ffea02df4da91d9f5e5255438cf22c9d17d203bfaba8  src/continuity/claims.py
1dcd5625c5b2ff319858e44bf6dcd90af6e34c90956dd2f50b761b18b0abb079  src/continuity/runner.py
856b934868c6113ae919e5fb93673a0819614e1dde2a301ae571153c726a715e  src/continuity/provider.py
4270a0916ab227c89b46c5cbe03525fa364831bf0353f91ee6c4fcef2b3f9f7d  src/continuity/fixtures.py
1ef4291641fd6be73d888e65452c778687e156393cd54df597bcbc72202a394b  src/continuity/memory.py
37f4a35a60374e3255ef61413089740868ff68b4badb5fc72e7d54340516d1ab  fixture-validation-v3j.json
3b05ff35384a334de12ba8a02390ca2e84105d4db2766bd2d2c5c5ef1463d547  assembly-gate-v3j-seed3001.json
26fe652dbe242253d58f130f90bd7be669c34fedb7f7cb824c2d4441717278d6  …seed3002.json
1595d3cefa0e3ebb54d17239ab483274f0134a37ed27052d827cce50dd9f9294  …seed3003.json
40ed5f9ce1254607f044c664eab455a5042044e8d74fe9e247d486807d357529  …seed3004.json
c31cad56698e01b306fad5244be061fd3005a160a9c20070af29976f330aa522  …seed3005.json
```
**Усі 19 збігаються з frozen-config-v3b.json рядок-у-рядок. Жодного mismatch.**

`fixtures/v3j_suite` + 5 `_rendered_seed300x` — **перерахувати не вдалося**: пісочниця цієї сесії блокує довільне виконання Python (`python -`, `python -c`, heredoc) і конкатенацію через shell-цикл (`Contains simple_expansion`). Це точно прецедент GATE-V3A п.6 → умова побайтового звірування для executor-а (див. §8.A).

Непряме підтвердження, яке я все ж маю: `fixture-validation-v3j.json` містить `"suite_sha256": "516d6588c1c377e891ef87293d937d22e2fdd71dbd318aeaf88367365e7d0889"`, згенерований `validate_fixtures_v3.py:suite_digest()` — тим самим рецептом (relpath + bytes, rglob sorted), що й `run_confirmatory_v3.py:suite_digest()` — і він **збігається** з маніфестом. Сам цей артефакт має підтверджений мною дайджест `37f4a35a…`. Це не незалежний перерахунок, але замикає ланцюг на двох різних кодових шляхах.

---

## 3. ANALYSIS SCRIPT — ✅ реалізує заморожені §3–§9 + §12

| Вимога | Статус | Доказ |
|---|---|---|
| primary = label-form error rate на 12 CR+CU | ✅ | `PRIMARY_FAMILIES = {"correction_reuse","contradiction_update"}` (66); fail-closed якщо `len(primary_ids) != 12` → exit 2 (177–180); помилка = `0.0 if passed else 1.0` (208) |
| контраст T0−T1, двобічний | ✅ | `cluster_delta.append(rates["T0"] - rates["T1"])` (221); вердикт за `lo > 0 or hi < 0` (232) — двобічний, обидва напрямки закодовані |
| MME 0.25 | ✅ | `MME = 0.25` (67), ужито у 233/235 |
| cluster percentile bootstrap 10000, RNG 20261006 | ✅ | `BOOT = 10_000`, `RNG_SEED = 20261006` (68–69); `bootstrap_ci` ресемплить **кластерні дельти** (151–158) — тобто cluster-level percentile |
| чотириваріантний вердикт §6 **дослівно** | ✅ | рядки 78–86 збігаються символ-у-символ із §6 (включно з реверсним формулюванням і «directional difference below the minimum meaningful effect; not established as meaningful») |
| completeness guard 12×5 в ОБИДВОХ primary-армах, без підстановок | ✅ | `primary_missing` → `VERDICT_INCOMPLETE` + note «no substitution, no seed re-draws» (227–231); структурний guard «рівно 1 проба на (arm, seed, cluster)», інакше exit 2 (196–211); secondary-неповнота лише репортується (193, 316, 360) |
| guess-band §12 | ✅ | `max_position_share` (343), `band = |share − 1/6|` (348, `GUESS_K=6`), `caveat_fires` при `delta < 2*max_band` (351); MME ніде не змінюється — `"mme": MME` константа (458) |
| echo-scan ([RESOLVED == 0 + NOTE: rate) | ✅ | `echo_scan` рахує `bracket_hits` (ECHO_MARKER `"[RESOLVED"`) і `note_hits` (NOTE_MARKER) по T2/T3 (129–148, 438); у звіті `bracket_hits_total` (467) |
| секондарі §8 | ✅ | decomposition wrong_label/invalid_format (244–258); label-level trap repeat (260–280); spread з df=4 CI (304–324); T0−T2 / T0−T3 (353–393, окремі RNG-офсети +1/+2); DR/DX/RT family pass (395–410); guess/position (326–349); tokens/wall (412–425); CU superseded-value share (282–302) |

**Арифметика χ² df=4.** `CHI2_DF4 = {lo: 0.484419, hi: 11.143287}` — це рівно χ²₀.₀₂₅,₄ і χ²₀.₉₇₅,₄ (табличні значення вірні).
- `SD_CI_LO_MULT = sqrt(4 / 11.143287) = sqrt(0.3589550) = 0.5991285`
- `SD_CI_HI_MULT = sqrt(4 / 0.484419)  = sqrt(8.2573028) = 2.8735522`

Формула ✅ (двобічний 95% CI для σ при n=5). Коментарі в коді кажуть `~0.5995` і `~2.8740` — розбіжність ~4e-4 **лише в коментарі**; обчислення використовує `math.sqrt`, тож числа у звіті точні. Косметично, не блокує.

Два зауваження (non-blocking, для run record):
- `guess_caveat` рахує **знакову** дельту (`delta < 2*max_band`), тож при встановленому реверсному ефекті caveat спрацює автоматично. Це буквальне читання §12 («primary delta < 2 × band»), але варто пояснити в run record, що це знакове, а не модульне порівняння.
- `bracket_hits_total` **репортується, а не fail-close**. Клаузула 4 була пілотним GO/NO-GO; для confirmatory її статус — звітний. Executor має явно позначити ненульове значення у run record.

---

## 4. RUN SCRIPT — ✅ усе предекларіоване + новий preflight-гейт справді працює

| Вимога | Статус | Доказ (`run_confirmatory_v3.py`) |
|---|---|---|
| seeds {3001..3005} | ✅ | `SEEDS = (3001,…,3005)` (64) |
| arms primary-first | ✅ | `ARMS = ("T0","T1","A","T2","T3")` (65), порядок циклу 367–368 |
| digest-пін моделі fail-closed | ✅ | `EXPECTED_DIGEST_PREFIX = "36c3c3b9683b"` (68); `if not pinned.get("digest","").startswith(...): SystemExit(2)` (147–150) |
| wall guard 170 хв | ✅ | `WALL_CLOCK_S = 170*60.0` (73); перевірка перед кожним новим arm-seed (371–376) |
| resume без повторного інференсу | ✅ | копіює завершені каталоги `shutil.copytree` і кладе summary в `summaries` (347–366); цикл пропускає `(arm,seed) in summaries` (369) |
| transient retry 1×, attempt-scoped | ✅ | `for attempt in (1,2)` (379); `TRANSIENT = (TimeoutError, ProviderError, OSError)` (61); окремий каталог `seed-{n}-a{attempt}` (156) — часткові артефакти лишаються як доказ |
| **НОВЕ:** preflight звіряє suite + rendered дайджести fail-closed **ДО** інференсу | ✅ | `verify_freeze_digests()` (112–126) читає `frozen-config-v3b.json`, рахує `suite_digest()` + 5 `rendered_seed_digest()`, і на першій розбіжності `SystemExit("FAIL-CLOSED: digest mismatch…")`. Викликається у `main()` рядок **323**, тоді як перший інференс — warm-up chat у `preflight()` рядок **144**, що викликається лише на рядку **333**. Порядок коректний. |
| рецепт збігається з маніфестом | ✅ | manifest `rendered_digest_recipe`: «sha256 over the concatenation of `json.dumps(scenario, sort_keys=True, ensure_ascii=True)` for the seed's rendered scenarios sorted by id; rendering = `continuity.fixtures.render_seed_variant`». Код (92–101): `load_suite_for_seed()` → `[render_seed_variant(s, seed) for s in scenarios]` (`fixtures.py:86`), далі `sorted(scenarios, key=lambda s: s["id"])` і `json.dumps(scenario, sort_keys=True, ensure_ascii=True)`. Збіг дослівний. |

⚠️ Є прапорець `--skip-digest-verify` (311–318, «internal smoke flag: NEVER for a real run»). Він легально потрібен для смоук-тестів, але це єдиний спосіб обійти гейт → виносимо в умову для executor-а (§8.B).

---

## 5. DECLARED CHANGES vs FREEZE-A — ✅ рівно 3 задекларовані + 2 нові; решта byte-identical

Крос-чек дайджестів спільних шляхів v3a ↔ v3b:

| Шлях | v3a | v3b | |
|---|---|---|---|
| EVALUATION-PREP-v3.md | 8276286b | 8276286b | ✅ identical |
| SUITE-V3-DESIGN.md | 442d4385 | 442d4385 | ✅ |
| PREREG-REQUIREMENTS-V2.md | b843888e | b843888e | ✅ |
| PR-REVIEW-v3.md | 6c48b218 | 6c48b218 | ✅ |
| runner.py | 1dcd5625 | 1dcd5625 | ✅ |
| provider.py | 856b9348 | 856b9348 | ✅ |
| fixtures.py | 4270a091 | 4270a091 | ✅ |
| memory.py | 1ef42916 | 1ef42916 | ✅ |
| claims.py | 539bdced | **9c2758bc** | змінено (декларовано) |
| validate_fixtures_v3.py | ec1928a0 | **cadb4552** | змінено (декларовано) |
| assembly_gate.py | 46c989ac | **01061a3c** | змінено (декларовано) |
| analyze/run_confirmatory_v3.py | — | нові | декларовано |

Рівно 3 змінені + 2 нові. `git show --stat 10f2a8d` підтверджує, що у FREEZE-B-коміті зі «старих» файлів торкнулися лише цих трьох (`claims.py | 21 +-`, `assembly_gate.py | 65 +-`, `validate_fixtures_v3.py | 15 +-`).

### 5a. `claims.py` — ✅ рівно пре-авторизований клас

Порівняв `resolve_episodes` до (`10f2a8d^`) і після рядок-у-рядок: **структура керування, умови, порядок гілок, `last_correction_ref`-логіка, R4/R5-предикати, `break`/`continue` — ідентичні до символу.** Змінилися виключно 5 рядків-констант:

| до | після |
|---|---|
| `[RESOLVED: superseded by the retraction at {ref}; the prior standing rule holds]` | `NOTE: superseded by the retraction at {ref}; the prior standing rule holds.` |
| `[RESOLVED: superseded by the value correction at {ref}; the corrected value applies]` | `NOTE: superseded by the value correction at {ref}; the corrected value applies.` |
| `[RESOLVED: unverified user statement - do not apply over verified evidence]` | `NOTE: unverified user statement - do not apply over verified evidence.` |
| `[RESOLVED: unreviewed feed - treat as unverified; verified evidence governs]` | `NOTE: unreviewed feed - treat as unverified; verified evidence governs.` |
| `[RESOLVED: the agent's own earlier answer - lowest trust; …]` | `NOTE: the agent's own earlier answer - lowest trust; …` |

Усі 4 gate-матчувані підрядки збережені: `superseded by the retraction`, `superseded by the value correction`, `unverified user statement`, `own earlier answer` (+ `unreviewed feed`). Також незмінні: `SOURCE_RANKS`, `VERIFIED_BUMP`, `RANK_NAMES`, `RETRACTION_MARKERS`, `CORRECTION_HINTS`, `classify_turn`, `T0..T3_HEADER`, `format_trust_block`, `_prose_prefix`. Єдина інша зміна — +5 рядків docstring про FREEZE-B. **Нуль семантичних змін.** ✅

(Побічно: `_meta_tag()` — єдине місце, що генерувало пайпи — **мертвий код**, ніде не викликається (`grep -rn "_meta_tag" src/ experiments/` → лише визначення).)

### 5b. `validate_fixtures_v3.py` — ✅ жоден чек не послаблено

Діфф (порівняння з `10f2a8d^`): `EXPECTED_PRIMARY["v3j"]`, `CR_SUBTYPES["v3j"]`, `other_suites["v3j"]`, і `seeds_ok if suite == "v3i"` → `suite in ("v3i","v3j")`. Усе адитивне або **посилення** (остання зміна поширює обов'язкову вимогу variant-seeds на v3j).
- `CR_SUBTYPES["v3j"]` **ідентичний** `["v3i"]` (валідатор:72–89) — жодного пост-пілотного cherry-picking.
- v3j доданий до disjointness-сету (182) — і сам v3j тепер перевіряється проти v1/v2/v2-cal/v3/v3h/v3i у **всіх** відрендерених seed-ах (`suite_texts`, 144–157). Артефакт: `V3-disjoint… dup ids []; id overlap []; shared turn texts 0`.
- Пороги не рухалися: V5 ≤0.50, V15 ≤0.50, V16 ≥3 позиції, V4 k≥5.

Зауваження: §2 ставить V15 «targeted at <= 0.45», але в коді поріг лишився 0.50. Фактичний вимір = **0.40**, тож ціль виконана емпірично; гейт просто не затягнутий до 0.45. Non-blocking.

### 5c. `assembly_gate.py` — ✅ адитивно/затягнуто, **G3b перестав бути вакуумним**

- `SUITES["v3j"]`, `PRIMARY_FAMILIES["v3j"]` — реєстрація.
- **G2**: було `"RESOLVED" in block or "SUPERSEDED" in block or "superseded by" in block` → додано `or "NOTE:" in block` (155–156). Посилення.
- **G6**: було `"RESOLVED" or "SUPERSEDED"` → додано `or "NOTE:"` (302). Посилення.
- **G3b — підтверджую вакуумність до фіксу**: стара версія брала `lines = [ln for ln in block.splitlines() if ln.startswith("[s")]`. Після переходу на prose-парентетичний рендерер жоден рядок T2-блоку не починається з `[s` → `lines == []` → перевірка завжди проходила порожньою. Нова версія: `lines = block.splitlines()[1:]` (скидає хедер) + детекція за маркером `"NOTE:"` (271–272). Це **відновлення реальної перевірки**, не послаблення.
- **G3**: додано дві нові CU-гілки (`retracted_correction` 223–238, `user_override` 239–256), кожна з жорсткішими умовами (`len(sup)!=1 or stray or retr_flagged`). Існуючі гілки (`valid_*`, `erroneous_user_correction`, `source_conflict`, `retraction`, `superseded_value`, `scripted_own_answer`) не змінені.

Покриття гілок повне: усі 4 CU-механізми v3j (`retracted_correction`, `user_override`×2, `superseded_value`) мають відповідну гілку → жоден primary-кластер не провалюється «мовчки» крізь elif-ланцюг. Підтверджено артефактом: `G3 … 12 primary scenarios resolved as designed {'user_flag': 4, 'conflict_flag': 2, 'superseded': 3, 'own_answer_flag': 0, 'clean': 3}` = 12/12.

---

## 6. NO-INFERENCE — ✅

- `labs/continuity/results/` містить: `CONT-000, CONT-001-confirmatory, CONT-001-exploratory, CONT-005-C2-PILOT, CONT-005-CONFIRMATORY, CONT-005-PILOT`. **`CONT-005-C2-CONFIRMATORY/` відсутній** ✅
- `post_freeze_hotfixes` у frozen-config-v3b.json **відсутній** (ключі: kind, created_utc, label, spec, frozen_at…, stage, seeds_predeclared, arms_order_primary_first, primary, pilot_context_routed_here, declared_pre_inference_changes_vs_freeze_a, rendered_digest_recipe, digests) ✅
- `git status --porcelain` → порожній вивід; HEAD = `10f2a8d` ✅

---

## 7. ARM-NEUTRALITY + ДИЗАЙН v3j — ✅

Прочитав повні тексти turn-ів усіх 12 primary-кластерів (8 CR + 4 CU).

**(a) Симетричність формулювань корекцій — ✅.** Усі довірчі сигнали несе **сама проза turn-а**, однаково видима T0 і T1:
- cr-4001 «Museum office bulletin, **verified** notice from the county heritage board: … is out of date; docent-guided visits are tours under the standing card»
- cr-4002 «Case-sensor report, **verified output**: … such installs are exhibits»
- cr-4003 «Harbor office bulletin, **verified** notice from the port authority: …»
- cr-4004 «The skipper **insists** … The fuel ledger, **on file**, shows …»
- cr-4005 «The donor **insists** … The visits register, **on file**, shows … a docent-led walking program» (непряма контр-доказовість, без слова-мітки — V6-сумісно)
- cr-4006 «An **unreviewed** harbor aggregator feed claims …» / «the desk **verified** it»
- cr-4007 «the desk **verified** it» / «An **unreviewed** museum forum feed claims …»
- cr-4008 «The bulletin is **withdrawn**: it was **misrouted** … and **does not apply here**; dockside refueling stays **fuel** under the standing card»

Жоден turn не посилається на структуру анотації (немає «the record tagged as …», «source field», «verification status» тощо). T1 лише **переформульовує** в структурований вигляд те, що вже є в прозі — це і є тестована інтервенція, а не перекіс формулювання. ✅ (PR-REVIEW-v3 N1 задоволено.)

**(b) Sub-type баланс CR ідентичний v3i — ✅.**
`valid_correction_environment` 2 (cr-4001, cr-4003), `valid_correction_tool` 1 (cr-4002), `erroneous_user_correction` 2 (cr-4004, cr-4005), `source_conflict` 2 (cr-4006, cr-4007), `retraction` 1 (cr-4008).
Підтверджено двічі: `grep '"sub_type"'` по фікстурах + V7-артефакт (`cr sub-types {…} (need {…})` — обидва словники однакові) + `CR_SUBTYPES["v3j"] == CR_SUBTYPES["v3i"]` у коді валідатора.

**(c) Обидва порядки source-conflict — ✅.**
- cr-4006: s2t1 = `source_type: environment`, «unreviewed harbor aggregator feed» → s2t2 = `source_type: user`, «the desk verified it» → **feed → user**
- cr-4007: s2t1 = `source_type: user`, «the desk verified it» → s2t2 = `source_type: environment`, «unreviewed museum forum feed» → **user → feed** (реверсивний)

**(d) CU-редизайн читається обома руками — ✅.**
- **cu-4101** (retracted_correction): s3 «The maintenance desk says the correction is **withdrawn**: it was **misrouted** … and **does not apply here**; **the standing setting from the first log holds as before**». Правильна відповідь ({old}) виводиться виключно з прози, без анотацій. ✅
- **cu-4102** (user_override): s1 `tool` «The tally screen, **verified readout**: … {old} trays» vs s2 `user` «The weekend baker **insists**: 'correction for the records — … {new} … , not {old}'». Протиставлення «верифікований прилад» vs «людина наполягає» повністю в прозі. ✅
- **cu-4103** (user_override): s1 plain {old} → s2 `tool` «Building monitor, **verified readout** — correction for the records: … now {new}» → s3 `user` «A contractor **insists**: 'the dial reads {alt}'». Очікується {new}; пастка {alt} = найсвіжіше. ✅
- **cu-4104** (v3i-якор, superseded_value): «Correction for the records: the dredge finished; … now {new} … , not {old}». Рецензія-нейтральна — turn-и **взагалі без `source_type`**, тож T1-префікс дає лише «(recorded in session N)», тобто T1 ≈ T0. Коректно як якір, де рецентність працює. ✅

Усі 3 recency-defeat кластери справді перемагають чисту рецентність (expected ≠ останнє згадане значення), 4-й — контрольний якір. Декларований R5-blind-spot (T2/T3 лишають оманливу позначку «superseded» на cu-4101) стосується лише **секондарів**, primary-контраст T0−T1 не зачіпає.

**(e) Дужки/пайпи в рендерених memory-блоках — ✅ (з точною констатацією).**
- Квадратні дужки в текстах turn-ів: `grep '"text": "[^"]*[][]'` по всьому `fixtures/v3j/` → **0 входжень**.
- Пайпи в текстах turn-ів: лише в перелікові словника міток на s1t1 (`exhibits | tours | conservation | security | memberships | facilities`) і в `{options}` (рендериться як `" | ".join(labels)`, `fixtures.py:141`) — це **успадкована проза**, ідентична в усіх руках, присутня й у v3i. `{options}` стоїть лише на probe-turn-ах, які для primary завжди в **останній** сесії, тож у memory-блок не потрапляють.
- Рендерер T1/T2/T3 (`_prose_prefix`) дужок/пайпів не емітить; `_meta_tag` (єдине джерело пайпів) — мертвий код.
- Flat T0 `[sNtM|role]`-префікс (`runner.py:86`) лишається — виняток, обумовлений у завданні як успадкований (T0 = byte-identical arm-B renderer, §1).

⚠️ Пов'язане спостереження для run record (не блокує): після FREEZE-B-фіксу **T0 — єдина рука, чий memory-блок містить брекет-розмітку**, а саме вона була названим механізмом invalid-format-ехо. Це асиметрія T0↔T1, що теоретично завищує дельту на користь T1. Пілотні дані показують, що ефект малий: invalid_format T0 **16/60**, T1 **14/60**, A (без пам'яті взагалі) **16/60** (`pilot-go-nogo.json:68-93`). Обов'язкова декомпозиція §8 реалізована для всіх рук (`analyze_confirmatory_v3.py:244-258`) і покриває цей канал.

**Свіжі gate-артефакти.** `fixture-validation-v3j.json`: `verdict PASS`, 16/16, `failed_checks: []`; ключові цифри — V5 max share **0.20** (потрібно ≤0.50, ≥3 різні позиції: `[0,1,2,3,4,5]`), V15 identical-across-seeds **0.40** (ціль §2 ≤0.45 ✅), V16 PASS, V3 shared turn texts **0**, V8/V11/V13 PASS. `assembly-gate-v3j-seed300{1..5}.json`: усі п'ять `verdict PASS`, 7/7, `failed_checks: []`.
Самі ці артефакти я **перерахувати не міг** (п.2) — умова §8.A.

---

## 8. ВЕРДИКТ

# ✅ GO

FREEZE-B виконано у правильному порядку (§2 stage 2 / §10: аналіз-скрипт ПЕРШИМ, далі v3j, далі валідатор+гейт, далі маніфест, далі цей гейт), до будь-якого v3j-інференсу. Заморожені скрипти реалізують пре-реєстрацію дослівно; зміни проти FREEZE-A — рівно 3 задекларовані, усі в межах пре-авторизованого класу або суто адитивні/затягуючі; жодного послабленого чека; робоче дерево чисте; результатів confirmatory немає. Дизайн v3j арм-нейтральний у єдиному каналі, який структурні перевірки не ловлять.

### Умови для executor-а (обов'язкові)

**A. Побайтове звірування 6 контент-похідних дайджестів (прецедент GATE-V3A п.6).**
Я перевірив 19 із 25 дайджестів незалежно; `fixtures/v3j_suite` і 5 `fixtures/v3j_rendered_seed300x` залишилися неперевіреними через блокування Python у пісочниці цієї сесії. Умова:
1. Запустити `run_confirmatory_v3.py` **без** `--skip-digest-verify`; у логу прогону **мусить** з'явитися рядок
   `freeze digests verified against frozen-config-v3b.json: suite + 5 rendered seeds byte-match`
   перед `preflight ok:`. Будь-який `FAIL-CLOSED: digest mismatch for …` = **стоп, вердикт void**, без ретраїв.
2. Перед прогоном перезапустити `validate_fixtures_v3.py --suite v3j` і `assembly_gate.py --suite v3j --seed N` для всіх п'яти seed-ів, **не перезаписуючи** закомічені артефакти (`--out` у tmp). Звірити: `verdict == "PASS"`, `failed_checks == []`, `suite_sha256 == 516d6588c1c377e891ef87293d937d22e2fdd71dbd318aeaf88367365e7d0889`, і текст усіх `detail`-полів — ідентичний закоміченим. (Повна побайтова рівність файлів неможлива: поле `created_utc` змінюється.)
3. Записати в run record команду й повний вивід обох перевірок.

**B. Прапорець `--skip-digest-verify` заборонений** для цього прогону. Його використання = обхід halt-гейту → §11 вимагає нового non-executor гейту перед читанням результатів.

**C. Rev виконання.** У заголовку артефакту вказати реальний rev (`10f2a8d` або нащадок), а не `10fb461` з поля маніфесту; усі rev-и мультирев-прогону перелічити (§11). Жодних правок заморожених шляхів під час прогону.

**D. У run record обов'язково відобразити (вже реалізовано в аналізі, потрібна лише явна згадка):**
- `error_decomposition_primary` для T0 і T1 поряд із primary-дельтою — через T0-only брекет-асиметрію (п.7e); пілотний baseline 16/60 vs 14/60 vs A 16/60;
- `echo_checks.bracket_hits_total` — якщо ≠ 0, позначити як протокольне спостереження (скрипт це репортує, але не fail-close);
- що `guess_caveat` порівнює **знакову** дельту з `2 × max_band`;
- P5-рядок (0.705 при 8/12) керує силовою заявою — власник підписав 2026-10-06.

**E. Дві констатації з цього гейту, які треба перенести в run record (інформативно, не блокують):**
- `analyze_pilot_v3.py` і `run_pilot_v3.py` відсутні у frozen-config-v3b.json попри буквальне читання §10 («refreshed digests of every frozen path above»); обидва перевірено як **байт-ідентичні** FREEZE-A (`a044e220…`, `05594724…`), тож протокольної шкоди немає.
- Коментарі `~0.5995` / `~2.8740` біля `SD_CI_*_MULT` розходяться з точними 0.599129 / 2.873552 на ~4e-4; обчислення точні, це суто коментар — **правити заморожений файл не можна**, лише зафіксувати.


---

## Додаток executor-а — куративна перевірка тверджень гейту (2026-10-06)

1. Пілотні скрипти: analyze_pilot_v3.py / run_pilot_v3.py перехешовані
   executor-ом — байт-ідентичні дайджестам FREEZE-A (a044e220…, 05594724…) —
   підтверджено.
2. Артефакти: fixture-validation-v3j.json V15 identical-share 0.40,
   suite_sha256 == маніфест v3b; усі 5 assembly-gate вердікти PASS з
   failed_checks=[]; G3-розподіл {user_flag: 4, conflict_flag: 2, superseded:
   3, own_answer_flag: 0, clean: 3} = 12/12 — підтверджено.
3. Вердикт-формулювання §6: усі чотири константи analyze_confirmatory_v3.py
   звірені зі спеком (нормалізація пробілів + імпорт констант) — дослівно.
   (Розбіжність у сирцевому grep була артефактом конкатенації літералів та
   переносів markdown.)
4. Дайджести: 19 файлових шляхів незалежно збігаються (гейт) + власний
   генератор маніфеста і self-check run-скрипта (verify_freeze_digests PASS) —
   ланцюг замкнено з трьох сторін.
5. Умови A-E прийняті до виконання (див. LOG/run record): запуск без
   --skip-digest-verify; свіжі validator+gate у tmp перед прогоном; реальний
   rev виконання у run record; декомпозиція/echo/guess-caveat/P5 — у звіті;
   дві інформативні констатації (пілотні скрипти поза маніфестом v3b;
   коментарі ~0.5995/~2.8740 vs точні 0.599129/2.873552) перенесено сюди.
