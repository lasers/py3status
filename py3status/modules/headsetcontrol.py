r"""
Display device readouts currently exhibiting in supported gaming headsets.

HeadSetControl is a cross-platform tool to control USB gaming headsets. It can manage
sidetone, battery status, LED lights, equalizers, and more. Supported gaming headsets:
Logitech G930, G533, G633, G933 SteelSeries Arctis 7/PRO 2019 and Corsair VOID (Pro).

Configuration parameters:
    cache_timeout: refresh interval for this module (default 10)
    format: display format for this module (default '{format_device}')
    format_device: display format for devices
        (default '{product} [\?color=battery_level {battery_level}%]')
    format_device_separator: show separator if more than one (default ' ')
    thresholds: specify color thresholds to use
        (default [(0, 'darkgray'), (25, 'bad'), (50, 'degraded'), (75, 'good')])

Format placeholders:
    {name}           eg, HeadsetControl
    {version}        eg, 3.1.0-84-gc8bbeb3
    {api_version}    eg, 1.4
    {hidapi_version} eg, 0.15.0
    {device_count}   eg, 1

format_device placeholders:
    {status}     eg, success
    {device}     eg, Logitech G PRO X 2 LIGHTSPEED
    {vendor}     eg, Logitech
    {product}    eg, PRO X 2 LIGHTSPEED
    {id_vendor}  eg, 0x046d
    {id_product} eg, 0x0af7

Requires:
    headsetcontrol: A cross-platform tool to control USB gaming headsets

Examples:
```
# hide headsets based on battery levels (ie disconnected)
headsetcontrol {
    format_device = "[\?if=battery_level>0 [\?color=darkgray {product}] "
    format_device += "[\?color=battery_level {battery_level}%]]"
}
```

@author Valentin Weber <valentin+py3status@wv2.ch>
@license BSD

SAMPLE OUTPUT
[
    {'full_text': 'PRO X 2 LIGHTSPEED '},
    {'full_text': '75%', 'color': '#00f000'},
]
"""

from json import loads

STRING_NOT_INSTALLED = "not installed"


class Py3status:
    """ """

    # available configuration parameters
    cache_timeout = 10
    format = "{format_device}"
    format_device = "{product} [\?color=battery_level {battery_level}%]"
    format_device_separator = " "
    thresholds = [(0, 'darkgray'), (25, 'bad'), (50, 'degraded'), (75, 'good')]

    def post_config_hook(self):
        self.headsetcontrol_command = ["headsetcontrol", "-o", "json"]
        if not self.py3.check_commands(self.headsetcontrol_command):
            raise Exception(STRING_NOT_INSTALLED)

        self.thresholds_init = {}
        for name in ["format", "format_device"]:
            self.thresholds_init[name] = self.py3.get_color_names_list(getattr(self, name))

    def _get_headsetcontrol_data(self):
        try:
            data = self.py3.command_output(self.headsetcontrol_command)
        except self.py3.CommandError as ce:
            data = ce.output
        return loads(data)

    def headsetcontrol(self):
        headsetcontrol_data = self._get_headsetcontrol_data()
        devices = headsetcontrol_data.pop("devices", [])
        new_devices = []

        for device in devices:
            device = self.py3.flatten_dict(device, "_")

            for x in self.thresholds_init["format_device"]:
                if x in device:
                    self.py3.threshold_get_color(device[x], x)

            new_devices.append(self.py3.safe_format(self.format_device, device))

        format_device_separator = self.py3.safe_format(self.format_device_separator)
        format_device = self.py3.composite_join(format_device_separator, new_devices)
        headsetcontrol_data.update({"format_device": format_device})

        for x in self.thresholds_init["format"]:
            if x in headset_data:
                self.py3.threshold_get_color(headsetcontrol_data[x], x)

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, headsetcontrol_data),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """

    from py3status.module_test import module_test

    module_test(Py3status)
