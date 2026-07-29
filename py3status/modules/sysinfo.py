"""
Display static system information.

Configuration parameters:
    format: display format for this module
        *(default 'py3status {py3status_version} '
        '• python {python_version}')*

Format placeholders:
    User/session:
    {username} username, e.g. 'alex'
    {hostname} hostname, e.g. 'toolbx'

    Host/kernel:
    {machine} machine type, e.g. 'x86_64'
    {node} computer's network name, e.g. 'toolbx'
    {processor} processor name, e.g. 'amdk6' (often empty on Linux)
    {release} system's release, e.g. '7.1.4-200.fc44.x86_64'
    {system} system/OS name, e.g. 'Linux'
    {version} system's release version, e.g. '#1 SMP PREEMPT_DYNAMIC Sat Jul 18 19:16:16 UTC 2026'

    OS distribution:
    {os_id} distribution ID, e.g. "fedora"
    {os_name} distribution name, e.g. "Fedora Linux"
    {os_pretty_name} distribution pretty name, e.g. "Fedora Linux 44 (KDE Plasma)"
    {os_version} distribution version, e.g. "44 (KDE Plasma)"
    {os_version_id} distribution version ID, e.g. "44"

    Runtime/status bar:
    {py3status_version} py3status version, e.g. '3.64'
    {python_version} Python version, e.g. '3.14.6'
    {wm_name} window manager detected by py3status, e.g. 'i3' or 'sway'

Examples:
````
# display system information
sysinfo uname {
    format = '{system} {release}'
}

# display logged-in username
sysinfo whoami {
    format = "{username}"
}
```

@author ultrabug, lasers

SAMPLE OUTPUT
{'full_text': 'py3status 3.64 • python 3.14.6'}
"""

from getpass import getuser
from os import getgid, getuid
from os import name as os_name
from platform import (
    freedesktop_os_release,
    libc_ver,
    platform,
    python_version,
    uname,
)
from pwd import getpwuid
from socket import gethostname
from sys import platform as sys_platform

from py3status.version import version as py3status_version


def get_sysinfo_data():
    uname_data = uname()
    user_data = getpwuid(getuid())
    libc_info = libc_ver()

    try:
        os_release = freedesktop_os_release()
    except OSError:
        os_release = {}

    return {
        "username": getuser(),
        "hostname": gethostname(),
        "uid": getuid(),
        "gid": getgid(),
        "home": user_data.pw_dir,
        "shell": user_data.pw_shell,
        "gecos": user_data.pw_gecos,
        "system": uname_data.system,
        "node": uname_data.node,
        "release": uname_data.release,
        "version": uname_data.version,
        "machine": uname_data.machine,
        "processor": uname_data.processor,
        "platform": platform(),
        "sys_platform": sys_platform,
        "os_type": os_name,
        "libc_name": libc_info[0],
        "libc_version": libc_info[1],
        "python_version": python_version(),
        "py3status_version": py3status_version,
        "os_name": os_release.get("NAME", ""),
        "os_id": os_release.get("ID", ""),
        "os_version": os_release.get("VERSION", ""),
        "os_version_id": os_release.get("VERSION_ID", ""),
        "os_pretty_name": os_release.get("PRETTY_NAME", ""),
    }


class Py3status:
    """ """

    # available configuration parameters
    format = 'py3status {py3status_version} • python {python_version}'

    def post_config_hook(self):
        self.sysinfo_data = get_sysinfo_data()
        self.sysinfo_data["wm_name"] = self.py3._py3_wrapper.config.get("wm_name")

        if self.py3._py3_wrapper.config.get("testing"):
            self.sysinfo_data["wm_name"] = "test_wm"
            width = max(map(len, self.sysinfo_data))
            for name, value in sorted(self.sysinfo_data.items()):
                self.py3.log(f"{name:<{width}}  {value}", level="debug")

    def sysinfo(self):
        return {
            "cached_until": self.py3.CACHE_FOREVER,
            "full_text": self.py3.safe_format(self.format, self.sysinfo_data),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
