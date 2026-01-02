# Esta App debe:

# - Recibir una lista de archivos de audios (canciones).
# - Recibir un video base cuya duración debe ser igual a la duración de la canción más larga.
# - En el directorio de las canciones crear un subdirectorio llamado videos.
# - Generar un video para cada canción usando el video base.
# - Debe cortar cada video a la duración de la canción con mkvmerge.
# - Debe borrar las partes que no sean canción.
# - El audio de cada canción para el video debe ser previamente convertido al formato AAC-LC @ 320 kbps, 48 kHz y normalizado por sonoridad (LUFS -14, True Peak -1.0 dBTP).
# - No debe modificarse la canción original.
# - Los archivos temporales de audio deben crearse en el subdirectorio videos y luego del proceso deben ser borrados.
# - El video final de cada canción debe mantener el nombre de la canción original. Solo que ahora con extensión .mkv.


class VideoMusicProcessor:
    pass
