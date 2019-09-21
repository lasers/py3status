# -*- coding: utf-8 -*-
"""
Display spaces.

Configuration parameters:
    format: display format for this module (default '{output}')
    cache_timeout: refresh interval for this module (default 1)
    width: specify a number of columns for the monitor (default 270)

@author spaceguy

SAMPLE OUTPUT
{'full_text': 'spacer'}
"""


class Py3status:
    """
    """

    # available configuration parameters
    format = "{output}"
    cache_timeout = 1
    width = 270

    def spacer(self):
        output = self.py3.get_output()
        self.py3.log(output)
        width = 0
        num = 0

        for name, data in output.items():
            if any(x in name for x in ["group", "frame", "scroll", "spacer"]):
                continue
            self.py3.log(name)
            module = data["module"].get_latest()

            for x in module:
                # self.py3.log(x)
                width += len(x["full_text"])

            num += 1

        free_space = self.width - width
        self.py3.log("WIDTH:{}, FREE_SPACE:{}".format(width, free_space))
        space_data = {"output": " " * free_space}

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, space_data),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
