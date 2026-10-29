import json
import os
import unittest
from unittest.mock import patch

from translator import LibreTranslateTranslator, create_translator


class TranslatorTests(unittest.TestCase):
    def test_local_provider_is_available_without_loading_argos(self):
        self.assertEqual(type(create_translator("local")).__name__, "ArgosTranslator")

    def test_unknown_provider_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unknown translation provider"):
            create_translator("unknown")

    def test_invalid_libretranslate_url_is_rejected(self):
        with patch.dict(os.environ, {"LIBRETRANSLATE_URL": "not-a-url"}):
            with self.assertRaisesRegex(ValueError, "must begin"):
                create_translator("libretranslate")

    def test_libretranslate_posts_text_and_reads_translation(self):
        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return b'{"translatedText":"Xin chao"}'

        with patch("translator.urlopen", return_value=Response()) as open_url:
            result = LibreTranslateTranslator("http://localhost:5000").translate("Hello", "en", "vi")
        self.assertEqual(result, "Xin chao")
        self.assertEqual(json.loads(open_url.call_args.args[0].data), {
            "q": "Hello", "source": "en", "target": "vi", "format": "text"
        })

    def test_api_key_is_sent_only_when_supplied(self):
        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return b'{"translatedText":"Bonjour"}'

        with patch("translator.urlopen", return_value=Response()) as open_url:
            LibreTranslateTranslator("https://translate.example", "test-key").translate("Hi", "en", "fr")
        self.assertEqual(json.loads(open_url.call_args.args[0].data)["api_key"], "test-key")


if __name__ == "__main__":
    unittest.main()
