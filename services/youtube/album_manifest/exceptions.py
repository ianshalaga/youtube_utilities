class ManifestError(Exception):
    """Base exception for manifest loading errors."""


class ManifestParseError(ManifestError):
    """Raised when the YAML cannot be parsed."""


class ManifestConfigurationError(ManifestError):
    """Raised when the manifest structure is invalid."""