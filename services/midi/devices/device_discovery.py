"""
device_discovery.py

Descubrimiento de dispositivos MIDI disponibles en el sistema.

Este módulo encapsula el acceso a la biblioteca ``mido`` para que el resto
de la aplicación no dependa directamente de ella.
"""

from __future__ import annotations

from typing import Optional

import mido

from services.midi.devices.midi_device import MidiDevice


class MidiDeviceDiscovery:
    """Servicio encargado de descubrir dispositivos MIDI."""

    @staticmethod
    def list_input_devices() -> list[MidiDevice]:
        """
        Devuelve todos los dispositivos MIDI de entrada.

        Returns
        -------
        list[MidiDevice]
            Lista de dispositivos encontrados.
        """
        return [
            MidiDevice(
                name=port_name,
                port_name=port_name,
            )
            for port_name in mido.get_input_names()
        ]

    @classmethod
    def find_device(cls, device_name: str) -> Optional[MidiDevice]:
        """
        Busca un dispositivo cuyo nombre contenga el texto indicado.

        La búsqueda no distingue mayúsculas/minúsculas.

        Parameters
        ----------
        device_name
            Nombre (o parte del nombre) del dispositivo.

        Returns
        -------
        MidiDevice | None
        """

        search = device_name.casefold()

        for device in cls.list_input_devices():
            if search in device.name.casefold():
                return device

        return None

    @classmethod
    def device_exists(cls, device_name: str) -> bool:
        """
        Indica si existe un dispositivo con ese nombre.

        Parameters
        ----------
        device_name
            Nombre o parte del nombre.

        Returns
        -------
        bool
        """

        return cls.find_device(device_name) is not None
