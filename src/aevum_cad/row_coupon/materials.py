"""Print material per printed part, and the reason it was chosen.

Two FDM materials, split by what each part has to survive
(docs/knowledge/materials_strategy.md:271-283 sets the bias):

- ASA for dry, load-bearing parts that set the plate datum. Its higher softening point
  (about 100 C against PETG's 80 C) means less creep at 37 C, and creep in these parts
  moves the coverslip and therefore focus.
- PETG for everything wetted, headspace-facing, wiped down with ethanol, or that flexes to
  snap or latch. PETG is a routine cell-culture plastic, tolerates ethanol and IPA, and has
  stronger layer bonding for snaps; ASA is styrenic and can stress-crack at a latch or
  under a solvent wipe.

Split pieces inherit their installed part's material, so both halves of a keyed joint
shrink alike. PEN is the upgrade path for the three headspace shells (wet chamber frame,
lid manifold shell, lid cover) once a filament source and a creep coupon exist.
"""

from __future__ import annotations

from typing import Any

MATERIALS: dict[str, dict[str, Any]] = {
    "ASA": {
        "label": "ASA",
        "zh": "ASA 线材",
        "softening_c": 100,
        "bambu_filament": {"h2s": "Generic ASA @BBL H2S 0.4 nozzle"},
    },
    "PETG": {
        "label": "PETG",
        "zh": "PETG 线材",
        "softening_c": 80,
        "bambu_filament": {"h2s": "Generic PETG @BBL H2S"},
    },
}

PART_MATERIALS: dict[str, tuple[str, str]] = {
    "deck_pods": (
        "ASA",
        "dry and load-bearing; sets the row height on the deck, so creep at 37 C matters",
    ),
    "plate_support_frame": (
        "ASA",
        "dry datum for the plate; creep here moves the coverslip and the focus",
    ),
    "wet_chamber_frame": (
        "PETG",
        "wet-side and headspace wall; wiped with ethanol (PEN upgrade path)",
    ),
    "lid_manifold_shell": ("PETG", "headspace shell carrying the gas path (PEN upgrade path)"),
    "lid_cover": ("PETG", "headspace lid, cleaned between runs (PEN upgrade path)"),
    "lower_harness_cover": (
        "PETG",
        "snaps onto its owner (service path harness_cover_install_and_release)",
    ),
    "lid_harness_cover": (
        "PETG",
        "snaps onto its owner (service path harness_cover_install_and_release)",
    ),
    "printed_lower_sensor_connector_shroud": ("PETG", "flexes on connector release"),
    "printed_lid_sensor_connector_shrouds": ("PETG", "flexes on connector release"),
    "printed_gas_pcb_keeper_doors": ("PETG", "keeper door that latches over the gas PCB"),
    "printed_sample_relief_cap": ("PETG", "wet seal cap on the lid boss, removed for service"),
    "printed_wedge_locks": ("PETG", "latching wedges; ASA's weaker layer bond cracks at a latch"),
}


def material_of(installed_part: str) -> str:
    try:
        return PART_MATERIALS[installed_part][0]
    except KeyError:
        raise KeyError(
            f"no print material for {installed_part!r}; add it to PART_MATERIALS in "
            "src/aevum_cad/row_coupon/materials.py"
        ) from None


def release_body_materials(registry: dict[str, Any]) -> dict[str, str]:
    """Rigid print piece -> material, through the registry's own chain
    (release body -> canonical source -> installed part)."""
    part_of_source = {
        s["source_artifact_id"]: s["installed_part"] for s in registry["canonical_sources"]
    }
    return {
        rb["release_body_id"]: material_of(part_of_source[rb["source_artifact_id"]])
        for rb in registry["release_bodies"]
        if rb["body_class"] == "rigid_print_piece"
    }
