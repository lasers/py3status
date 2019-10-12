# -*- coding: utf-8 -*-
"""
Display spaces.

Configuration parameters:
    button_down: specify button number to decrease width (default 5)
    button_up: specify button number to increase width (default 4)
    cache_timeout: refresh interval for this module (default 1)
    format: display format for this module (default '{output}{width}')

Format placeholders:
    {output} output
    {width} width number

@author lasers

SAMPLE OUTPUT
{'full_text': 'spacer'}
"""


class Py3status:
    """
    """

    # available configuration parameters
    button_down = 5
    button_up = 4
    cache_timeout = 1
    format = "{output}{width}"

    def post_config_hook(self):
        self.print_width = False
        self.show_width = self.py3.format_contains(self.format, "width")
        self.width = self.py3.storage_get("width") or 220

    def spacer(self):
        width = 0

        for name, data in self.py3._output_modules.items():
            if any(x in name for x in ["group", "frame", "scroll", "spacer"]):
                continue
            module = data["module"].get_latest()
            width += sum([len(x["full_text"]) for x in module])

        output = " " * (self.width - width)

        if self.print_width and self.show_width:
            self.print_width = False
            output = output[len(str(self.width)) :]
            width = self.width
        else:
            width = ""

        space_data = {"output": output, "width": width}

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, space_data),
        }

    def kill(self):
        self.py3.storage_set("width", self.width)

    def on_click(self, event):
        button = event["button"]
        if button == self.button_up:
            self.width += 1
            self.print_width = True
        elif button == self.button_down:
            self.width -= 1
            self.print_width = True


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
