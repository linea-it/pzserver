"""Tests for release HATS configuration customization."""

from copy import deepcopy

import pytest

from pzserver.hats_config import customize_hats_config


@pytest.fixture
def hats_template():
    return {
        "input": {
            "user_selected_cols": [
                "u_<FLUX>Flux",
                "u_<FLUX>FluxErr",
            ]
        },
        "photometry": {
            "measurements": [
                {
                    "name": "<FLUX>",
                    "input": {
                        "type": "flux",
                        "value_pattern": "BAND_<FLUX>Flux",
                        "error_pattern": "BAND_<FLUX>FluxErr",
                    },
                    "output": {
                        "type": "<MAG_OR_FLUX>_dered",
                        "value_pattern": (
                            "BAND_<FLUX><MAG_OR_FLUX>_<DEREDDENING>"
                        ),
                        "error_pattern": (
                            "BAND_<FLUX><MAG_OR_FLUX>Err_<DEREDDENING>"
                        ),
                    },
                }
            ],
            "invalid_handling": {"old": True},
        },
        "dust": {"use_dustmap": None},
    }


@pytest.mark.parametrize(
    (
        "convert_flux_to_mag",
        "dereddening",
        "output_type",
        "value_pattern",
        "error_pattern",
        "replacement",
    ),
    [
        (False, "none", "flux", "BAND_cModelFlux", "BAND_cModelFluxErr", None),
        (
            False,
            "sfd",
            "flux_dered",
            "BAND_cModelFlux_sfd",
            "BAND_cModelFluxErr_sfd",
            None,
        ),
        (True, "none", "mag", "BAND_cModelMag", "BAND_cModelMagErr", 99.0),
        (
            True,
            "sfd",
            "mag_dered",
            "BAND_cModelMag_sfd",
            "BAND_cModelMagErr_sfd",
            99.0,
        ),
    ],
)
def test_customize_hats_config_matches_tsm_photometry_modes(
    hats_template,
    convert_flux_to_mag,
    dereddening,
    output_type,
    value_pattern,
    error_pattern,
    replacement,
):
    original = deepcopy(hats_template)

    config = customize_hats_config(
        hats_template,
        flux="cModel",
        dereddening=dereddening,
        convert_flux_to_mag=convert_flux_to_mag,
    )

    assert hats_template == original
    assert config["input"]["user_selected_cols"] == [
        "u_cModelFlux",
        "u_cModelFluxErr",
    ]
    measurement = config["photometry"]["measurements"][0]
    assert measurement["name"] == "cModel"
    assert measurement["input"] == {
        "type": "flux",
        "value_pattern": "BAND_cModelFlux",
        "error_pattern": "BAND_cModelFluxErr",
    }
    assert measurement["output"] == {
        "type": output_type,
        "value_pattern": value_pattern,
        "error_pattern": error_pattern,
    }
    assert config["dust"]["use_dustmap"] == (
        dereddening if dereddening != "none" else None
    )

    invalid_handling = config["photometry"]["invalid_handling"]
    for channel in ("value", "error"):
        assert invalid_handling[channel]["replacement"] == {
            "value": replacement,
            "when": "invalid",
        }
        if convert_flux_to_mag:
            assert invalid_handling[channel]["limit"] == {
                "value": 99.0,
                "comparison": "greater_or_equal",
                "use_absolute": True,
            }
        else:
            assert "limit" not in invalid_handling[channel]


def test_customize_hats_config_validates_required_values(hats_template):
    with pytest.raises(ValueError, match="must be an object"):
        customize_hats_config([], flux="cModel", dereddening="none")

    with pytest.raises(ValueError, match="flux type is required"):
        customize_hats_config(hats_template, flux="", dereddening="none")

    with pytest.raises(ValueError, match="must be a boolean"):
        customize_hats_config(
            hats_template,
            flux="cModel",
            dereddening="none",
            convert_flux_to_mag="yes",
        )
