# Contributing

The useful contributions here are usually **new checks**, not new features.

## What counts as a check

A check belongs in this package if it satisfies all four:

1. **It can be run before you believe a result**, not after a reviewer asks.
2. **It names a specific way of being wrong.** "Improves quality" is not a
   failure mode; "the metric can be moved by adding voxels anywhere" is.
3. **It comes with a case where it fires and a case where it does not.** Both go
   in `tests/`. A check that never passes is as useless as one that never fails.
4. **It reports a number, not a verdict.** Return the quantity and let the caller
   decide the threshold; `stable` and `beats_random` are conveniences on top of
   numbers that are always returned.

## What a check should not do

* Depend on a particular loss, architecture or dataset.
* Require ground truth that a normal evaluation would not already have.
* Silently pick a convention. If a result depends on connectivity, tolerance or
  class balance, that parameter is an argument with the convention documented.

## Practicalities

```bash
git clone https://github.com/GuoCheng24/topocheck
cd topocheck
pip install -e ".[dev]"
pytest -q
```

Please keep dependencies to numpy / scipy / scikit-image. If a check needs more
than that, it probably belongs in its own package with this one as a dependency.

If you have data where one of these checks behaves differently from what the
README reports — especially a domain where the repairable share is high and a
repair method beats the random baseline at matched false-merge cost — that is the
most valuable thing you could send. Open an issue with the numbers.
