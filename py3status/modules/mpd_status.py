# -*- coding: utf-8 -*-
"""
Display songs currently playing in Music Player Daemon.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 5)
    format: display format for this module
        (default '\?color=state [{artist} - {title}|{file}]')
    host: specify server host to use (default 'localhost')
    password: specify server password to use (default None)
    port: specify server port to use (default 6600)
    thresholds: specify color thresholds to use
        (default [('stop', 'bad'), ('pause', 'degraded'), ('play', 'good')])

Format placeholders:
    {artist}         eg Music For Programming
    {audio}          eg 44100:24:2
    {bitrate}        eg 112
    {consume}        eg 0
    {date}           eg 2018
    {duration}       eg 7547.663
    {elapsed}        eg 8.626
    {file}           eg music_for_programming_50-misc.works.mp3
    {id}             eg 4
    {last-modified}  eg 2018-07-17T16:21:16Z
    {mixrampdb}      eg 0.000000
    {playlist}       eg 6
    {playlistlength} eg 2
    {pos}            eg 1
    {random}         eg 0
    {repeat}         eg 0
    {single}         eg 0
    {song}           eg 1
    {songid}         eg 4
    {state}          eg pause
    {time}           eg 7548
    {title}          eg Episode 50 (Compiled by Misc.)
    {volume}         eg 100

Requires:
    python-mpd2: a Python MPD client library

Examples:
```
```

@author shadowprince, zopieux
@license Eclipse Public License

SAMPLE OUTPUT
{'color': '#00ff00', 'full_text': 'Music For Programming - Idol Eyes'}

paused
{'color': '#ffff00', 'full_text': 'Music For Programming - Idol Eyes'}

stopped
{'color': '#ff0000', 'full_text': 'Music For Programming - Idol Eyes'}
"""

from mpd import MPDClient


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 5
    format = "\?color=state [{artist} - {title}|{file}]"
    host = "localhost"
    password = None
    port = 6600
    thresholds = [("stop", "bad"), ("pause", "degraded"), ("play", "good")]

    def post_config_hook(self):
        self.client = None
        self.client_timeout = 10
        self.thresholds_init = self.py3.get_color_names_list(self.format)

        self.placeholders = []
        for x in self.py3.get_placeholders_list(self.format):
            if x in ["elapsed", "duration", "time", "pos"]:
                self.placeholders.append(x)

    def _get_mpd(self, disconnect=False):
        if disconnect:
            if self.client is not None:
                try:
                    self.client.disconnect()
                finally:
                    self.client = None
        else:
            try:
                if self.client is None:
                    self.client = MPDClient()
                    self.client.timeout = self.client_timeout
                    self.client.connect(host=self.host, port=self.port)
                    if self.password:
                        self.client.password(self.password)
                return self.client
            except Exception as e:
                self.client = None
                raise e

    def mpd_status(self):
        mpd_data = {}

        try:
            client = self._get_mpd()
            for query in [client.status, client.currentsong]:
                mpd_data.update(query())
        except Exception as e:
            self._get_mpd(disconnect=True)
            self.py3.error(format(e))

        for x in self.thresholds_init:
            if x in mpd_data:
                self.py3.threshold_get_color(mpd_data[x], x)

        for x in self.placeholders:
            try:
                value = int(mpd_data.get(x, ""))
                if x in ["elapsed", "duration", "time"]:
                    minutes, seconds = divmod(value, 60)
                    value = "{:d}:{:02d}".format(minutes, seconds)
                elif x == "pos":
                    value += 1
                mpd_data[x] = value
            except (KeyError, ValueError):
                pass

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, mpd_data),
        }

    def kill(self):
        self._get_mpd(disconnect=True)

    def on_click(self, event):
        self._get_mpd().pause()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
