# REVIEW-FABLE-CONT006 — independent full-arc review (post CN-012 invalidation)

- **Reviewer:** model "Fable" via Claude Code CLI (`claude --model fable -p`), fresh context, read-only, repo root (first in the standing queue; limit had reset). Launched on the owner's directive ("при відновленні моделі Фабла прогнати незалежне ревю").
- **Date:** 2026-10-09, after the CN-012 invalidation commit a8c7c97; reviewed the full arc incl. all four gate records, the co-owner's PRELIM-REVIEW-CONT006-BAD-LESSON.md, and the invalidated confirmatory record.
- **Verdict (summary):** invalidation CONFIRMED (independently verified from artifacts); three NEW findings F-1..F-3 (F-1: the CN-012 fix kept a hard-coded tuple with a comment falsely claiming derivation — fixed same day; F-2: the memory guard carried its own parallel arm list — fixed; F-3: the anchor-divergence 26pp signal was printed in pilot artifacts with no stop criterion attached); rerun recommended only after a short design milestone (guard hardening + per-family headroom + MME 0.20 + multi-trace worker + fresh v3m suite). Cross-reference: docs/REVIEW-CONT006-CN012-RERUN.md (co-owner, same day — RC-1..RC-6 largely overlapping).

---

## Raw review (Fable, verbatim)

Усі артефакти прочитані: пріга+дизайн, 4 гейти, моє минуле рев'ю, прелім-рев'ю, CN-012, LOG-хвіст, runner.py/run_cont006.py (пост-фікс), pilot-gate JSON, confirmatory summary + run-record header (INVALID), активні стори; телеметрію інвалідних трейсів перевірив сам (summary/trace greps). Нижче повний звіт.

---

# Незалежне рев'ю CONT-006 (повний arc) після інвалідації — Fable, 2026-10-09

Read-only; python-запуски обмежив до read-only інспекції JSON/trace (greps + event-census) — усі числа нижче або перевірені мною по артефактах, або явно позначені як цитовані.

## A. Аудит arc-у свіжим оком

### A.0 Самостійно підтверджені факти CN-012

- `R0/R1/R2/seed-6003/summary.json` конфірматорки: **`memory_episodes: 0` у кожному** — поле лежало у КОЖНОМУ закоміченому summary всього ланцюга.
- R0/seed-6003/trace.jsonl: **35 подій `memory.injected`, 0 з `"injected": true`** — телеметрія порожніх ін'єкцій теж була в кожному трейсі.
- Тобто CN-012 не «прихований» дефект: сигнал був надрукований у артефактах від Phase V і далі. Його ніхто не читав. Інвалідація обґрунтована (див. D.1).

### A.1 Чи є ЩЕ дефекти класу CN-012 (тихі конфіг-розриви)? Так — три знахідки

**F-1 (сам фікс CN-012 містить doc-code розрив — клас RC-4).** `runner.py:452-458`: коментар стверджує «the tuple now derives from memory_arms so it can never drift again», але рядок 452-453 — **досі захардкоджений літерал** `("B","C","D","E","T0".."T3","R0".."RGOLD")`, НЕ похідний від `memory_arms` (runner.py:206). Зміст зараз збігається, але вектор дрейфу, що породив CN-012, живий, а коментар бреше про його усунення. Виправити буквально: `if arm in memory_arms:`.

**F-2 (другий паралельний кортеж).** `run_cont006.py:308`: `appends_expected = arm in ("R0","R1","R2","R3","RBAD","RGOLD")` — memory-guard сам тримає ВЛАСНИЙ захардкоджений список арм. Якщо CONT-007 додасть арму, її треба буде не забути у ДВОХ місцях знову. Guard має імпортувати членство з runner (single source of truth), або, краще, fail-closed жити в самому runner-і: memory-арма, що закінчила мультисесійний сценарій з `memory.count()==0`, — виняток на місці, незалежно від експериментального скрипта.

**F-3 (анкерна дивергенція — виміряна, надрукована, не зв'язана критерієм).** Потужність b0 = 0.525 заякорена на C2 T-армах (мій RC-1); CN-A прямо каже «if R0 behaves differently the realized power shifts». Пілотний R0 TR = **0.267 — мінус 26 пунктів від анкера**; Phase V S0 = **0.0714 (2/28!)** проти того ж очікування ~0.5. Критерій 5 чесно перерахував потужність на 0.267 і… пройшов (0.857), бо ніякий критерій не питав «ЧОМУ memory-арма дає половину свого анкера». Це і є передбачувана guard-діра №1: дані кричали з Phase V, а протокол мав лише ceiling-headroom (R0 ≤ 0.75) — перевірку на занадто ЛЕГКО, не на занадто ДИВНО-ВАЖКО.

### A.2 (i) Чи міг R1 актюватися без епізодів

Частково актюався — це треба зафіксувати точніше, ніж у CN-012. Event-census R1/seed-6003: **53 `selfmodel.injected`, 53 `reflection.commit`, 61 `reflection.proposal`, 19 `selfmodel_failure_pattern`** — selfmodel-блок рендерився щосесії, і рефлексія КОМІТИЛА failure-патерни з in-run probe-результатів. Але шлях, який і є суттю R1-очікування (конфлікт-рев'ю над епізодами пам'яті; механізм CONT-001 D−C parroting +0.5015), був виголоджений: 0 епізодів → нічого juxtapose-ити. Отже R1 пробіг як «no-memory + статичний selfmodel + рефлексія-над-пробами»; R1−R0 = 0.000 консистентно з цим, і **секондарі «parroting replication» не тестувалася взагалі**. Формулювання CN-012 «zero episodes to reflect on» вірне щодо епізодів, але «reflection was inert» було б хибним — вона бігала і комітила, просто не тим каналом.

### A.3 (ii) Валідність RBAD-парротингу і VAL-активацій без пам'яті

- **RBAD-парротинг — валідний і за відсутності пам'яті.** 4-грам «two fitting choices in your own words» потрапив у відповідь із lesson-блоку контексту; пам'ять у ланцюзі доставки не бере участі. Застереження одне: з пам'яттю контекст щільніший, тож ВЕЛИЧИНА салієнтності уроку може бути іншою — existence proof стоїть, кількісне узагальнення ні.
- **VAL-активації — валідні як liveness, НЕвалідні як рішення §7.2.** +0.214/+0.250 доводять, що канал рухає поведінку проти «нічого». Але §7.2 — це генералізаційна валідація уроків ПОВЕРХ пам'яті: S0 мав бути memory-базою (~0.5), а був 0.0714. Рішення ACTIVATE ухвалене на чужій базі; за preреговою семантикою воно **void**, і в перезапуску Phase V обов'язково переганяється. Самі ТЕКСТИ сторів валідні (корпус-деривовані, нуль v3l-контенту — контамінаційний гейт це довів незалежно).

### A.4 (iii) «Випадкова аблація ≈ критичний тест 1» — завищена заява

Конфігураційно R2-клітина — буквально «lessons without episodic memory» (тест 1). Але тест 1 цінний КОНТРАСТОМ проти full-R2 (lessons+memory), якого не існує. Фактично пробігло «lessons-only vs nothing-only»: Δ=0.019 каже лише, що уроки самі по собі не покращують коректність над голим агентом — на цій поверхні, з цим (формат-домінованим) стором, при band-роздутому MME 0.333, з потужністю, що ніколи не рахувалася для цього контрасту. Чесне читання: **незареєстрований експлораторний датапойнт**, корисний як прикидка для майбутнього тесту 1, не як його виконання. Фраза «≈ критичний тест 1» у LOG/CN-012 хай живе з лапками «≈» і цим абзацом поруч.

Що в цьому датапойнті реально сильне і реплікується двічі (пілот + конфірматорка): **формат-ефект**. R2 0.0095 / R3 0.029 проти R0 0.162 / R1 0.133 format-miss — і конверсія мисів у **wrong_label** (R0 68 → R2 82 зі 105), не в правильні відповіді. Це найцінніший behavioral-результат arc-у: канал доставляє і виконується, але носить не те знання.

### A.5 (iv) Чому ЖОДЕН гейт не зловив порожню пам'ять; чи була діра передбачуваною

Передбачуваною — так, на трьох рівнях, і це головний процесний урок arc-у:

1. **Diff-рев'ю ловить коміссії, не оміссії.** GATE-CONT006 check 7 построково перевірив `runner.py` diff і навіть перелічив arm-membership кортежі («memory requirement keeps the old 8 arms and adds the R-arms») — але append-кортеж на :452 у diff НЕ з'являвся, бо його якраз і не змінили. Гейт перевіряв «чи не змінено зайвого», ніхто не перевіряв «чи змінено все потрібне». Інваріант «кожен arm-gated блок runner-а покриває нові арми» ніде не був механізований.
2. **Асиметрія guard-ів нового vs старого каналу.** Пріга §10 має store-integrity guard, retrieval-телеметрію, «zero rendered blocks for empty store» — ВСЕ для уроків (нового каналу). Для пам'яті — субстрату всієї лабораторії — нуль liveness-перевірок: ніхто не вимагав ненульових append-ів/ін'єкцій. Мушу зафіксувати власну частку: **моє PR-REVIEW-CONT006 поставило §10 ✅ і цієї асиметрії не побачило.** Усі п'ять RC були про lesson-машинерію і статистику; «чи справді біжить старий канал» я не спитав так само, як і всі.
3. **Усі гейти були pre-inference / artifact-oriented.** Чотири гейти ре-хешували фрізи, симулювали рендерери, перевіряли нуль-інференс — жоден не мав мандату читати телеметрію ЖИВОГО рана перед тим, як аналізатор читає результати. Єдиний live-читач — сам аналізатор, а він рахує лише probe.result. Плюс A.1/F-3: анкерна дивергенція 26 пунктів була надрукована у pilot-gate і не мала зв'язаного стоп-критерію.

Висновок (iv): guard-діра була передбачувана як КЛАС (паралельні захардкоджені кортежі + відсутність live-telemetry гейту), не як конкретний рядок. Owner-ова інтуїція спрацювала там, де протокол структурно не дивився.

## B. Оцінка прелім-рев'ю ко-овнера (PRELIM-REVIEW-CONT006-BAD-LESSON.md)

**Загалом — згоден, рев'ю коректне і корисне.** Головна кларифікація (BAD — синтетичний контрфакт з declared bypass, парротинг ≠ якість worker-а; тестована межа — containment ПІСЛЯ активації, тоді як справжня лінія оборони — ДО активації) — точна і збігається з конструкцією преріги (RC-3 fold, `bypasses_evidence_validation: true`). Числа (R0 0.286 / RBAD 0.429; GOLD 0.214→0.143, 0.071 < 0.10) звірені з pilot-gate-cont006.json — усі точні. Правильно і те, що locally-higher score RBAD не рятує критерій: пріга зумисне карає сам факт цитування.

Що пропущено або потребує поправки:

1. **Воно теж не побачило CN-012, маючи докази перед очима.** Рев'ю читало «RBAD traces, especially RBAD/seed-6002/trace.jsonl» — трейс, де кожна `memory.injected` порожня і `memory_episodes: 0`. Це не докір (ніхто не побачив), але підтвердження A.5: вузько-сфокусовані рев'ю успадковують сліпі плями протоколу.
2. **Недооцінений криtерій-6 сигнал.** Рев'ю називає GOLD-TRIV «weak directional evidence» — формально так на 14 пробах, але вже В ТОМУ Ж pilot-gate критерій 6 показував R2/R3 invalid-format 0.000 проти R0 0.133 / R1 0.200 на всіх TR-пробах: liveness каналу вже тоді була сильною, не слабкою. Конфірматорка це підтвердила (0.0095/0.029 vs 0.162).
3. **П.4 рекомендацій («не вчити агента second-guess-ити активні уроки») — спірний як загальне правило.** Для ЧИСТОТИ вимірювання CONT-006 — так. Для архітектури — RBAD показав, що виконання уроку без жодного тертя з очевидним конфліктом задачі (проба явно просить один лейбл) — це і є знахідка; «челендж-канал» (CHALLENGE_LESSON existed у схемі!) — легітимний напрям, а не загроза вимірюванню. Варто формулювати як «не в цьому експерименті», не «не робити».
4. Статус-рядок «preliminary until the confirmatory result is available» тепер застарів подвійно: конфірматорка і відбулась, і інвалідована; документ вартий одно-абзацного post-CN-012 апдейта (висновки рев'ю, до речі, інвалідацію ПЕРЕЖИВАЮТЬ — вони всі про lesson-канал).

## C. Перегрунтування експерименту (директива owner-а)

### C.1 Per-family headroom gates — так, це друга ключова дірка поряд із CN-012

Цикл-2 мав **per-family `0.15 < mean < 0.85` в ОБОХ армах** (EVALUATION-PREP-v3 §2 cl.1; мій же PR-REVIEW-v3 RC1 змусив прибрати pooled-формулювання, бо pooled 0.50 ховав «6/8 CR на 1.0 + 4/4 CU на 0.0»). CONT-006 пріга залишила тільки **pooled R0 ≤ 0.75 — ceiling-only, без floor, без per-family**. Наслідки вже в даних: per-class таблиця конфірматорки показує класи на нулях і від'ємних дельтах при базі ~0.16-0.27 — частина сімейств напевне лежала під floor-ом, де Δ=+0.33 арифметично недосяжна. А головне — **floor-гейт майже напевно зловив би CN-012**: R0 memoryless на CU/RT-сім'ях (завдання, рішення яких ЖИВЕ в пам'яті) мав бути біля нуля, і per-family floor заверещав би на пілоті. Відновити цикл-2 формулювання: per-family (0.15, 0.85), обидві арми контрасту, плюс anchor-divergence стоп з A.1/F-3: `|R0_measured − b0_anchor| > 0.15 → halt & investigate` (не параметр-мув — саме investigate).

### C.2 Композиція memory+lessons: перерахунок усього статистичного каркаса

З пам'яттю R0 ≈ 0.5+ (анкер 0.525). Тоді:

- **MME 0.333 стає структурно майже недосяжним**: R2 мусив би ≥ 0.86 — за стелею headroom-бенду. Band-правило (мій RC-2 fold) спрацювало на **n_gc=12** пробах: dev 0.167 ≈ 2 проби; у конфірматорці на n=42 band_dev 0.095–0.118 — біля/нижче порога. Тобто подвоєння MME було, ймовірно, small-n артефактом. Фікс у новій прерізі: або (a) band-читання «paired-Δ cancels, caveat-only» (перша опція мого ж RC-2 — я б тепер обрав її), або (b) формула з мінімальним n (band міряти на повному GC-наборі конфірматорки чи на ≥40 пробах, не на 12). Повернути MME 0.20 і перерахувати потужність на калібрświatomu b0 з пілота-з-пам'яттю.
- **Контекст-бюджет досі не тестований у комбінації**: memory-блок + lesson-блок (≤165 слів) + selfmodel (R1) + сесійні терни при num_ctx 4096. Інвалідний ран ніколи не вправляв сумарне навантаження. Обов'язковий офлайн-смоук: повний мультисесійний сценарій на КОЖНІЙ армі з assert-ами на (а) ненульові append-и, (б) непорожні ін'єкції на s≥2, (в) непорожній lesson-рендер, (г) відсутність тихого context-clip (prompt_tokens < num_ctx з запасом). CN-012-смоук («R0 cu-сценарій → 8 append-ів») — лише чверть цього.

### C.3 Worker-бандлінг: per-trace → multi-trace, щоб FIX-B помер як клас

POSTW довів: per-trace бандли роблять §7.1(b) (≥2 трейси) **структурно несатисфайним** — 58/58 відмов предетерміновано, і рятував пост-хок кластеринг (FIX-B), тобто крос-трейс evidence став артефактом валідатора, а не worker-а. У перезапуску крос-трейс підтримка має бути природною: бандли груповані по сценарій-сім'ї/класу через ≥2 трейси (напр., «усі cu-ранcluster X по всіх армах-сідах» в один виклик, num_ctx дозволяє 8192 після key-turn конденсації), worker сам цитує кілька трейсів. Це усуває і arity-двозначність (FIX-A): один формат ref-ів, зафіксований прикладом у промпті. FIX-A/B/C-уроки конвертувати в дизайн, не нести як патчі.

### C.4 Зміст уроків: формат домінує — балансувати репортингом і дедупом, не квотою

Корпус: FP-6 271 (проти 629 сум інших) → R2-стор: **3 з 4 уроків — format-compliance, з них два майже тезки** («Format Compliance for/in Classification Tasks» — Jaccard < 0.70 пропустив семантичні дублі), що з top-k=3 означає: retrieval майже завжди палить 2-3 слоти на один і той самий формат-ритуал. Звідси і результат: формат вилікуваний, зміст — ні. Рекомендації (усі пре-реєстровані, без тюнінгу на v3l-результатах): (а) семантичний дедуп або per-class cap = 1 для FP-6 у сторі (FP-6 — cross-cutting клас за таксономією, йому не потрібні три примірники); (б) телеметрія class-coverage стора як предекларований репорт; (в) НЕ квотувати accepted по класах силоміць — якщо worker не видобуває не-форматні уроки з крос-трейс бандлів (C.3), це чесний негативний результат про worker, його не можна маскувати стратифікацією. Гіпотеза для нової преріги: multi-trace бандли + 1×FP-6 cap → стор з реальним шансом нести зміст.

### C.5 R1

У перезапуску R1 нарешті матиме епізоди — конфлікт-рев'ю актюється, parroting-очікування (R1 ≤ R0) стане тестованим уперше на цій поверхні. Залишити як є (byte-stable baseline, per-run copy selfmodel — пілотний фікс уже в коді), лише додати у смоук assert на ненульові епізод-деривовані reflection-саммарі (щоб відрізнити A.2-режим від повного).

### C.6 Фікстури і стори: що реюзабельне

- **v3l — НЕ реюзати для нового конфірматорного ендпойнта.** Не через модель (frozen weights, temp 0 — модель-side контамінації нема), а через дизайнер-side: перегрунтування (headroom-гейти, MME, баланс уроків) ухвалюється ЗНАЮЧИ покластерні v3l-результати всіх арм — реюз означає, що гейти калібровані на тест-сеті. Сама пріга має прецедентне правило: «any rebalance = a NEW suite + fresh review». Білдер-пайплайн здешевлює v3m до дня роботи: нові світи, нові сіди {7001..7007}, той самий валідатор.
- **Таксономія, корпус-маніфест, worker-машинерія (пост-фікс), аналізатори, run-скрипт — реюз без застережень** (параметри аналізаторів перефрізяться під нову прерігу).
- **Лесон-ТЕКСТИ R2 (4) і R3 (8) — реюзабельні**: деривовані тільки з корпусу, нуль v3l-контенту (контамінаційний гейт), v3m вони теж не бачили. Але якщо приймається C.3/C.4 — worker перебігає по-новому, і старий R2-стор стає baseline-порівнянням, не основним. R3 gold — реюз прямий (blind-протокол не порушується: автор не бачив ані v3l, ані v3m).
- **Активації R2/R3 — void (A.3), Phase V переганяється** на v3m VAL-кластерах проти R0-з-пам'яттю. BAD/GOLD-TRIV тексти — реюз з обов'язковим пере-прогоном 4-gram-чека проти рендереного v3m (механіка готова).
- **VAL-кластери/поріг +0.05**: поріг лишити (слабкий директивний бар за дизайном — з пам'яттю він стане строгішим природно, бо S0 виросте); але додати у V-activate той самий anchor-check (S0 проти очікуваної бази) — ще одна точка, де CN-012-клас ловиться за копійки.

## D. Вердикт і рекомендації

### D.1 Інвалідація — ПІДТВЕРДЖУЮ

Самостійно верифіковано: `memory_episodes: 0` у конфірматорних summary всіх арм, 35/35 порожніх `memory.injected` у перевіреному R0-трейсі, CN-012-кортеж у runner.py. Пробігли не пре-реєстровані арми; вердикт «no confirmatory difference» як тест R2-vs-R0-поверх-пам'яті нікчемний. Маркування run-record INVALID зі збереженням замороженого виводу аналізатора як запису незареєстрованої аблації — правильна форма.

### D.2 Статус артефактів

**Валідні без застережень:** таксономія; корпус-маніфест; v3l як suite-артефакт + валідатор (19/19); обидва аналізатори; worker raw log + v2-стори (тексти); R3 gold-уроки (blind-протокол цілий); counterfactual-тексти + 4-gram-чекер; всі 4 гейт-записи як процесні документи; **пілотний RBAD-парротинг** — як властивість lesson-каналу (headline-результат arc-у).

**Валідні з застереженнями:** VAL-активації +0.214/+0.250 (liveness проти «нічого»; рішення ACTIVATE — void); **формат-ефект** (0.162→0.0095, реплікований двічі) — сильний, але виміряний без пам'яті; конфірматорні дані — як незареєстрований lessons-only-vs-nothing датапойнт («≈ тест 1» — із застереженням A.4); GOLD-TRIV 0.071 — directional.

**Втрачено:** первинний вердикт; R1-контраст (parroting-реплікація не тестувалась); pilot-критерії 4-5 (headroom/power на фіктивній базі); band-деривований MME 0.333 (міряний на memoryless армах, n=12); обидва R1-пілотні інциденти часу не компенсують — Phase V/P/C GPU-година спалена.

### D.3 Пріоритезовані зміни перед перезапуском

1. **Guard-hardening (нуль GPU):** F-1 (кортеж реально деривувати з `memory_arms`, коментар зробити правдою), F-2 (guard-членство з runner-а; fail-closed у самому runner-і), повний комбінований смоук C.2 (усі канали, всі арми, assert-и на телеметрію).
2. **Anchor-divergence стоп-критерій** у Phase V і пілоті (|виміряне − анкер| > 0.15 → halt & investigate). Найдешевший CN-012-детектор.
3. **Per-family headroom gates (0.15, 0.85), обидві арми** — повернути цикл-2 формулювання (C.1).
4. **MME назад до 0.20 + band-фікс** (caveat-only paired-читання або min-n), потужність перерахувати на базі пілота-з-пам'яттю (C.2).
5. **Worker: multi-trace бандли** (C.3) — FIX-A/B у дизайн.
6. **Стор-композиція: семантичний дедуп / FP-6 cap + class-coverage репорт** (C.4).
7. **v3m + сіди {7001..}**; Phase V перегнати; реюз за C.6; 4-gram re-check контрфактів.
8. **Live-telemetry гейт:** перед тим як БУДЬ-ЯКИЙ аналізатор читає результати — механічна перевірка channel-liveness усіх арм (append-и, ін'єкції, lesson-рендери, context-fit). Це закриває клас «усі гейти pre-inference» назавжди.

### D.4 Перезапускати зараз чи design-мілстоун?

**Спершу design-мілстоун, і він короткий.** Мінімальний перезапуск «тільки CN-012-фікс, усе інше заморожене» юридично чистий, але науково приречений: MME 0.333 на базі ~0.525 вимагає R2 ≥ 0.86 (за стелею), стор на ¾ формат-уроків уже довів, що лікує не те, а headroom-гейтів нема — третя поспіль «no difference» була б куплена за GPU-годину передбачувано. Пункти D.3 — це ~2-3 дні zero-GPU роботи (пріга-амендмент + v3m + смоук) плюс стандартний цикл рев'ю-гейт. Один дешевий GPU-крок всередині мілстоуна: 2-сідовий калібрувальний пілот R0-з-пам'яттю на v3m для чесного b0 перед фіксацією MME. Після цього — повний перезапуск за звичною фазовою дисципліною.

**Одним рядком:** arc процедурно найщільніший в лабораторії — і саме він показав межу pre-inference-гейтів: п'ять ревізій заморожених артефактів не замінили одного погляду на живу телеметрію; перезапуск вартий того лише після короткого перегрунтування (memory-guards + per-family headroom + MME 0.20 + multi-trace worker + v3m), бо формат-ефект і RBAD-парротинг уже довели, що канал живий — тепер треба чесно виміряти, чи вміє він нести зміст.

---

## Executor curation appendix

Load-bearing claims re-verified against the repo before folding (mandatory rule):

1. **A.0 (memory_episodes 0 in every summary; 35/35 empty injections in R0/seed-6003)** — CONFIRMED (stores 0 episodes; injection census run by the executor during the owner-instigated audit, and re-confirmed post-review).
2. **F-1 (append tuple still a hard-coded literal with a false "derives from memory_arms" comment)** — CONFIRMED by reading runner.py:452-458 at review time. Fixed the same day: `MEMORY_ARMS` hoisted to module level; run_scenario and the run-script guard both derive from it (F-1 + F-2 + RC-1).
3. **F-2 (guard's own parallel arm list in run_cont006.py:308)** — CONFIRMED; fixed via `from continuity.runner import MEMORY_ARMS`.
4. **F-3 (pilot R0 TR 0.267 vs anchor 0.525; Phase V S0 0.0714; criterion 5 recomputed power at the divergent base instead of halting)** — CONFIRMED from pilot-gate-cont006.json and the prereg text.
5. **A.2 (R1 census: 53 selfmodel.injected / 53 reflection.commit / 61 reflection.proposal — reflection ran and committed, only the episode channel was starved)** — CONFIRMED by census of R1/seed-6003. CN-012's wording updated in spirit: R1's reflection was NOT inert; the episode-derived pathway was.
6. **Numbers in section B (0.286/0.429; 0.214->0.143)** — CONFIRMED from pilot-gate-cont006.json (already verified at the pilot gate).
7. **C.4 (three of four R2 lessons are format lessons, two near-duplicate titles; injection census 265/265/228/37)** — CONFIRMED from the v2 store and the confirmatory telemetry census run during this audit.

## Disposition (folded same day)

| Item | Change | Where |
| --- | --- | --- |
| F-1 / RC-1 | MEMORY_ARMS single source of truth at module level; run_scenario append branch derives from it; comment now true | src/continuity/runner.py |
| F-2 / RC-1 | memory guard imports MEMORY_ARMS (no third list) | experiments/suite-v3/run_cont006.py |
| RC-2 / Fable C.2 | combined_channel_smoke.py committed as a permanent regression test (every memory arm on a REAL multi-session v3l scenario; asserts appends > 0, non-empty injections at s>=2, lesson renders, R0/R2/R3 identical episodic refs, no context clip) — PASS x5 | experiments/cont006/combined_channel_smoke.py; frozen paths |
| F-3 / C.1 / D.3.2 | NOT folded yet — belongs to the rethink milestone (anchor-divergence stop criterion + per-family headroom gates + MME 0.20 + band min-n + multi-trace worker + v3m decision): owner-gated next step | docs/ (to be authored in the rethink milestone) |

The rethink itself (Fable C/D + co-owner RC-3..RC-6 + Stage A/B) is NOT executed here: it is a design milestone requiring the owner's go, per both reviews' recommendation ("спершу design-мілстоун" / "new review chain before GPU").
