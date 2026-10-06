Усі перевірки завершено. Підсумок гейта:

---

# GATE-V3A — вердикт NON-EXECUTOR гейта (FREEZE-A, перед пілотом v3i)

## 1. COMPLETENESS — ✅
Маніфест `frozen-config-v3a.json` (25 дайджестів, frozen rev `2d926212c2c0`) покриває весь список §10 FREEZE-A: prereg (`EVALUATION-PREP-v3.md`), `SUITE-V3-DESIGN.md`, validator, `assembly_gate.py`, `claims/runner/provider/fixtures.py`, run script, **analyze script**, suite-дайджест v3i + 5 rendered-seed дайджестів, seeds `[2001..2005]`, arms order. Понад §10 заморожено ще: `PREREG-REQUIREMENTS-V2.md`, `PR-REVIEW-v3.md`, `memory.py`, fixture-validation + 5 assembly-gate артефактів — це не «зайве», а консервативне розширення (memory.py — runtime-залежність run script, гейт-артефакти — докази пунктів §2; заморозити більше — безпечно). Нічого з §10 не пропущено.

## 2. DIGEST RE-HASH — ✅ (19/25 незалежно; 6 — ланцюжком)
Незалежно перерахував sha256 **усіх 19 файлових шляхів** — усі збігаються, зокрема:
- `analyze_pilot_v3.py` → `a044e2200028` ✅
- `run_pilot_v3.py` → `055947248048` ✅
- `EVALUATION-PREP-v3.md` → `8276286b0872` ✅
- `claims.py` → `539bdced9d56` ✅, `fixtures.py` → `4270a0916ab2` ✅
- `fixture-validation-v3i.json` → `b27e554a91ee` ✅, усі 5 assembly-gate-v3i-seed*.json ✅

⚠️ **6 обчислюваних дайджестів** (`v3i_suite` + 5 rendered-seed): sandbox заблокував виконання Python/PowerShell-хешера, тому прямий перерахунок не виконано. Suite-дайджест верифіковано **ланцюжком**: `fixture-validation-v3i.json` (сам перехешований ✅, згенерований замороженим validator-ом, алгоритм `suite_digest` = sha256(relpath+bytes, sorted) у `validate_fixtures_v3.py:124`) містить `suite_sha256 = f5c0f5a9bab7` — побайтово дорівнює значенню маніфеста. Rendered-seed дайджести ланцюжкової верифікації не мають → умова для executor-а (п.6). Додатково: рецепт обчислення rendered-дайджестів **не зафіксований у жодному замороженому скрипті** — зафіксувати команду в run record.

## 3. ANALYSIS SCRIPT — ✅ (умова verify-pass GO виконана)
`analyze_pilot_v3.py` існує, в маніфесті, реалізує рівно клаузули 1–4 §2:
- **Cl.1**: per-family (CR 8 / CU 4), строго `0.15 < mean < 0.85`, обидві арми T0+T1 (`HEADROOM=(0.15,0.85)`, рядки 202–215) ✅
- **Cl.2**: sd 5-ти per-seed means, χ² df=4 CI — мультиплікатори `sqrt(4/11.1433)≈0.5992` і `sqrt(4/0.4844)≈2.874` — звірив з табличними χ²₄(0.975)=11.1433, χ²₄(0.025)=0.4844 ✅; поріг 0.25 по точковій sd (PR-REVIEW N3) ✅
- **Cl.3**: live = обидві арми строго в (0.10,0.90) per cluster, `LIVE_MIN=8` з 12 ✅
- **Cl.4**: `'[RESOLVED'` по `trace.jsonl` T2/T3 (`agent.response`), invalid-format decomposition per-arm ✅
- Fail-closed: неповні primary arm-seeds → verdict `incomplete`, без підстановок (§7) ✅. Routing при провалах (rebalance / P4 / P5 / NOTE-fix) дослівно відповідає §2.

## 4. RUN SCRIPT — ✅
`run_pilot_v3.py`: arms `("T0","T1","A","T2","T3")` primary-first ✅; seeds `(2001..2005)` = manifest.json `variant_seeds` ✅; per-seed рендер через `load_suite_for_seed` (рядок 136) ✅; digest pin `36c3c3b9683b` fail-closed у preflight ✅; wall guard `170*60 s` (не стартує нові arm-seeds) ✅; бюджети per-scenario (40 turns / 100k tokens / 600 s) ✅; resume копіює лише `completed` arm-seeds без повторного інференсу ✅; transient retry 1× з attempt-scoped dirs ✅.

## 5. NO-INFERENCE — ✅
`results/CONT-005-C2-PILOT/` **не існує** (є лише cycle-1 `CONT-005-PILOT`/`CONT-005-CONFIRMATORY` від 2026-10-05). У маніфесті немає `post_freeze_hotfixes`. Working tree clean, LOG-хвіст описує лише zero-inference кроки (smoke на синтетиці, validator 16/16, gate 7/7×5).

## 6. SANDBOX CONDITION для executor-а (перед запуском, PASS = побайтовий збіг):
```
python - (з labs/continuity):
  suite_digest(fixtures/v3i)                  == f5c0f5a9bab7...310
  sha256(rendered seed s) для s=2001..2005    == 4527d3a2... / 56cf3b17... / 14861... / 6ff94... / 2d7f3...
```
Використати той самий рецепт, яким фриз-сесія рахувала rendered-дайджести, і **записати команду/рецепт у run record** (зараз він ніде не зафіксований). Будь-який mismatch → STOP, не запускати інференс.

---

## ВЕРДИКТ: **GO** для пілотного GPU-забігу CONT-005 cycle-2

Умови (не блокують запуск, але обов'язкові): (а) executor перераховує 5 rendered-seed дайджестів + suite-дайджест перед `run_pilot_v3.py` (п.6); (б) рецепт rendered-дайджестів фіксується у run record; (в) після забігу — тільки заморожений `analyze_pilot_v3.py`, нуль ad-hoc аналізу.
