from dataclasses import dataclass


@dataclass(frozen=True)
class VideoSignature:
    """
    Value Object que representa la firma técnica de un archivo de video.

    La firma encapsula todas las características relevantes para
    determinar compatibilidad entre videos sin exponer detalles
    de bajo nivel ni estructuras externas (ffprobe, JSON, etc.).

    Es un objeto:
    - Inmutable (frozen=True)
    - Comparable por igualdad estructural
    - Seguro para uso como clave o referencia estable

    Usos principales:
    - Validación de compatibilidad entre videos.
    - Verificación de end screens.
    - Agrupación de archivos con características homogéneas.
    """

    codec: str
    """
    Codec de video principal (por ejemplo: 'h264', 'hevc').
    """

    width: int
    """
    Ancho del video en píxeles.
    """

    height: int
    """
    Alto del video en píxeles.
    """

    frame_rate: float
    """
    Framerate del video expresado como valor decimal.
    """

    audio_codecs: tuple[str, ...]
    """
    Tupla ordenada con los codecs de audio presentes en el archivo.

    Se utiliza una tupla en lugar de una lista para garantizar
    inmutabilidad y permitir comparaciones directas.
    """

    audio_stream_count: int
    """
    Cantidad total de streams de audio presentes en el archivo.
    """
