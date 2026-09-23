from __future__ import annotations

import argparse

from aevum_cad.params import ROOT, load_params
from aevum_cad.row_coupon import (
    export_row_coupon,
    export_row_coupon_final_print_pieces,
    export_row_coupon_validation_tools,
    row_coupon_layout,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "params",
        nargs="?",
        default=ROOT / "cad" / "one_row_coupon.params.json",
        help="Path to a one-row coupon params JSON file.",
    )
    args = parser.parse_args()

    params = load_params(args.params)
    paths = export_row_coupon(params, ROOT / "outputs" / "cad")
    final_piece_paths = export_row_coupon_final_print_pieces(
        params,
        ROOT / "outputs" / "cad" / "final_print_pieces",
    )
    validation_paths = export_row_coupon_validation_tools(params, ROOT / "outputs" / "cad")
    layout = row_coupon_layout(params)
    print(
        "layout: "
        f"x={layout['length_x']:.2f} y={layout['width_y']:.2f} "
        f"stack_z={layout['assembly_top_z']:.2f} "
        f"deck_to_top_z={layout['assembly_envelope_z']:.2f} mm"
    )
    for kind, path in paths.items():
        print(f"{kind}: {path}")
    for kind, path in final_piece_paths.items():
        print(f"final_piece_{kind}: {path}")
    for kind, path in validation_paths.items():
        print(f"validation_{kind}: {path}")


if __name__ == "__main__":
    main()
