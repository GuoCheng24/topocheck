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
endpoints become co-connected. On TopCoW (3-D cerebrovascular, 50 held-out
cases), a **random** assignment of fragments to components reduced the break rate
by **25.9%** — beating every learned repair we had built (best: 20.6%) and
landing within a point of the crude "connect every fragment to the largest
component" rule (**27.4%**). Both blew up false merges by 17–20x, which is the
only reason the difference is visible at all.

A method that does not clearly beat a random repair *of the same size*, at
matched false-merge cost, has not been shown to repair anything. Report both.

### 2. `decompose_errors` — how much of the error is even repairable?

Split connectivity failures into

* **missing** — an endpoint is in no predicted component at all: the structure
  was never detected, and no decoder can recover it;
* **fragment** — both endpoints detected but in different components: this is
  the part a repair could fix.

`fragment / break` is then a hard upper bound on any repair method, and in our
data it was **not** a loose bound: on the 50 TopCoW held-out volumes an oracle
repair captured **27.36%** against a predicted budget of **27.4%**, with a
per-case Spearman correlation of **1.000** between a case's budget and its
realised gain, and **0/50** cases exceeding their own budget.

Measure this before building the method. On HRF (2-D retinal fundus) the
repairable share was only **1.8–3.3%** across four training objectives, which
caps that entire family of methods at a few percent no matter how clever the
decoder is.

### 3. `tolerance_sweep` — does the conclusion survive the metric's conventions?

Requiring the exact ground-truth endpoint voxel to lie inside a predicted
component is one convention among several. Relaxing it to "within 2 voxels"
changed TopCoW from *72.3% of errors are undetected structure* to *48.2%*, and
cut the break rate from 0.146 to 0.095 (**-34.6%**) — while the same relaxation
moved HRF almost not at all (undetected share stayed within **93.8–98.2%** over
tolerances 0–3, on two different training objectives).

If your error composition moves under the sweep, the metric cannot on its own
carry a claim about *why* the errors happen. Report the sweep, not one setting.

### 4. `annotation_floor` — is the improvement inside human disagreement?

Evaluate the metric between two independent annotations of the same images. On
STARE (20 retinal fundus images, two expert annotators) the break rate between
them was **0.204** in one direction and **0.564** in the other, and **99.4%** of
that disagreement was *structure one annotator drew and the other did not* — not
fragmentation.

A U-Net cross-validated on the same 20 images against annotator `ah` reached a
break rate of **0.214** where the second human scored **0.206**, while scoring
higher on both Dice (0.775 vs 0.740) and clDice (0.845 vs 0.715). A model can fit
one annotator's inclusion convention about as well as another expert does, which
is worth knowing before reading a 30% improvement as 30% better topology.
(Model-vs-human numbers are field-of-view masked, hence 0.206 rather than 0.204.)

The direction matters: a more inclusive annotator scores very differently as
reference than as prediction. Both are reported.

### 5. `prevalence_check` — does a balanced-sample AUC survive deployment?

Discriminative power measured on a 1:1 sample says little when positives are
rare. On TopCoW, a classifier separating missed-vessel voxels from background
using only local image statistics reached **AUC 0.971** on balanced samples
(label-shuffled control: 0.505). Deployed at the real class ratio it needed a
**12.2x** increase in false structure to buy a 15.6% break reduction, and was
beaten at every operating point by simply ranking the same voxels by the
segmentation network's own probability (13.1% break reduction at 6.7x).

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
* The checks are domain-agnostic; the numbers are not. Every figure quoted above
  comes from public datasets, with a plain U-Net and standard topology-aware
  losses (clDice, Skeleton Recall, supervoxel loss, tubular loss):
  **HRF** (2-D retinal fundus, 45 images), **STARE** (2-D retinal fundus, 20
  images, two annotators), **TopCoW** (3-D cerebrovascular, held-out 50 plus
  external centres from ISLES, Lausanne and IXI) and **MSD Task08 Hepatic
  Vessel** (3-D). No private or patient-identifiable data is involved.

## License

MIT
