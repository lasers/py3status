# -*- coding: utf-8 -*-
"""
Display animated banner.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 0.5)
    format: display format for this module (default "Sux dis. {banner}")

@author lasers, su8

SAMPLE OUTPUT
{'full_text': 'Sux dis. Suuuuuuuu8 ~~~'}
"""


class Py3status:
    """
    """

    # available configuration parameters
    format = "Sux dis. {banner}"
    cache_timeout = 0.5
    banner = [
        "Suuuuuuuu8",
        " Suuuuuuuu8",
        "Suuuuuuuu8 ~",
        " Suuuuuuuu8 ~",
        "Suuuuuuuu8 ~~",
        " Suuuuuuuu8 ~~",
        "Suuuuuuuu8 ~~~",
        " Suuuuuuuu8 ~~~",
        ":)",
    ]

    def post_config_hook(self):
        self.length = len(self.banner)
        self.index = -1

    def su8(self):
        self.index = (self.index + 1) % self.length
        su8_data = {"banner": self.banner[self.index]}

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, su8_data),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
