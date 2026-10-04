# Owner brief template — phone-first arc report skeleton

Origin: the 2026-10-04 review cycle — structure proposed by the GLM-5.3-Flash review,
hardened by the Fable review (`docs/REVIEW-FABLE.md` §6), adopted for every future
arc-closing report in this lab. Goal: the owner reads the decision-relevant truth in
~90 seconds from a phone; depth lives in artifacts, links use stable file paths.

Hard rules: ≤80 lines total; verdict and decisions on the first screen; every number
carries a CI and a direction; no commit hashes in the body (audit trail goes to
LOG.md); no table wider than 3 columns; each decision ships with a one-word default
so the owner can reply "ok to all / ok except #N".

```markdown
# <ARC NAME> — owner brief (<date>)

## VERDICT
<one sentence: what the arc established, exactly as pre-registered>
<caveat line: the main thing the number does NOT mean — floors, power, scope>

## ВАМ НА РІШЕННЯ / DECISIONS FOR YOU
1. <decision in the imperative> — default: <accept|yes|no|defer>. Context: <1 line>. Artifact: <path>
2. … (max 6; every item has a default)

## ЩО СТАЛОСЬ / WHAT RAN
<4–5 lines: arms/runs/counts; crashes and deviations stated plainly, unrounded>

## ЧИСЛА / NUMBERS (≤6, each with CI + direction)
- <metric>: <value>, 95% CI [.., ..] — <direction phrase>

## НЕГАТИВИ Й ВІДХИЛЕННЯ / NEGATIVES & DEVIATIONS
- <what failed, what deviated from protocol, what was fixed how — no smoothing>

## ЩО НЕ ДОВЕДЕНО / NOT CLAIMED
- <3 bullets: exploratory-only signals, construct limits, scope bounds>

## ЛІНКИ / DIG DEEPER
- <pre-registration path> · <results-summary path> · <findings path> · <review path>
```

Language: match the owner's session language (Ukrainian headers above are the
default here; keep field names bilingual-safe). The two-line VERDICT is mandatory —
a verdict line without its caveat is a defect (Fable §6.1).
