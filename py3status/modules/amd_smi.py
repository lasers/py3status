r"""
Display AMD information currently exhibiting in the AMD GPUs.

amd-smi, short for AMD System Management Interface program, is a cross
platform tool that supports all standard AMD driver-supported Linux distros.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 10)
    categories: specify a list of amd-smi categories to use
        (default ['static', 'metric'])
    format: display format for this module (default '{format_gpu}')
    format_gpu: display format for AMD GPUs
        *(default '{asic_market_name} [\?color=temperature_edge_value '
        '{temperature_edge_value}°C] [\?color=mem_usage_used_vram_percent '
        '{mem_usage_used_vram_percent}%]')*
    format_gpu_separator: show separator if more than one (default ' ')
    memory_unit: specify memory unit, eg 'KiB', 'MiB', 'GiB', otherwise auto,
        or None to leave values/units as-is (default 'B')
    thresholds: specify color thresholds to use
        (default [(0, 'good'), (65, 'degraded'), (75, 'orange'), (85, 'bad')])

Format placeholders:
    {format_gpu} format for AMD GPUs

format_gpu placeholders:
    {asic_market_name}            official product name
    {temperature_edge_value}      core GPU temperature
    {mem_usage_used_vram_value}   VRAM used
    {mem_usage_used_vram_unit}    VRAM used unit
    {mem_usage_used_vram_percent} VRAM used percentage
    {mem_usage_total_vram_value}  total VRAM
    {mem_usage_total_vram_unit}   total VRAM unit

    Run `python /path/to/amd_smi.py --list-fields` for a full list of
    supported field names, grouped by category. Not all supported
    field names will be usable. See `amd-smi --help` for more information.

Color thresholds:
    format_gpu:
        `xxx`: print a color based on the value of AMD `xxx` field

Requires:
    amd-smi: command line interface to query AMD devices

Examples:
```
# display amd fields
amd_smi {
    format_gpu = '{asic_market_name} [\?color=temperature_edge_value '
    format_gpu += '{temperature_edge_value}°C] '
    format_gpu += '[\?color=mem_usage_used_vram_percent '
    format_gpu += '{mem_usage_used_vram_value} {mem_usage_used_vram_unit}'
    format_gpu += '[\?color=darkgray&show \|]{mem_usage_used_vram_percent:.1f}%]'
}

# display raw used/total VRAM too, untouched by memory_unit auto-scaling
amd_smi {
    memory_unit = None
    format_gpu = '{asic_market_name} [\?color=temperature_edge_value '
    format_gpu += '{temperature_edge_value}°C] '
    format_gpu += '[\?color=mem_usage_used_vram_percent '
    format_gpu += '{mem_usage_used_vram_percent:.1f}%] '
    format_gpu += '[{mem_usage_used_vram_value} {mem_usage_used_vram_unit}/'
    format_gpu += '{mem_usage_total_vram_value} {mem_usage_total_vram_unit}]'
}
```

@author lasers

SAMPLE OUTPUT
[
    {'full_text': 'AMD Radeon 780M Graphics '},
    {'color': '#00ff00', 'full_text': '58°C 26.6%'},
]

raw_vram
[
    {'full_text': 'AMD Radeon 780M Graphics '},
    {'color': '#00ff00', 'full_text': '58°C 26.6% '},
    {'full_text': '1091 MB/4096 MB'},
]
"""

from json import loads

STRING_NOT_INSTALLED = "not installed"
UNIT_MULTIPLIERS = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3}
EXCLUDED_VALUES = {"N/A", "No running processes detected"}
CATEGORIES = {
    "list": "list",
    "metric": "metric",
    "static": "static",
    "firmware": "firmware",
    "bad_pages": "bad-pages",
    "topology": "topology",
    "process": "process",
}


class Py3status:
    """ """

    # available configuration parameters
    cache_timeout = 10
    categories = ["static", "metric"]
    format = "{format_gpu}"
    format_gpu = (
        r"{asic_market_name} [\?color=temperature_edge_value "
        r"{temperature_edge_value}°C] "
        r"[\?color=mem_usage_used_vram_percent "
        r"{mem_usage_used_vram_percent}%]"
    )
    format_gpu_separator = " "
    memory_unit = "B"
    thresholds = [(0, "good"), (65, "degraded"), (75, "orange"), (85, "bad")]

    def post_config_hook(self):
        if not self.py3.check_commands("amd-smi"):
            raise Exception(STRING_NOT_INSTALLED)

        placeholders = self.py3.get_placeholders_list(self.format_gpu)
        format_gpu = {x: ":.1f" for x in placeholders if x.endswith("_percent")}
        self.format_gpu = self.py3.update_placeholder_formats(self.format_gpu, format_gpu)
        self.thresholds_init = self.py3.get_color_names_list(self.format_gpu)
        self.memory_properties = (
            {x[:-5] for x in placeholders if x.endswith("_unit")} if self.memory_unit else []
        )

        # list is always fetched/cached; static is fetched/cached once if listed.
        # self.categories only needs the rest. self.amd_data gets merged once here.
        categories = set(self.categories)
        list_data = self._get_gpu_data("list")
        static_data = self._get_gpu_data("static") if "static" in categories else {}
        self.categories = categories - {"static", "list"}
        self.amd_data = {i: e | static_data.get(i, {}) for i, e in list_data.items()}

    @staticmethod
    def _flatten(value, prefix=""):
        if not isinstance(value, (dict, list)):
            return {prefix: value}
        pairs = value.items() if isinstance(value, dict) else enumerate(value)
        flat = {}
        for key, sub_value in pairs:
            flat.update(Py3status._flatten(sub_value, f"{prefix}_{key}" if prefix else str(key)))
        return flat

    @staticmethod
    def _flatten_category(entry, drop=()):
        entry = {k: v for k, v in entry.items() if k not in drop}
        flat = Py3status._flatten(entry)
        return {k: v for k, v in flat.items() if v not in EXCLUDED_VALUES}

    def _get_gpu_data(self, category):
        data = loads(self.py3.command_output(f"amd-smi {category} --json"))
        data = data.get("gpu_data", data) if isinstance(data, dict) else data
        drop = () if category == "list" else {"gpu"}
        return {entry.get("gpu"): self._flatten_category(entry, drop) for entry in data}

    def amd_smi(self):
        amd_data = {name: self._get_gpu_data(CATEGORIES[name]) for name in self.categories}

        new_gpu = []
        for index, gpu in self.amd_data.items():
            for name in self.categories:
                gpu.update(amd_data[name][index])

            used = gpu.get("mem_usage_used_vram_value")
            total = gpu.get("mem_usage_total_vram_value")
            if used is not None and total:
                gpu["mem_usage_used_vram_percent"] = used / total * 100

            threshold_gpu = gpu.copy()

            for key in self.memory_properties:
                unit = gpu[f"{key}_unit"]
                if unit in UNIT_MULTIPLIERS:
                    value = gpu[f"{key}_value"] * UNIT_MULTIPLIERS[unit]
                    threshold_gpu[f"{key}_value"] = value / UNIT_MULTIPLIERS["MB"]
                    gpu[f"{key}_value"], gpu[f"{key}_unit"] = self.py3.format_units(
                        value, self.memory_unit
                    )

            for x in self.thresholds_init:
                if x in threshold_gpu:
                    self.py3.threshold_get_color(threshold_gpu[x], x)

            new_gpu.append(self.py3.safe_format(self.format_gpu, gpu))

        format_gpu_separator = self.py3.safe_format(self.format_gpu_separator)
        format_gpu = self.py3.composite_join(format_gpu_separator, new_gpu)

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, {"format_gpu": format_gpu}),
        }


if __name__ == "__main__":
    from sys import argv

    if "--list-fields" in argv:
        from json import dumps
        from subprocess import check_output
        from sys import exit

        def _fetch(category):
            data = loads(check_output(["amd-smi", category, "--json"], text=True))
            data = data.get("gpu_data", data) if isinstance(data, dict) else data
            drop = () if category == "list" else {"gpu"}
            return {entry.get("gpu"): Py3status._flatten_category(entry, drop) for entry in data}

        per_category = {name: _fetch(CATEGORIES[name]) for name in CATEGORIES}

        new_gpus = []
        msg = "This GPU contains {} supported fields."
        for index in sorted(per_category["list"]):
            gpu = {}
            total = 0
            for name in CATEGORIES:
                fields = per_category[name].get(index, {})
                if fields:
                    gpu[name] = fields
                total += len(fields)
            gpu["= " + msg.format(total)] = ""
            gpu["=" * (len(msg) + 2)] = ""
            new_gpus.append(gpu)

        print(dumps(new_gpus, sort_keys=True, indent=4))
        exit()
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
