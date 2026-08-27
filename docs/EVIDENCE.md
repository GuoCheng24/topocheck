# Where the numbers in the README come from

The checks in this package are domain-agnostic and reproducible from the
repository. The **numbers** quoted in the README are not: they come from
segmentation experiments that are not shipped here, on public datasets. This
document states exactly how each one was produced so that it can be audited, and
is explicit about what a reader cannot verify from this repository alone.

What *is* reproducible here: `examples/why_random_wins.py` reproduces the
*phenomenon* behind the headline claim from scratch on synthetic data, in about a
minute, with no downloads. If you only check one thing, check that.

## Common setup

| | |
|---|---|
| Segmenter | plain U-Net (MONAI, 5 levels, 2 residual units per level), trained from scratch per dataset |
| Losses compared | Dice+CE baseline, clDice, Skeleton Recall, supervoxel loss, tubular loss, and unit-level objectives of our own |
| Operating point | threshold 0.5 unless a threshold sweep is stated |
| Connectivity | 8-neighbour in 2-D, 26-neighbour in 3-D, foreground |
| Units | open branches of the ground-truth skeleton, junctions removed, minimum 5 voxels — the same decomposition `topocheck.build_units` implements |
| Break | a unit is broken when its two endpoints are not in the same predicted component |

## Claim by claim

### "a random assignment reduced the break rate by 25.9%"

TopCoW, 50 held-out volumes, strict endpoint criterion, single baseline U-Net.
Fragments (predicted components other than the largest, at least 10 voxels) were
each linked to another component along a minimum-cost path through `1 - p`.
Strategies compared, all at unlimited link cost:

| strategy | break reduction | false merges vs baseline |
|---|---|---|
| shuffled-label control | 0.0% | 1x |
| cheapest-partner rule | 16.5% | 17x |
| learned pairwise selector | 20.6% | 10x |
| **random assignment** | **25.9%** | 18x |
| connect all to largest component | 27.4% | 20x |

Random therefore lands **1.5 points** behind the crude connect-to-largest rule
(25.87% against 27.36% before rounding) and ahead of every learned strategy.

The learned selector was trained on three external centres (ISLES, Lausanne, IXI)
and applied to the held-out 50, so it never saw the test cases. The false merge
column is the fraction of ground-truth component pairs fused, relative to the
unrepaired baseline; it is defined on the 20 of 50 cases that have at least two
ground-truth components above 50 voxels.

### "3.3% on HRF against 27.7% on TopCoW"

Fragmented share of all connectivity errors at the strict criterion, baseline
U-Net. HRF: 1.8-3.3% across four training objectives (Dice+CE, unit-level mean,
unit-level CVaR, Skeleton Recall). TopCoW: 20.7-28.0% across the same four.
The figure quotes the Dice+CE baseline in each case: 3.3% against 27.7%, a ratio
of **8.4**.

### "an oracle repair captured 27.36% against a predicted budget of 27.4%"

Same 50 TopCoW volumes. The budget is `fragment / break` measured before any
repair; the realised gain is from linking every fragment to the largest
component at unlimited cost. Per case, Spearman correlation between a case's own
budget and its own realised gain was 1.000 (p = 5e-77, n = 50) and no case
exceeded its budget.

### "96.7% to 94.6%" and "72.3% to 48.2%"

Undetected share of connectivity errors as the endpoint tolerance goes from 0 to
2 voxels, baseline U-Net. HRF stays within 93.8-98.2% over tolerances 0-3 on two
training objectives. TopCoW: 72.3, 63.3, 48.2, 41.6 at tolerances 0, 1, 2, 3,
with the break rate falling from 0.146 to 0.095, a relative reduction of
**34.6%** (0.1457 to 0.0953 before rounding).

### "0.204 in one direction and 0.564 in the other"

STARE, 20 fundus images, annotators `ah` and `vk`, no field-of-view mask. Taking
`ah` as reference and `vk` as prediction gives a break rate of 0.204 with 99.4%
of the disagreement being undetected structure; the reverse gives 0.564 with
99.5%. The asymmetry is because `vk` annotates more: 10.9% foreground against
7.6%, and 373 branch units per image against 176.

### "a U-Net lands 0.008 from the second human"

Same 20 STARE images, 4-fold cross-validation, trained against `ah` at native
resolution, evaluated with a field-of-view mask applied to both model and human
(hence 0.206 rather than 0.204 for the human). At threshold 0.05 the unit-level
objective reaches break 0.214, Dice 0.775, clDice 0.845, against the second
human's 0.206, 0.740, 0.715.

### "AUC 0.971 ... 12.2x false structure for a 15.6% break reduction"

TopCoW. Positives are ground-truth skeleton voxels of undetected units with
p < 0.5; negatives are background voxels with p < 0.5, matched on distance to the
nearest detected vessel. Features are local intensity statistics of the raw image
only, at radii 1, 2, 3, 5 and 8, with no network output among them; the
classifier is gradient boosting with case-disjoint folds. Balanced-sample AUC was
0.971 at radius 1, decreasing monotonically to 0.952 at radius 8; the
label-shuffled control was 0.505 and a distance-only feature 0.511.

Deployed at the real class ratio on the held-out 50, ranking all p < 0.5 voxels
by this classifier and adding the top fraction back: at 2% added the break rate
fell 15.6% with false structure at 12.2x baseline and Dice down 0.067. Ranking
the same voxels by the network's own probability did better at every point
(13.1% at 6.7x for 1% added).

## What you cannot check from this repository

* The trained segmenters, and therefore the exact numbers above.
* Dataset access. HRF, STARE and MSD Task08 are downloadable without
  registration; TopCoW requires a challenge registration.
* Whether these findings hold on a domain we did not try. That is the first item
  in "Where help is wanted" in the README, and it is a real question, not a
  rhetorical one.
