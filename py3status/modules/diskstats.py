# -*- coding: utf-8 -*-
"""
Display disk information.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 1)
    disks: specify a list of disks to use (default ['sd?'])
    format: display format for this module (default '{format_disk}')
    format_disk: display format for disks
        *(default '{name} [\?color=darkgray [\?color=read {read:.0f}]'
        '[\?if=read [\?max_length=1 {read_unit}]] [\?color=write {write:.0f}]'
        '[\?if=write [\?max_length=1 {write_unit}]]]')*
    format_disk_separator: show separator if more than one (default ' ')
    thresholds: specify color thresholds to use
        *(default [(0, "darkgray"), (0.001, "bad"),
        (1000, "degraded"), (1000000, "good")])*

Format placeholders:
    {format_disk} format for disks

format_disk placeholders:
    {name}
    {read}
    {total}
    {write}

Color thresholds:
    xxx: print a color based on the value of `xxx` placeholder

@author lasers

SAMPLE OUTPUT
{'full_text': 'sda '}
"""

from fnmatch import fnmatch


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 1
    disks = ["sd?"]
    format = "{format_disk}"
    format_disk = "{name} [\?color=darkgray [\?color=read {read:.0f}]"
    format_disk += "[\?if=read [\?max_length=1 {read_unit}]] [\?color=write "
    format_disk += "{write:.0f}][\?if=write [\?max_length=1 {write_unit}]]]"
    format_disk_separator = " "
    thresholds = [(0, "darkgray"), (0.001, "bad"), (1000, "degraded"), (1000000, "good")]

    # min_length?
    format_disk = "{name} [\?color=darkgray [\?min_length=4 [\?color=read "
    format_disk += "{read:.0f}][\?if=read [\?max_length=1 {read_unit}]]] "
    format_disk += "[\?min_length=4 [\?color=write {write:.0f}]"
    format_disk += "[\?if=write [\?max_length=1 {write_unit}]]]]"

    # total only?
    format_disk = "{name} [\?min_length=4 [\?color=darkgray [\?color=total {total:.0f}]"
    format_disk += "[\?if=total [\?max_length=1 {total_unit}]]]]"

    def post_config_hook(self):
        self.thresholds_init = self.py3.get_color_names_list(self.format)
        placeholders = self.py3.get_placeholders_list(self.format_disk)
        self.placeholders = [
            x for x in placeholders if x in ["read", "write", "total"]
        ]

        self.first_run = True
        self.sector_size = 512
        self.last_diskstats = self._get_diskstats_data()

        if self.disks:
            diskstats_data = self._get_diskstats_data()
            disks = []
            for _filter in self.disks:
                for k, v in diskstats_data.items():
                    if fnmatch(k, _filter):
                        disks.append(k)
            self.disks = disks

        self.thresholds_init = {}
        for name in ("format", "format_disk"):
            self.thresholds_init[name] = self.py3.get_color_names_list(
                getattr(self, name)
            )

    def _get_diskstats_data(self):
        diskstats = {}
        with open("/proc/diskstats") as f:
            for line in f.readlines():
                disk = line.split()
                disk[5] = int(disk[5])
                disk[9] = int(disk[9])
                diskstats[disk[2]] = disk
            return diskstats

    def diskstats(self):
        diskstats_data = self._get_diskstats_data()

        new_disk = []
        for k, v in diskstats_data.items():
            if self.disks and k not in self.disks:
                continue
            read = (v[5] - self.last_diskstats[k][5]) * 512
            write = (v[9] - self.last_diskstats[k][9]) * 512
            total = read + write
            disk = {"name": k, "total": total, "read": read, "write": write}

            for x in self.thresholds_init["format_disk"]:
                if x in disk:
                    self.py3.threshold_get_color(disk[x], x)

            for x in self.placeholders:
                if x in disk:
                    disk[x], disk[x + "_unit"] = self.py3.format_units(disk[x])

            format_disk = self.py3.safe_format(self.format_disk, disk)
            new_disk.append(format_disk)

        format_disk_separator = self.py3.safe_format(self.format_disk_separator)
        format_disk = self.py3.composite_join(format_disk_separator, new_disk)
        diskstats_data["format_disk"] = format_disk
        self.last_diskstats = diskstats_data

        for x in self.thresholds_init["format"]:
            if x in diskstats_data:
                self.py3.threshold_get_color(diskstats_data[x], x)

        self.first_run = False

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, diskstats_data),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
