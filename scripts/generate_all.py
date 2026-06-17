from __future__ import annotations

import argparse

from aevum_cad.fixture_model import export_fixture
from aevum_cad.labware import export_labware
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
    cad_paths = export_fixture(params, ROOT / "outputs" / "cad")
    labware_path = export_labware(params, ROOT / "outputs" / "labware")

    print("generated:")
    for kind, path in cad_paths.items():
        print(f"  {kind}: {path}")
    print(f"  labware: {labware_path}")


if __name__ == "__main__":
    main()
