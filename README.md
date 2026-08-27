# topocheck

Sanity checks for claims about **topology-aware segmentation** — the losses,
decoders and repair methods that promise fewer broken vessels, airways, neurons
or roads.

Connectivity metrics are unusually easy to move for the wrong reasons. Each check
here exists because it caught a result that looked publishable and was not.

```bash
pip install topocheck
```

```python
import topocheck as tc

units = tc.build_units(gt)                    # GT branch decomposition, 2-D or 3-D
tc.decompose_errors(pred, units)              # how much of the error is even repairable?
tc.random_repair_baseline(pred, repaired, units)   # does your repair beat a random one?
tc.tolerance_sweep(pred, units)               # does the conclusion survive the conventions?
tc.annotation_floor(gt_observer1, gt_observer2)    # is the gain inside human disagreement?
tc.prevalence_check(y, scores, prevalence=1e-3)    # does a balanced AUC survive deployment?
```

## The five checks, and why each one exists

### 1. `random_repair_baseline` — does your repair beat a random one?

Connectivity metrics reward *adding voxels*: link anything to anything and
endpoints become co-connected. On a 3-D cerebrovascular set, a **random**
assignment of fragments to components reduced the break rate by **25.9%**,
beating every learned repair we had built — and beating the "connect everything
to the trunk" rule that we had been treating as our strongest result.

A method that does not clearly beat a random repair *of the same size* has not
been shown to repair anything. Report both numbers.

### 2. `decompose_errors` — how much of the error is even repairable?

Split connectivity failures into

* **missing** — an endpoint is in no predicted component at all: the structure
  was never detected, and no decoder can recover it;
* **fragment** — both endpoints detected but in different components: this is
  the part a repair could fix.

`fragment / break` is then a hard upper bound on any repair method. In our data
it was **not** a loose bound: on 50 held-out volumes an oracle repair captured
27.36% against a predicted budget of 27.4%, with a per-case Spearman correlation
of 1.000 between predicted budget and realised gain, and **0/50** cases
exceeding their own budget.

Measure this before building the method. In 2-D retinal vessels the repairable
share was only **2–3%**, which caps that entire family of methods at a few
percent no matter how clever the decoder is.

### 3. `tolerance_sweep` — does the conclusion survive the metric's conventions?

Requiring the exact ground-truth endpoint voxel to lie inside a predicted
component is one convention among several. Relaxing it to "within 2 voxels"
changed a 3-D dataset from *72% of errors are undetected structure* to *48%*,
and cut the break rate by 35% — while the same relaxation moved a 2-D dataset by
almost nothing (94–97% stable).

If your error composition moves under the sweep, the metric cannot on its own
carry a claim about *why* the errors happen. Report the sweep, not one setting.

### 4. `annotation_floor` — is the improvement inside human disagreement?

Evaluate the metric between two independent annotations of the same images. On a
retinal set with two expert annotators the break rate between them was **0.204**
in one direction and **0.564** in the other, and **99.4%** of that disagreement
was *structure one annotator drew and the other did not* — not fragmentation. A
model trained on one annotator matched the second annotator's break rate while
scoring higher on Dice and clDice, which mostly says the benchmark measures
conformity to one annotator's inclusion convention.

The direction matters: a more inclusive annotator scores very differently as
reference than as prediction. Both are reported.

### 5. `prevalence_check` — does a balanced-sample AUC survive deployment?

Discriminative power measured on a 1:1 sample says little when positives are
rare. A classifier separating missed-vessel voxels from background at **AUC
0.97** on balanced samples, deployed at the real class ratio, needed a
false-structure increase of **12×** to buy a 15% break reduction — and was
outperformed by simply ranking the same voxels by the segmentation network's own
probability.

This check turns an AUC into the precision, and the false-positives-per-true,
that you would actually operate at. A zero false-positive count in a finite
sample is reported as a rule-of-three bound rather than a precision of 1.0.

## Scope and limitations

* Units are **open branches** of the GT skeleton: junctions are removed and only
  pieces with exactly two endpoints are kept. Under full connectivity, removing a
  junction also removes its immediate neighbours, so very short stubs do not
  survive; this is pinned by a test.
* Full connectivity (8-neighbour in 2-D, 26 in 3-D) is used throughout for the
  foreground, which avoids the foreground/background connectivity paradox for
  thin structures.
* `random_repair_baseline` matches the *number of voxels added*, which is a
  proxy for "amount of intervention". It is deliberately crude: its purpose is to
  establish a floor, not to be a competitive method.
* The evidence quoted above comes from retinal vessel (2-D) and cerebrovascular
  and hepatic vessel (3-D) segmentation. The checks are domain-agnostic; the
  numbers are not.

## License

MIT
