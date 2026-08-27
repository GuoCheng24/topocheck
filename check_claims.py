#!/usr/bin/env python3
"""Check that every number in the README is either reproduced or sourced.

    python check_claims.py              # everything
    python check_claims.py --runtime    # only what CI can re-run anywhere

A README that quotes numbers puts the reader in the position of having to trust
them.  This makes that checkable.  The claims split in two, and the split is the
point:

RUNTIME
    quoted from code that ships with this repository.  The checker re-runs that
    code and matches the output.  These must hold on any machine; CI checks them
    on every push, which is what the badge means.

SOURCED
    measured in segmentation experiments that are *not* shipped here.  Nothing
    in this repository can re-derive them, so the checker asserts the weaker but
    still meaningful property that each one appears in docs/EVIDENCE.md next to
    the dataset, model and protocol that produced it.  A number that drifts into
    the README without provenance fails here.

Exit code 0 if every claim passes, 1 otherwise.
"""
from __future__ import annotations

import os
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent
README = (ROOT / "README.md").read_text()
EVIDENCE = (ROOT / "docs" / "EVIDENCE.md").read_text()

# Each claim states where it must appear in the README and, for runtime claims,
# what must appear in the output of the code that ships here.  Keeping the two
# patterns separate is deliberate: the README and the program are allowed to
# word the same fact differently, and a checker that conflates them is fragile.
#
#   (kind, description, README pattern, output key, output pattern)
CLAIMS: list[tuple[str, str, str, str, str]] = [
    # ---- reproduced by code that ships here -------------------------------
    ("runtime", "quickstart: 7 branches",
     r"decomposes into 7 branches", "quickstart", r"decomposes into 7 branches"),
    ("runtime", "quickstart: break 0.286 split",
     r"break 0\.286 = missing 0\.143", "quickstart", r"break 0\.286 = missing 0\.143"),
    ("runtime", "quickstart: at most 50% removable",
     r"at most 50% of the breaks", "quickstart", r"at most 50% of the breaks"),
    ("runtime", "quickstart: 36 voxels added",
     r"added 36 voxels", "quickstart", r"added 36 voxels"),
    ("runtime", "quickstart: useless repair refused",
     r"beats random: False", "quickstart", r"beats random: False"),
    ("runtime", "demo: random tops the break ranking at every level",
     r"the strategy that scores \*\*best\*\* on break rate is",
     "demo", r"cuts: random"),
    ("runtime", "demo: random fuses everything",
     r"fusing everything makes every pair of endpoints", "demo", r"false merge rate 1\.00"),
    ("runtime", "coverage is 99%",
     r"[Tt]ests cover 99% of the package", "coverage", r"coverage 99%"),
    ("runtime", "CI floor is 95%",
     r"enforces a 95% floor", "workflow", r"--cov-fail-under=95"),
    # ---- measured elsewhere, must be sourced in docs/EVIDENCE.md ----------
    ("sourced", "random baseline 25.9%",            r"\b25\.9%",            "25.9", ""),
    ("sourced", "best learned repair 20.6%",        r"\b20\.6%",            "20.6", ""),
    ("sourced", "connect-to-largest 27.4%",         r"\b27\.4%",            "27.4", ""),
    ("sourced", "false merges 10-20x",              r"10-20x",                "20x", ""),
    ("sourced", "HRF repairable 3.3%",              r"\b3\.3%",             "3.3", ""),
    ("sourced", "TopCoW repairable 27.7%",          r"\b27\.7%",            "27.7", ""),
    ("sourced", "HRF repairable range 1.8-3.3%",    r"1\.8[\u2013-]3\.3%",   "1.8", ""),
    ("sourced", "oracle realised 27.36%",           r"\b27\.36%",           "27.36", ""),
    ("sourced", "per-case Spearman 1.000",          r"\b1\.000\b",          "1.000", ""),
    ("sourced", "HRF undetected 96.7 to 94.6",      r"96\.7% to 94\.6%",     "96.7", ""),
    ("sourced", "TopCoW undetected 72.3 to 48.2",   r"72\.3% to 48\.2%",     "72.3", ""),
    ("sourced", "TopCoW break 0.146 to 0.095",      r"0\.146 to 0\.095",     "0.146", ""),
    ("sourced", "tolerance cut 34.6%",              r"-34\.6%",              "34.6", ""),
    ("sourced", "HRF stable 93.8-98.2%",            r"93\.8[\u2013-]98\.2%", "93.8", ""),
    ("sourced", "STARE floor 0.204",                r"\b0\.204\b",          "0.204", ""),
    ("sourced", "STARE floor 0.564",                r"\b0\.564\b",          "0.564", ""),
    ("sourced", "99.4% of disagreement undetected", r"\b99\.4%",            "99.4", ""),
    ("sourced", "model break 0.214",                r"\b0\.214\b",          "0.214", ""),
    ("sourced", "second human 0.206",               r"\b0\.206\b",          "0.206", ""),
    ("sourced", "model Dice 0.775 vs 0.740",        r"0\.775 vs 0\.740",     "0.775", ""),
    ("sourced", "model clDice 0.845 vs 0.715",      r"0\.845 vs 0\.715",     "0.845", ""),
    ("sourced", "gap to second human 0.008",        r"\b0\.008\b",          "0.008", ""),
    ("sourced", "image-feature AUC 0.971",          r"\b0\.971\b",          "0.971", ""),
    ("sourced", "shuffled control 0.505",           r"\b0\.505\b",          "0.505", ""),
    ("sourced", "12.2x false structure",            r"\b12\.2x",            "12.2", ""),
    ("sourced", "for a 15.6% break reduction",      r"15\.6%",               "15.6", ""),
    ("sourced", "network probability 13.1% at 6.7x",
     r"13\.1% break reduction .*?6\.7x", "13.1", ""),
    ("sourced", "8.4-fold repairable difference",   r"8\.4-fold",            "8.4", ""),
    ("sourced", "random 1.5 points behind",         r"1\.5 points behind",    "1.5 points", ""),
]


def _run(*args: str) -> str:
    # The coverage run below executes the test suite, which contains a test that
    # calls this script.  Without this flag the two call each other forever;
    # tests/test_claims.py skips itself when it sees it.
    env = {**os.environ, "TOPOCHECK_IN_CLAIMS": "1"}
    r = subprocess.run([sys.executable, *args], cwd=ROOT, capture_output=True,
                       text=True, env=env)
    return r.stdout + r.stderr


def _outputs(need_runtime: bool) -> dict[str, str]:
    if not need_runtime:
        return {}
    out = {"quickstart": _run("examples/quickstart.py"),
           "demo": _run("examples/why_random_wins.py")}
    cov = _run("-m", "pytest", "-q", "--cov=topocheck", "--cov-report=term")
    m = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", cov)
    out["coverage"] = f"coverage {m.group(1)}%" if m else cov
    out["workflow"] = (ROOT / ".github" / "workflows" / "test.yml").read_text()
    return out


# Numbers in the README that are not empirical claims about results.  Structural
# ones are matched by pattern; anything else has to be listed individually with a
# reason, so that exempting a number is a visible act rather than a quiet one.
STRUCTURAL = re.compile(
    r"""^(?:
        0\.1\.0                    # this package's version
      | 3\.9|3\.11|3\.12          # python versions
      | 2003\.07311|2404\.03010|2501\.01022|2411\.03228|2412\.14619   # arXiv ids
      | (?:19|20)\d\d              # years
      | [0-9]{1,3}                   # bare integers: counts, sizes, tolerances, panel numbers
      )$""",
    re.X,
)
EXEMPT = {
    "1.0": "the arithmetic value a precision cannot honestly take on a finite sample",
    "30%": "a rhetorical example of a hypothetical improvement, not a measurement",
}


def uncovered_numbers() -> list[str]:
    """Every number in the README prose must be covered by a claim.

    Without this, "N/N verified" only says that the claims we happened to write
    down still hold; a number added later, with no provenance, would pass
    silently.  Listing what is *not* checked is the other half of the report.
    """
    body = re.sub(r"```.*?```", "", README, flags=re.S)          # code blocks
    body = re.sub(r"\[!\[.*?\]\(.*?\)", "", body)               # badges
    body = re.sub(r"\]\(.*?\)", "]", body)                       # link targets
    found = set(re.findall(r"\d+(?:\.\d+)?(?:%|x|-fold)?", body))
    covered = set()
    for _, _, readme_pat, _, _ in CLAIMS:
        for m in re.finditer(readme_pat, README, re.S):
            covered.update(re.findall(r"\d+(?:\.\d+)?(?:%|x|-fold)?", m.group(0)))
    return sorted(n for n in found - covered
                  if not STRUCTURAL.match(n) and n not in EXEMPT)


def main(argv: list[str]) -> int:
    runtime_only = "--runtime" in argv
    claims = [c for c in CLAIMS if c[0] == "runtime"] if runtime_only else CLAIMS
    outs = _outputs(any(c[0] == "runtime" for c in claims))
    failed = []
    for kind, desc, readme_pat, key, out_pat in claims:
        if not re.search(readme_pat, README, re.S):
            failed.append((desc, "not found in README"))
            continue
        if kind == "runtime":
            if not re.search(out_pat, outs[key], re.S):
                failed.append((desc, f"README states it, but the {key} output does not"))
        elif key not in EVIDENCE:
            failed.append((desc, f"quoted in README, {key!r} absent from docs/EVIDENCE.md"))
    n = len(claims)
    if not runtime_only:
        loose = uncovered_numbers()
        for x in loose:
            failed.append((f"unclaimed number {x!r} in the README",
                           "no CLAIMS entry covers it, so nothing checks its provenance"))
    for desc, why in failed:
        print(f"FAIL  {desc}: {why}")
    print(f"\n{n - len(failed)}/{n} claims verified"
          f"{' (runtime only)' if runtime_only else ''}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
