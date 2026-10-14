"""Build effective HATS configurations for Training Set Maker submissions."""

from collections.abc import Mapping
from copy import deepcopy

PLACEHOLDERS = {
    "<FLUX>": "flux",
    "<MAG_OR_FLUX>": "mag_or_flux",
    "<DEREDDENING>": "dereddening",
}


def _replace_placeholders(value, replacements):
    if isinstance(value, str):
        result = value
        for placeholder, replacement_name in PLACEHOLDERS.items():
            result = result.replace(placeholder, replacements[replacement_name])
        return result

    if isinstance(value, list):
        return [_replace_placeholders(item, replacements) for item in value]

    if isinstance(value, Mapping):
        return {
            key: _replace_placeholders(child, replacements)
            for key, child in value.items()
        }

    return deepcopy(value)


def _create_invalid_handling(use_magnitude):
    replacement_value = 99.0 if use_magnitude else None

    def create_channel():
        channel = {"nonfinite_is_invalid": True}
        if use_magnitude:
            channel["limit"] = {
                "value": 99.0,
                "comparison": "greater_or_equal",
                "use_absolute": True,
            }
        channel["replacement"] = {
            "value": replacement_value,
            "when": "invalid",
        }
        return channel

    return {
        "value": create_channel(),
        "error": create_channel(),
    }


def customize_hats_config(
    template,
    *,
    flux,
    dereddening,
    convert_flux_to_mag=False,
):
    """Apply the basic TSM selections to a release HATS configuration."""
    if not isinstance(template, Mapping):
        raise ValueError("The release HATS configuration must be an object.")
    if not isinstance(convert_flux_to_mag, bool):
        raise ValueError("convert_flux_to_mag must be a boolean.")

    flux = str(flux or "")
    if not flux:
        raise ValueError("A flux type is required to build the HATS configuration.")

    dereddening = str(dereddening or "none")
    mag_or_flux = "Mag" if convert_flux_to_mag else "Flux"
    replacements = {
        "flux": flux,
        "dereddening": dereddening,
        "mag_or_flux": mag_or_flux,
    }
    config = _replace_placeholders(template, replacements)
    uses_dereddening = dereddening.casefold() != "none"
    output_type = (
        "mag" if convert_flux_to_mag else "flux"
    ) + ("_dered" if uses_dereddening else "")
    dereddening_suffix = f"_{dereddening}" if uses_dereddening else ""
    output_value_pattern = (
        f"BAND_{flux}{mag_or_flux}{dereddening_suffix}"
    )
    output_error_pattern = (
        f"BAND_{flux}{mag_or_flux}Err{dereddening_suffix}"
    )

    dust = config.get("dust")
    if isinstance(dust, Mapping):
        config["dust"] = {
            **dust,
            "use_dustmap": dereddening if uses_dereddening else None,
        }

    photometry = config.get("photometry")
    if isinstance(photometry, Mapping):
        measurements = photometry.get("measurements")
        if isinstance(measurements, list):
            customized_measurements = []
            for measurement in measurements:
                if not isinstance(measurement, Mapping):
                    customized_measurements.append(deepcopy(measurement))
                    continue

                output = measurement.get("output")
                output = dict(output) if isinstance(output, Mapping) else {}
                customized_measurements.append(
                    {
                        **measurement,
                        "output": {
                            **output,
                            "type": output_type,
                            "value_pattern": output_value_pattern,
                            "error_pattern": output_error_pattern,
                        },
                    }
                )
            measurements = customized_measurements

        config["photometry"] = {
            **photometry,
            "measurements": measurements,
            "invalid_handling": _create_invalid_handling(convert_flux_to_mag),
        }

    return config
