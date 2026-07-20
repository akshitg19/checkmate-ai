# Judge MVP scope

The `/check` API keeps the field name `latex` for backward compatibility, but
the current judge expects plain-text math, not LaTeX. Examples include
`3(x - 4) = 2x + 5`, `x = 17`, and `7 + 5`.

## Supported input

- One-variable linear equations with rational coefficients
- Rational-number arithmetic without variables
- Equivalent rearrangements that preserve the equation's solution set

## Outside the MVP

The judge reports these inputs as `unsupported` rather than trying to grade
them:

- Equations with more than one variable
- Exponents and nonlinear expressions such as `x^2 = 4` or `x(x + 1) = 2`
- Scientific notation such as `1e6`
- Variables in denominators, such as `1/x = 2`
- Functions, inequalities, systems of equations, and other advanced notation

Malformed text that cannot be parsed is reported separately as `parse_error`.

## Verdict status meanings

- `valid`: the step is mathematically equivalent to the previous valid line.
- `invalid`: the judge supports and understands the step, but it contains a
  mathematical mistake. Only this status can set `first_wrong_line`.
- `unsupported`: the input is understandable enough to identify it as outside
  the current product scope.
- `parse_error`: the input is malformed or could not be read as math.

`unsupported` and `parse_error` are capability/input-quality outcomes, not
evidence that the student made a mathematical mistake. If the problem itself
has either status, `/check` returns it in `problem_error` and leaves `verdicts`
empty.
