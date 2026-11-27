from pathlib import Path
from typing import Any, Mapping

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PARAMETERS_PATH = PROJECT_ROOT / "config" / "parametros.yaml"


def load_parameters(path: Path = DEFAULT_PARAMETERS_PATH) -> dict[str, Any]:
    """Load and validate the configuration values used by the MVP."""
    try:
        with path.open(encoding="utf-8") as parameter_file:
            parameters = yaml.safe_load(parameter_file)
    except yaml.YAMLError as error:
        raise ValueError(f"Invalid YAML in {path}: {error}") from error

    if not isinstance(parameters, dict):
        raise ValueError(f"Expected a YAML mapping in {path}.")

    comparable_rules = _mapping(parameters, "comparables")
    _number(comparable_rules, "tolerancia_area", minimum=0)
    price_range = comparable_rules.get("rango_precio_m2_valido")
    if (
        not isinstance(price_range, list)
        or len(price_range) != 2
        or not all(_is_number(value) for value in price_range)
        or price_range[0] <= 0
        or price_range[0] > price_range[1]
    ):
        raise ValueError(
            "comparables.rango_precio_m2_valido must contain two positive "
            "numbers in ascending order."
        )

    confidence_rules = _mapping(parameters, "confianza")
    for level in ("alta", "media"):
        level_rules = _mapping(confidence_rules, level)
        _number(level_rules, "min_comparables", minimum=1, integer=True)
        _number(level_rules, "max_coef_variacion", minimum=0)

    environment_rules = _mapping(parameters, "entorno")
    _number(environment_rules, "radio_busqueda_m", minimum=0, exclusive=True)

    return parameters


def _mapping(parent: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = parent.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"Expected '{key}' to contain a mapping.")
    return value


def _number(
    values: Mapping[str, Any],
    key: str,
    minimum: float,
    *,
    integer: bool = False,
    exclusive: bool = False,
) -> float:
    value = values.get(key)
    if not _is_number(value) or (integer and not isinstance(value, int)):
        raise ValueError(f"Expected '{key}' to be a number.")
    if (exclusive and value <= minimum) or (not exclusive and value < minimum):
        operator = "greater than" if exclusive else "at least"
        raise ValueError(f"Expected '{key}' to be {operator} {minimum}.")
    return value


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)
