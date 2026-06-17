from __future__ import annotations

import argparse

from aevum_cad.fixture_model import export_fixture
from aevum_cad.params import ROOT, load_params


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "params",
        nargs="?",
        default=ROOT / "cad" / "p300_poc_fixture.params.json",
        help="Path to a fixture params JSON file.",
    )
    args = parser.parse_args()

    params = load_params(args.params)
    paths = export_fixture(params, ROOT / "outputs" / "cad")
    for kind, path in paths.items():
        print(f"{kind}: {path}")


if __name__ == "__main__":
    main()
