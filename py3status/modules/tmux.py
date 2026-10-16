r"""
Display information about your running terminal multiplexers.

tmux is a terminal multiplexer: it enables a number of terminals to be
created, accessed, and controlled from a single screen. tmux may be detached
from a screen and continue running in the background, then later reattached.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 10)
    format: display format for this module (default '{format_session}')
    format_buffer: display format for buffers (default '{buffer_name}')
    format_buffer_separator: show separator if more than one (default ' ')
    format_client: display format for clients (default '{client_termname}')
    format_client_separator: show separator if more than one (default ' ')
    format_pane: display format for panes (default '{pane_title}')
    format_pane_separator: show separator if more than one (default ' ')
    format_session: display format for sessions (default '{session_name}')
    format_session_separator: show separator if more than one (default ' ')
    format_window: display format for windows (default '{window_name}')
    format_window_separator: show separator if more than one (default ' ')
    thresholds: specify color thresholds to use (default [])

Format placeholders:
    {buffer}         number of buffers
    {client}         number of clients
    {pane}           number of panes
    {session}        number of sessions
    {window}         number of windows
    {format_buffer}  format for buffers
    {format_client}  format for clients
    {format_pane}    format for panes
    {format_session} format for sessions
    {format_window}  format for windows

format_xxx placeholders:
    See `man -P 'less +/^FORMATS' tmux` for a full list of tmux
    variables to use. Not all tmux variables will be usable.

Color thresholds:
    xxx: print a color based on the value of `xxx` placeholder, either a
        count in `format` (eg `session`) or a value in `format_xxx`
        (eg `session_windows`, `session_name`)

Examples:
```
# show window names, with the current window of each session in green
tmux {
    format = '{format_window}'
    format_window = '[\?if=window_active [\?color=good {window_name}]'
    format_window += '|{window_name}]'
    format_window_separator = ', '
}

# show the current window of each session
tmux {
    format = '{format_window}'
    format_window = '[\?if=window_active [\?color=darkgray {session_name}:]'
    format_window += '{window_name}]'
}

# show attached sessions in green, detached ones in yellow
tmux {
    format_session = '[\?if=session_attached [\?color=good {session_name}]'
    format_session += '|[\?color=degraded {session_name}]]'
}

# show windows that rang the bell, in red
tmux {
    format = '{format_window}'
    format_window = '[\?if=window_bell_flag [\?color=bad '
    format_window += '{session_name}:{window_name}]]'
}

# show what is running in each window
tmux {
    format = '{format_pane}'
    format_pane = '[\?if=pane_active [\?color=darkgray {window_name}:]'
    format_pane += '{pane_current_command}]'
    format_pane_separator = ', '
}

# show counts, with the session count in red when tmux isn't running
tmux {
    format = '[\?color=session {session}s] {window}w {pane}p'
    thresholds = [(0, 'bad'), (1, 'good')]
}
```

@author lasers

SAMPLE OUTPUT
{'full_text': '[tmux] py3status'}
"""

STRING_NOT_INSTALLED = "not installed"
NEW_LINE = "|NEWLINE|"
SEPARATOR = "|SEPARATOR|"
NO_SERVER = (
    "no server running",  # socket file left behind
    "No such file or directory",  # no socket file yet
    "server exited unexpectedly",  # server died while we connected
)
# read tmux flags (1 if ..., else 0) and counts (number of ...) as int
# fmt: off
NUMBERS = {
    "alternate_on", "bracket_paste_flag", "client_control_mode", "client_prefix", "client_readonly",
    "client_utf8", "cursor_blinking", "cursor_flag", "cursor_very_visible", "history_bytes",
    "insert_flag", "keypad_cursor_flag", "keypad_flag", "loop_last_flag", "mouse_all_flag",
    "mouse_any_flag", "mouse_button_flag", "mouse_sgr_flag", "mouse_standard_flag",
    "mouse_utf8_flag", "origin_flag", "pane_active", "pane_at_bottom", "pane_at_left",
    "pane_at_right", "pane_at_top", "pane_dead", "pane_floating_flag", "pane_format",
    "pane_in_mode", "pane_input_off", "pane_last", "pane_marked", "pane_marked_set", "pane_pipe",
    "pane_synchronized", "pane_unseen_changes", "pane_zoomed_flag", "rectangle_toggle",
    "search_count_partial", "search_present", "selection_active", "selection_present",
    "server_sessions", "session_active", "session_activity_flag", "session_attached",
    "session_bell_flag", "session_format", "session_group_attached", "session_group_many_attached",
    "session_grouped", "session_many_attached", "session_marked", "session_silence_flag",
    "session_windows", "sixel_support", "synchronized_output_flag", "window_active",
    "window_active_clients", "window_active_sessions", "window_activity_flag", "window_bell_flag",
    "window_bigger", "window_end_flag", "window_format", "window_last_flag", "window_linked",
    "window_linked_sessions", "window_marked_flag", "window_panes", "window_silence_flag",
    "window_start_flag", "window_zoomed_flag", "wrap_flag",
}
# fmt: on

COMMANDS = {
    "buffer": "list-buffers",
    "client": "list-clients",
    "pane": "list-panes -a",
    "session": "list-sessions",
    "window": "list-windows -a",
}


class Py3status:
    """ """

    # available configuration parameters
    cache_timeout = 10
    format = "{format_session}"
    format_buffer = "{buffer_name}"
    format_buffer_separator = " "
    format_client = "{client_termname}"
    format_client_separator = " "
    format_pane = "{pane_title}"
    format_pane_separator = " "
    format_session = "{session_name}"
    format_session_separator = " "
    format_window = "{window_name}"
    format_window_separator = " "
    thresholds = []

    def post_config_hook(self):
        if not self.py3.check_commands("tmux"):
            raise Exception(STRING_NOT_INSTALLED)

        self.thresholds_init = {"format": self.py3.get_color_names_list(self.format)}
        placeholders = set(self.py3.get_placeholders_list(self.format))
        placeholders.update(self.thresholds_init["format"])
        self.tmux_queries = {}
        for name, command in COMMANDS.items():
            if not {name, f"format_{name}"} & placeholders:
                continue
            format_string = getattr(self, f"format_{name}")
            self.thresholds_init[name] = self.py3.get_color_names_list(format_string)
            keys = list(
                {*self.py3.get_placeholders_list(format_string), *self.thresholds_init[name]}
            )
            fields = SEPARATOR.join(f"#{{{key}}}" for key in keys)
            self.tmux_queries[name] = {
                "format": format_string,
                "separator": getattr(self, f"format_{name}_separator"),
                "command": f'tmux {command} -F "{fields}{NEW_LINE}"',
                "numbers": NUMBERS.intersection(keys),
                "placeholders": keys,
                "error": None,
            }

    def _get_rows(self, name, query):
        try:
            output = self.py3.command_output(query["command"])
        except self.py3.CommandError as err:
            # tmux has nothing to list without a server, which is fine.
            # anything else (eg a socket we can't use) is worth saying, once.
            error = (err.error or err.output or str(err)).strip()
            if any(x in error for x in NO_SERVER):
                query["error"] = None
            elif query["error"] != error:
                query["error"] = error
                self.py3.log(f"{COMMANDS[name]}: {error}", level=self.py3.LOG_WARNING)
            return []
        query["error"] = None
        rows = []
        for line in output.split(NEW_LINE + "\n")[:-1]:
            row = dict(zip(query["placeholders"], line.split(SEPARATOR)))
            for key in query["numbers"]:
                if row[key].isdigit():
                    row[key] = int(row[key])
            rows.append(row)
        return rows

    def tmux(self):
        tmux_data = {}
        for name, query in self.tmux_queries.items():
            rows = self._get_rows(name, query)
            new_row = []
            for row in rows:
                for x in self.thresholds_init[name]:
                    if x in row:
                        self.py3.threshold_get_color(row[x], x)
                new_row.append(self.py3.safe_format(query["format"], row))

            format_row_separator = self.py3.safe_format(query["separator"])
            format_row = self.py3.composite_join(format_row_separator, new_row)
            tmux_data.update({name: len(rows), f"format_{name}": format_row})

        for x in self.thresholds_init["format"]:
            if x in tmux_data:
                self.py3.threshold_get_color(tmux_data[x], x)

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, tmux_data),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
