"""
Display number of pending updates for OpenSUSE Linux.

Display the system updates counted by zypper lu.

Configuration parameters:
    cache_timeout: How often we refresh this module in seconds
        (default 600)
    format: Display format to use
        (default 'zypper: {updates}')

Format placeholders:
    {updates} number of pending zypper updates

Color options:
    color_degraded: Upgrade available
    color_good: No upgrades needed

@author Ioannis Bonatakis <ybonatakis@suse.com>
@license BSD

SAMPLE OUTPUT
{'color': '#FFFF00', 'full_text': 'DNF: 14'}

"""

import subprocess
import re


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 600
    format = "zypper: {updates}"

    def post_config_hook(self):
        self._reg_ex_pkg = re.compile(b"v\\s\\S+", re.M)
        self._first = True
        self._updates = 0

    def zypper_updates(self):
        if self._first:
            self._first = False
            response = {
                "cached_until": self.py3.time_in(0),
                "full_text": self.py3.safe_format(self.format, {"updates": "?"}),
            }
            return response

        output, error = subprocess.Popen(
            ["zypper", "lu"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        ).communicate()
        updates = len(self._reg_ex_pkg.findall(output))

        if updates == 0:
            color = self.py3.COLOR_GOOD
            self._updates = 0
        else:
            self._updates = updates
            color = self.py3.COLOR_DEGRADED
        response = {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "color": color,
            "full_text": self.py3.safe_format(self.format, {"updates": updates}),
        }
        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
