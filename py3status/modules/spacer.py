# -*- coding: utf-8 -*-
"""
Display spaces.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 1)
    format: display format for this module (default '{output}')
    width: specify a number of columns for the monitor (default 220)

Format placeholders:
    {output} output

@author lasers

SAMPLE OUTPUT
{'full_text': 'spacer'}
"""


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 1
    format = "{output}"
    width = 220

    def spacer(self):
        width = 0

        for name, data in self.py3._output_modules.items():
            if any(x in name for x in ["group", "frame", "scroll", "spacer"]):
                continue
            module = data["module"].get_latest()
            width += sum([len(x["full_text"]) for x in module])

        output = " " * (self.width - width)

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, {"output": output}),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
