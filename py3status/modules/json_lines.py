"""
Display JSON lines.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 3600)
    format: display format for this module (default "{format_json}")
    format_json: display format for json lines (default "{name}")
    format_json_separator: show separator if more than one (default " ")

Format placeholders:
    Placeholders will be replaced by the JSON keys.

@author lasers
"""

from json import loads


class Py3status:
    """ """

    # available configuration parameters
    cache_timeout = 3600
    format = "{format_json}"
    format_json = "[\?color=lightblue {name}] [\?color=red {version}] [\?color=lightgrey&show ->] [\?color=lime {upstream}]"
    format_json_separator = " "
    command = "aur-out-of-date -user syyyr -json"

    def json_lines(self):
        json_objects = [loads(x) for x in self.py3.command_output(self.command).splitlines()]
        new_json = [self.py3.safe_format(self.format_json, json) for json in json_objects]

        format_json_separator = self.py3.safe_format(self.format_json_separator)
        format_json = self.py3.composite_join(format_json_separator, new_json)
        json_data = {"format_json": format_json}

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, json_data)
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
