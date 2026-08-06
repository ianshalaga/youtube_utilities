from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class MidiDevice:
    """
    Representa un dispositivo MIDI de entrada.

    Attributes
    ----------
    name:
        Nombre del dispositivo.
    port_name:
        Nombre exacto del puerto devuelto por mido.
    """

    name: str
    port_name: str
