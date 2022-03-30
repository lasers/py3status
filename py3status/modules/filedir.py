"""
Display estimated size usage for file and directories.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 10)
    filedirs: specify a list of tuples, eg (name, path).
    format: display format for this module (default '{format_filedir}')
    format_filedir: display format for files and directories
        (default "\?if=size {name} {size} {unit}")
    format_filedir_separator: show separator if more than one (default ' ')

Format placeholders:
    {format_filedir} format for files and directories

format_filedir placeholders:
    {name}        name, eg Desktop
    {path}        path, eg ~/Desktop
    {size}        size, eg 21.75
    {unit}        unit, eg GiB

Examples:
```
```

@author lasers

SAMPLE OUTPUT
"""

from pathlib import Path


class Py3status:
    """ """

    # available configuration parameters
    cache_timeout = 10
    format = "{format_filedir}"
    format_filedir = r"\?if=size {name} {size} {unit}"
    format_filedir_separator = " "
    filedirs = [
        ("Desktop", "~/Desktop"),
        ("Documents", "~/Documents"),
        ("Downloads", "~/Downloads"),
        ("Music", "~/Music"),
        ("Pictures", "~/Pictures"),
        ("Public", "~/Public"),
        ("Templates", "~/Templates"),
        ("Videos", "~/Videos"),
    ]

    def filedir(self):
        new_filedirs = []

        for name, path in self.filedirs:
            path = Path(path).expanduser()
            size = sum(f.stat().st_size for f in path.glob("**/*") if f.is_file())
            (value, unit) = self.py3.format_units(size)

            filedir_data = {
                "name": name,
                "path": path,
                "size": value,
                "unit": unit,
            }

            new_filedirs.append(self.py3.safe_format(self.format_filedir, filedir_data))

        format_filedir_separator = self.py3.safe_format(self.format_filedir_separator)
        format_filedir = self.py3.composite_join(format_filedir_separator, new_filedirs)

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(
                self.format, {"format_filedir": format_filedir}
            ),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
