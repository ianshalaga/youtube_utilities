
from pathlib import Path

from django import forms


class VideoMusicForm(forms.Form):
    max_items_per_dir = forms.IntegerField(
        label="Límite de pistas por directorio",
        min_value=1,
        initial=15,
    )

    audios_dir = forms.CharField(
        label="Directorio de audios",
        max_length=1024,
        strip=True,
    )

    video_path = forms.CharField(
        label="Vídeo base",
        max_length=1024,
        strip=True,
    )

    output_dir = forms.CharField(
        label="Directorio de salida",
        max_length=1024,
        strip=True,
        help_text=(
            "Puede ser una ruta absoluta o un directorio "
            "relativo al directorio de audios."
        ),
    )

    def clean_audios_dir(self) -> str:
        value = self.cleaned_data["audios_dir"]
        path = Path(value)

        if not path.is_dir():
            raise forms.ValidationError(
                "El directorio de audios no existe o no es un directorio."
            )

        return value

    def clean_video_path(self) -> str:
        value = self.cleaned_data["video_path"]
        path = Path(value)

        if not path.is_file():
            raise forms.ValidationError(
                "El vídeo base no existe o no es un archivo."
            )

        return value
