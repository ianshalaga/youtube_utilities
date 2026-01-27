from typing import Dict


COUNTRY_NAME_TO_ISO: Dict[str, str] = {
    "argentina": "AR",
    "chile": "CL",
    "uruguay": "UY",
    "brasil": "BR",
}

ISO_TO_COUNTRY_NAME: Dict[str, str] = {
    iso_code: name.title()
    for name, iso_code in COUNTRY_NAME_TO_ISO.items()
}


def normalize_country_name(name: str) -> str:
    """
    Normaliza el nombre del país para lookup.
    """
    return name.strip().lower()


def country_name_to_iso(name: str) -> str:
    """
    Dado un nombre de país devuelve el código ISO.

    Ej:
        "Argentina" -> "AR"
        "brasil"    -> "BR"
    """
    if not name:
        raise ValueError("Nombre de país vacío o nulo")

    key = normalize_country_name(name)

    if key not in COUNTRY_NAME_TO_ISO:
        raise ValueError(f"País desconocido: {name}")

    return COUNTRY_NAME_TO_ISO[key]


def iso_to_country_name(iso_code: str) -> str:
    """
    Dado un código ISO devuelve el nombre canónico del país.

    Ej:
        "AR" -> "Argentina"
        "BR" -> "Brazil"
    """
    if not iso_code:
        raise ValueError("Código ISO vacío o nulo")

    key = iso_code.strip().upper()

    if key not in ISO_TO_COUNTRY_NAME:
        raise ValueError(f"Código ISO desconocido: {iso_code}")

    return ISO_TO_COUNTRY_NAME[key]
