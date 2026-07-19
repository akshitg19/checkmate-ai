# Transcription failure log

Format: file | expected | actual | notes

## 2026-07-18 — first messy-handwriting batch

| file | expected | actual | notes |
|---|---|---|---|
| ambiguious.png | `x + 0\y + 0m + z - 7b = 17` | `x + εy + 0m + z - 7g = Π` | slashed-zero misread as ε; cursive `b` misread as `g`; `17` misread as `Π` |
| big.png | `7x + 11m + 155b` | `1*Oct + 155*b` | `7x` + `11m` almost entirely misread; `155b` correct |
| blank.png | (blank) | `UNREADABLE` | correct — fallback works |
| cramped.png | `3m + 4n = 2241774nz` | `3m + 4n = 22177402` | left side correct; cramped trailing digits/letters scrambled, letters read as digits |
| cursive.png | `1z + 2b + 4l = nbmq` | `\|g + 2g + 4l = ηb + mng` | `4l` correct; rest wrong — cursive `1`/`z` read as `\|g`, `b` read as `g` (same g/b confusion as #1), right side mostly fabricated |
| diagonal.png | `x + 4z = 24m` | `$\chi + 4z = 2m + m$` | `x` misread as `χ`; `24m` split into `2m + m`; stray `$` LaTeX wrapping |
| messy.png | `x + y = 4z + 2` | `x + y - 4z + 2` | `=` misread as `-` — ruled notebook line overlapping the equals sign |
| scribbled.png | `4x + mnz = 13d` (scribbled part correctly ignored) | `4x + mz + 22 <= 13d` | cross-out correctly disregarded; dropped `n` from `mnz`; `=` misread as `<=`, likely same ruled-line issue as messy.png |
| small.png | (mostly wrong per author) | `l*y*s * ∂g = 4*m + h_2 + 8*n` | small text size — largely unusable |
| test_line.png | `3x - 12 = 2x + 5` | `$3x - 12 = 2x + 5$` | content correct; same image transcribed clean (no `$`) on an earlier run — non-deterministic formatting |

## 2026-07-19 — live app usage (via new Finish Line export)

| written | transcribed | notes |
|---|---|---|
| `x = 2` | `x = a` | digit `2` misread as letter `a` |

### Patterns identified
1. **Ruled-line confusion**: printed horizontal ruling near a handwritten `=` gets read as `-` or `<=` (messy.png, scribbled.png — 2/10 samples, both equals signs).
2. **g/b cursive confusion**: recurring in ambiguious.png and cursive.png.
3. **Greek-letter bias**: model defaults to ε/Π/η/χ/∂ on ambiguous glyphs instead of the plain latin/digit vocabulary that's actually in scope for algebra.
4. **Non-deterministic LaTeX wrapping**: identical image (test_line.png) transcribed with and without `$...$` across runs — no temperature/seed set.
5. **Degrades sharply** on: cramped spacing, small text, dense multi-symbol lines (big.png, small.png).
