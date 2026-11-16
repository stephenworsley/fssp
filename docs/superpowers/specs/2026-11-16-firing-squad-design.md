# Firing Squad Synchronisation Simulator — Short Design

## Intent
A fun, prototype-quality Python program to simulate 1D cellular automata solving the
firing squad synchronisation problem, render the run as an image, and report whether
it solved the problem.

- **Goal:** demonstrate that a rule set works (or doesn't) for a chosen n.
- **Non-goals:** proving a rule set works for all n; polished visuals.
- **Anti-goal:** reporting success for a broken rule set.

## Approaches
- **Chosen:** a single Python script with rule tables as plain dicts and a matplotlib image.
  This is the simplest way to see whether a rule set works.
- Not chosen: an interactive or animated viewer, which is too much for a prototype.
  A "check n = 2..N" mode was also left out, because demonstrating a single n is enough.
- Missing-rule handling options considered:
  - Stop with an error. This gives a precise diagnosis but no picture.
  - Treat it as "stay the same". This hides copying mistakes.
  - **Chosen: fire.** Combined with the safeguards below, this always produces a picture
    and still can't report a false success.

## Behaviour (decided with user)
- **States:** short strings. Each rule set declares its general (G), quiescent (Q),
  and fire (F) state names.
- **Rules:** dict mapping `(left, self, right) -> new_state`.
- **Boundary:** a distinct marker `#` beyond each end. It is never updated and only
  appears as a neighbour in rule keys. It is separate from the real quiescent state.
- **Built-in rules,** inherited by every rule set unless it overrides them:
  `(Q, Q, Q) -> Q` and `(Q, Q, #) -> Q`.
- **Initial configuration:** the leftmost cell is the general and all others are quiescent.
- **Missing rule:** the cell goes to the fire state, and the pattern, cell index,
  and time step are recorded.
- **Stopping:** the run stops at the first step where *any* cell is in the fire state,
  or when the time limit is reached.
- **Verdict:** the run is a **success** only if all of the following hold:
  - every cell fires on the same step,
  - every firing comes from a real rule rather than a missing one,
  - the firing time is at least 2n − 2, the proven minimum.

  Otherwise it is a **failure**, with the reasons reported:
  - which cells fired prematurely,
  - any missing-rule patterns, with cell and step,
  - a "faster than possible" firing time,
  - a timeout.

## Configuration
- Number of cells `n`.
- Rule set: a named preset or a user-defined dict.
- Time limit: optional. *My call:* the default is `3n + 10`, which leaves room for
  rule sets slower than the optimal 2n − 2.
- *My call:* a small argparse CLI with `--cells`, `--preset`, `--max-steps`,
  `--matplotlib` (decided with user), and `--output`.

## Output
- **Intermediate result (decided with user):** the simulation produces a 2D integer
  array of shape `(time_steps, n)`. Each entry is a state index, together with the
  ordered list of state names that maps indices back to names. The simulation does no
  drawing itself. This keeps visualisation decoupled, so that new renderers can be added
  later without touching the simulation.
- *My call:* the simulation returns a single result object containing the array, the
  state names, the verdict, and the missing-rule records (cell, step, pattern). A
  renderer could then highlight cells that fired because of a missing rule. The array
  excludes the `#` boundary cells.
- **Renderers (decided with user):** two to start, each a separate function that takes
  the integer array and the state names.
  - **Terminal text (default):** prints the run to the terminal, one line per time step
    with t = 0 at the top, using ANSI colour escape codes (e.g. `\033[31m...\033[0m`).
    - *My call:* each cell is drawn as its state's short symbol, coloured per state.
    - *My call:* a colour legend is printed above the grid.
    - *My call:* if n is wider than the terminal, lines simply wrap. That's acceptable
      for a prototype.
  - **matplotlib PNG:** enabled with `--matplotlib`. Cells run along x and time along y,
    with t = 0 at the top. Each state has its own colour, and a legend is included.
    - *My call:* `--output` sets the PNG path, defaulting to `firing_squad.png`. It only
      applies with `--matplotlib`.
- A console verdict giving success or failure, the reasons, the firing time, and how it
  compares with 2n − 2.

## Presets
*My call:*
- Include Mazoyer's 6-state minimal-time solution.
  - Source: the transition table in `hediet/lean-cellular-automata`
    (`CellularAutomatas/proofs/constructions/fssp_mazoyer/ca.lean`), which is ported from the
    Coq formal proof (`rocq-archive/firing-squad`, `autom.v`).
  - States are `A B C L G F`, with quiescent = `L`, general = `G`, and fire = `F`.
  - The boundary is handled as a phantom neighbour: `L` on the left and `G` on the right.
  - Verified in a scratch check: all cells fire at exactly 2n − 2 for n = 3..199. It fails
    at n = 2, which is expected.
- Add others, such as Balzer's 8-state or Waksman's 16-state solutions, only if a reliable
  transition table can be found.
- Check each preset by running it for several values of n. If a preset fails, treat it as
  a transcription error to fix rather than shipping it.

## Left to the builder
- Colour palette, figure sizing, and the n = 1 edge case.
- Whether matplotlib is imported lazily, so the default text mode works without it
  installed. A lazy import is preferred.
- How users supply custom rule sets, for example a Python module they edit.
