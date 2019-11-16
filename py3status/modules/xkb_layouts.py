# -*- coding: utf-8 -*-
"""
Switch keyboard layouts.

Configuration parameters:
    button_next: mouse button to cycle next layout (default 4)
    button_prev: mouse button to cycle previous layout (default 5)
    cache_timeout: refresh interval for this module (default 10)
    format: display format for this module (default '{format_input}')
    format_input: display format for inputs, otherwise auto (default None)
    format_input_separator: show separator if more than one (default ' ')
    format_libinput: display format for libinputs (default None)
    inputs: specify a list of inputs to use (default [])
    thresholds: specify color thresholds to use
        *(default [("fr", "lightgreen"), ("French", "lightgreen"),
        ("ru", "lightcoral"), ("Russian", "lightcoral"),
        ("ua", "khaki"), ("Ukrainian", "khaki"),
        ("us", "lightskyblue"), ("English", "lightskyblue"),
        ("English (US)", "lightskyblue"),
    ])*

Format placeholders:
    {format_input} format for inputs
    {input}        number of inputs, eg 1

format_input placeholders:
    xkblayout-state:
    xkbgroup:
    xkb-switch:
    swaymsg:
        {c} layout number, eg, 0
        {n} layout name, eg, English (US)
        {s} layout symbol, eg, us
        {v} layout variant, eg, basic
        {e} layout variant; {v} or {s}, eg, dvorak
        {C} layout count, eg, 2
    swaymsg:
        {identifier}              eg, 320:556 USB-HID Keyboard
        {name}                    eg, Trackball, Keyboard, etc
        {vendor}                  eg, 320
        {product}                 eg, 556
        {type}                    eg, pointer, keyboard, touchpad
        {xkb_layout_names}        eg, English (US)
        {xkb_active_layout_index} eg, 0
        {format_libinput}         format for libinputs

format_libinput placeholders:
    {send_event}       eg, enabled
    {accel_speed}      eg, 0.0
    {accel_profile}    eg, adaptive
    {natural_scroll}   eg, adaptive
    {left_handed}      eg, disabled
    {middle_emulation} eg, disabled
    {scroll_method}    eg, none
    {scroll_button}    eg, 274

    Use `swaymsg -r -t get_inputs` to get a list of current sway inputs
    and for a list of placeholders. Not all of placeholders will be usable.

Color thresholds:
    xxx: print a color based on the value of `xxx` placeholder

Requires:
    xkblayout-state: a command-line program to get/set the current keyboard layout
    xkbgroup: query and change xkb layout state
    xkb-switch: program that allows to query and change the xkb layout state
    swaymsg: send messages to sway window manager

Examples:
```
# add multiple inputs, aliases, and/or icons
xkb_inputs {
    inputs = [
        {"identifier": "3897:1553:Heng_Yu_Technology_Poker_II","alias": "⌨ Poker 2"},
        {"identifier": "1241:402:USB-HID_Keyboard", "alias": "⌨ Race 3"},
        {"identifier": "1133:16495:Logitech_MX_Ergo", "alias": "🖲️ MX Ergo", "type": "pointer"},
    ]
}

# specify inputs to fnmatch
xkb_inputs {
    # display logitech identifiers
    inputs = [{"identifier": "*Logitech*"}]

    # display logitech keyboards
    inputs = [{"name": "Logitech*", "type": "key*"}]

    # display pointers only
    inputs = [{"type": "pointer"}]
}
```

@author lasers, saengowp, javiertury

SAMPLE OUTPUT
[{"full_text": "Xkb "}, {"color": "#00FFFF", "full_text": "us"}]

ru
[{"full_text": "Xkb "}, {"color": "#00FFFF", "full_text": "ru"}]
"""

STRING_ERROR = "invalid command `%s`"
STRING_NOT_AVAILABLE = "no available binary"
COMMAND_NOT_INSTALLED = "command `%s` not installed"


class Xkb:
    """
    """

    def __init__(self, parent):
        self.parent = parent
        self.post_config_setup(parent)
        self.setup(parent)

    def post_config_setup(self, parent):
        if not self.parent.format_input:
            self.parent.format_input = "[\?color=s {s}][ {v}]"

    def setup(self, parent):
        pass

    def make_format_libinput(self, _input):
        return _input

    def make_format_input(self, inputs):
        new_input = []
        for _input in inputs:
            _input = self.make_format_libinput(_input)
            for x in self.parent.thresholds_init["format_input"]:
                if x in _input:
                    self.parent.py3.threshold_get_color(_input[x], x)
            new_input.append(
                self.parent.py3.safe_format(self.parent.format_input, _input)
            )

        format_input_separator = self.parent.py3.safe_format(
            self.parent.format_input_separator
        )
        format_input = self.parent.py3.composite_join(format_input_separator, new_input)

        return {"format_input": format_input, "input": len(inputs)}

    def set_xkb_layout(self, delta):
        pass


class Xkbgroup(Xkb):
    """
    xkbgroup - query and change xkb layout state
    """

    def setup(self, parent):
        from xkbgroup import XKeyboard

        self.xo = XKeyboard
        self.active_index = self.xo().group_num
        self.map = {"num": "c", "name": "n", "symbol": "s", "variant": "v"}

    def get_xkb_data(self):
        xo = self.xo()
        group_data = xo.group_data
        group_data = xo.group_data._asdict()
        temporary = {self.map[k]: v for k, v in group_data.items()}
        temporary["e"] = temporary["v"] or temporary["s"]
        temporary["C"] = xo.groups_count

        return self.make_format_input([temporary])

    def set_xkb_layout(self, delta):
        xo = self.xo()
        self.active_index += delta
        self.active_index %= xo.groups_count
        xo.group_num = self.active_index + 1


class Xkb_Switch(Xkb):
    """
    xkb-switch - program that allows to query and change the xkb layout state
    """

    def setup(self, parent):
        self.init = {"cache": {}}
        for name in ["cC", "n"]:
            self.init[name] = self.parent.py3.get_placeholders_list(
                self.parent.format_input, "[{}]".format(name)
            )

    def get_xkb_data(self):
        temporary = {}
        s = self.parent.py3.command_output("xkb-switch -p").strip()
        v = None

        if "(" in s and ")" in s:
            v = s[s.find("(") + 1 : s.find(")")]
            s = s[: s.find("(")]

        temporary.update({"s": s, "e": v or s, "v": v})

        if self.init["cC"]:
            layouts = self.parent.py3.command_output("xkb-switch -l").splitlines()
            temporary["C"] = len(layouts)

            for index, layout in enumerate(layouts):
                if s == layout:
                    temporary["c"] = index
                    break

        if self.init["n"]:
            try:
                name = self.init["cache"][s]
            except KeyError:
                name = None
                try:
                    with open("/usr/share/X11/xkb/symbols/{}".format(s)) as f:
                        for line in f.read().splitlines():
                            if "name" in line:
                                name = line.split('"')[-2]
                                break
                except FileNotFoundError:
                    pass
                self.init["cache"][s] = name
            temporary["n"] = name

        return self.make_format_input([temporary])

    def set_xkb_layout(self, delta):
        if delta > 0:
            self.parent.py3.command_run("xkb-switch -n")
        else:
            i = self.parent.py3.command_output("xkb-switch -p").strip()
            s = self.parent.py3.command_output("xkb-switch -l").splitlines()
            self.parent.py3.command_run("xkb-switch -s {}".format(s[s.index(i) - 1]))


class Xkblayout_State(Xkb):
    """
    xkblayout-state - a command-line program to get/set the current keyboard layout
    """

    def setup(self, parent):
        self.placeholders = self.parent.py3.get_placeholders_list(
            self.parent.format_input, "[cnsveC]"
        )

        self.separator = "|SEPARATOR|"
        self.xkblayout_command = "xkblayout-state print {}".format(
            self.separator.join(["%" + x for x in self.placeholders])
        )

    def get_xkb_data(self):
        line = self.parent.py3.command_output(self.xkblayout_command)
        temporary = dict(zip(self.placeholders, line.split(self.separator)))

        return self.make_format_input([temporary])

    def set_xkb_layout(self, delta):
        self.parent.py3.command_run(
            "xkblayout-state set {}{}".format({+1: "+", -1: "-"}[delta], abs(delta))
        )


class Swaymsg(Xkb):
    """
    swaymsg - send messages to sway window manager
    """

    def post_config_setup(self, parent):
        if not self.parent.format_input:
            self.parent.format_input = "[{alias}][\?soft  ][\?color=s {s}][ {v}]"

    def setup(self, parent):
        from json import loads
        from fnmatch import fnmatch

        self.fnmatch, self.loads = (fnmatch, loads)
        self.swaymsg_command = ["swaymsg", "--raw", "--type", "get_inputs"]
        self.init_format_libinput = (
            self.parent.format_libinput
            and self.parent.py3.format_contains(
                self.parent.format_input, "format_libinput"
            )
        )

    def make_format_libinput(self, _input):
        if not self.init_format_libinput:
            return _input

        libinput = _input.pop("libinput", {})
        for x in self.parent.thresholds_init["format_libinput"]:
            if x in libinput:
                self.parent.py3.threshold_get_color(libinput[x], x)

        format_libinput = self.parent.py3.safe_format(
            self.parent.format_libinput, libinput
        )
        _input["format_libinput"] = format_libinput
        return _input

    def update_xkb_input(self, xkb_input, user_input):
        xkb_input["alias"] = user_input.get("alias", xkb_input["name"])

        if "xkb_active_layout_name" in xkb_input:
            c = xkb_input["xkb_active_layout_index"]
            C = len(xkb_input["xkb_layout_names"])
            n = xkb_input["xkb_active_layout_name"]
            s = n
            v = None

            if "(" in n and ")" in n:
                s = n[n.find("(") + 1 : n.find(")")].lower()
                n = n[: n.find("(") - 1]

            xkb_input.update({"c": c, "C": C, "s": s, "e": v or s, "n": n, "v": v})

        return xkb_input

    def get_xkb_data(self):
        xkb_data = self.loads(self.parent.py3.command_output(self.swaymsg_command))
        excluded = ["alias"]
        new_xkb = []

        for xkb_input in xkb_data:
            if self.parent.inputs:
                for _filter in self.parent.inputs:
                    for key, value in _filter.items():
                        if key in excluded or key not in xkb_input:
                            continue
                        if not self.fnmatch(xkb_input[key], value):
                            break
                    else:
                        new_xkb.append(self.update_xkb_input(xkb_input, _filter))
            else:
                _filter = {}
                new_xkb.append(self.update_xkb_input(xkb_input, _filter))

        return self.make_format_input(new_xkb)


class Py3status:
    """
    """

    # available configuration parameters
    button_next = 4
    button_prev = 5
    cache_timeout = 10
    format = "{format_input}"
    format_input = None
    format_input_separator = " "
    format_libinput = None
    inputs = []
    thresholds = [
        ("fr", "lightgreen"),
        ("French", "lightgreen"),
        ("ru", "lightcoral"),
        ("Russian", "lightcoral"),
        ("ua", "khaki"),
        ("Ukrainian", "khaki"),
        ("us", "lightskyblue"),
        ("English", "lightskyblue"),
        ("English (US)", "lightskyblue"),
    ]

    def post_config_hook(self):
        # specify xkblayout-state, xkbgroup, xkb-switch, or swaymsg to use, otherwise auto
        self.switcher = getattr(self, "switcher", None)
        if getattr(self, "module_test", None) is True:
            self.format = "\[{switcher}\][\?soft  ]" + self.format

        keyboard_commands = ["xkblayout-state", "xkbgroup", "xkb-switch", "swaymsg"]
        if not self.switcher:
            if self.py3.get_wm_msg() == "swaymsg":
                self.switcher = "swaymsg"
            else:
                self.switcher = self.py3.check_commands(keyboard_commands)
        elif self.switcher not in keyboard_commands:
            raise Exception(STRING_ERROR % self.switcher)
        elif not self.py3.check_commands(self.switcher):
            raise Exception(COMMAND_NOT_INSTALLED % self.switcher)

        self.backend = globals()[self.switcher.replace("-", "_").title()](self)

        self.thresholds_init = {}
        for name in ["format", "format_input", "format_libinput"]:
            self.thresholds_init[name] = self.py3.get_color_names_list(
                getattr(self, name)
            )

    def xkb_layouts(self):
        xkb_data = self.backend.get_xkb_data()

        for x in self.thresholds_init["format"]:
            if x in xkb_data:
                self.py3.threshold_get_color(xkb_data[x], x)

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, xkb_data),
        }

    def on_click(self, event):
        button = event["button"]
        if button == self.button_next:
            self.backend.set_xkb_layout(+1)
        elif button == self.button_prev:
            self.backend.set_xkb_layout(-1)


if __name__ == "__main__":

    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    config = {"module_test": True}
    module_test(Py3status, config=config)
