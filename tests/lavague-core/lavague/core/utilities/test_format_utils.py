import unittest
from lavague.core.utilities.format_utils import extract_and_eval


class TestFormatUtils(unittest.TestCase):
    def test_extract_and_eval(self):
        self.assertEqual(
            extract_and_eval(
                """[{'query':'#root', 'action':'Click on the root element'}]"""
            ),
            [{"query": "#root", "action": "Click on the root element"}],
        )
        self.assertEqual(
            extract_and_eval(
                """[{'query':'img[data-testid="lang-switch"]', 'action':'Click on the image with the `data-testid` attribute equal to `lang-switch`'}]"""
            ),
            [
                {
                    "query": 'img[data-testid="lang-switch"]',
                    "action": "Click on the image with the `data-testid` attribute equal to `lang-switch`",
                }
            ],
        )
        self.assertEqual(
            extract_and_eval(
                """[{'query':'img[data-testid="lang-switch"]', 'action':'Click on the image with the `data-testid` attribute equal to `lang-switch`'}, {'query':'img[data-testid="lang-switch2"]', 'action':'Click on the image with the `data-testid` attribute equal to `lang-switch2`'}]"""
            ),
            [
                {
                    "query": 'img[data-testid="lang-switch"]',
                    "action": "Click on the image with the `data-testid` attribute equal to `lang-switch`",
                },
                {
                    "query": 'img[data-testid="lang-switch2"]',
                    "action": "Click on the image with the `data-testid` attribute equal to `lang-switch2`",
                },
            ],
        )


if __name__ == "__main__":
    unittest.main()
