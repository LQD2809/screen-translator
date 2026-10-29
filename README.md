# Screen Translator

A Windows desktop tool for translating text visible on your screen. The interface lets you capture a screen region, open an image, or type/paste text, then shows the result in a movable, always-on-top translation card.

The first version handles on-screen text only. **It does not translate audio or speech.** For videos, select a region and enable periodic refresh to re-read changing subtitles.

## Requirements

- Windows 10 or later
- Python 3.10+
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) installed on Windows and available on `PATH`
- Optional offline translation: Argos Translate and a matching language package
- Optional online translation: a LibreTranslate server

## Install and run

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

In the app, select **Local (Argos)** or **LibreTranslate**, then choose the source and destination languages. Enter language codes such as `en` and `vi`.

- Local translation requires Argos Translate and an installed package for the selected language pair. Install it with `python -m pip install argostranslate`, then add the desired language package using the [Argos Translate instructions](https://github.com/argosopentech/argos-translate). OCR and image processing remain local.
- To use an online LibreTranslate endpoint, set `LIBRETRANSLATE_URL` (defaults to `http://localhost:5000`) and, if required by that server, `LIBRETRANSLATE_API_KEY` before starting the app. No API key is included. Only the text being translated is sent to the configured endpoint.

## Use

- **Capture screen**: drag a rectangle around on-screen text. OCR runs and the translation appears in the floating card.
- **Open image**: select a PNG, JPEG, BMP, or TIFF image for OCR.
- **Translate text**: type or paste text in the source field and press the button.
- **Video subtitles**: capture a region, then use **Refresh every 2s** to periodically OCR that same region. This is best-effort: frames may be repeated or missed depending on playback and text quality.
- **Translation card**: drag it to move; use the slider to change opacity.

## Tests

```powershell
python -m unittest discover -s tests -v
```

Screen capture and overlay require an interactive Windows desktop with Tesseract installed.
