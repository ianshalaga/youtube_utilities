"""
processor.py

Procesador principal de la aplicación MIDI Mapper.
"""

from services.midi.devices.device_discovery import MidiDeviceDiscovery


class MidiMapperProcessor:
    """
    Orquesta el flujo principal de la aplicación MIDI Mapper.
    """

    def __init__(
        self,
        target_device: str,
    ) -> None:

        self._target_device = target_device
        self._device_discovery = MidiDeviceDiscovery()

    def process(self) -> None:
        """
        Ejecuta el flujo principal.
        """

        print("=" * 40)
        print("Buscando dispositivos MIDI...")
        print("=" * 40)
        print()

        devices = self._device_discovery.list_input_devices()

        if not devices:
            print("No se encontraron dispositivos MIDI.")
            return

        for index, device in enumerate(devices):
            print(f"[{index}] {device.name}")

        print()

        device = self._device_discovery.find_device(
            self._target_device
        )

        if device is None:
            print(
                f"✗ No se encontró '{self.TARGET_DEVICE}'."
            )
            return

        print(
            f"✓ Dispositivo encontrado: {device.name}"
        )
