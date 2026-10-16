r"""
Display the current status of the watson time-tracking tool.

Configuration parameters:
    cache_timeout: Number of seconds before state is re-read
        (default 10)
    format: The format for module output.
        (default '\?color=status Project {project}{tag_str} started')
    state_file: Path to the file which watson uses to track its own state
        (default '~/.config/watson/state')

Format placeholders:
    {project} Name of the active project
    {tag_str} String-representation of the list of active tags

Requires:
    https://github.com/TailorDev/Watson: commandline time tracking tool

@author Markus Sommer (https://github.com/CryptoCopter)
@license BSD

SAMPLE OUTPUT
{'full_text': 'Project baking [milk, eggs] started', 'color': '#00FF00'}
"""

import json
from pathlib import Path
from typing import Dict, List, Union


class Py3status:
    """ """

    # available configuration parameters
    cache_timeout = 10
    format = r"\?color=status Project {project}{tag_str} started"
    state_file = "~/.config/watson/state"

    def post_config_hook(self):
        self.state_file = Path(self.state_file).expanduser()

    def _error(self, error: str) -> Dict[str, str]:
        return {
            "full_text": self.py3.safe_format(r"\?color=bad {error}", {"error": error}),
            "cached_until": self.py3.time_in(seconds=self.cache_timeout),
        }

    def _format_output(self, session_data: Dict[str, Union[str, int, List[str]]]) -> Dict[str, str]:
        if not session_data:
            return self._error("No project started")

        project = session_data["project"]
        tags = session_data["tags"]

        if tags:
            tag_str = " [{}]".format(", ".join(tags))
        else:
            tag_str = " "

        self.color_status = self.py3.COLOR_GOOD
        return {
            "full_text": self.py3.safe_format(
                self.format, {"project": project, "tag_str": tag_str}
            ),
        }

    def watson(self) -> Dict[str, str]:
        if not self.state_file.is_file():
            return self._error("State file not found")

        try:
            with self.state_file.open("r") as f:
                session_data = json.load(f)
                output = self._format_output(session_data=session_data)
                output["cached_until"] = self.py3.time_in(seconds=self.cache_timeout)
                return output
        except OSError:
            return self._error("Error reading file")
        except json.JSONDecodeError:
            return self._error("Error decoding json")


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
