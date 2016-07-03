# -*- coding: utf-8 -*-
"""
Display information about the current song and video playing on player with
mpris support.

Configuration parameters:
    button_play: mouse button to play the entry
    button_stop: mouse button to stop the player
    button_pause: mouse button to pause the player
    button_pause_toggle: mouse button to toggle between play and pause mode
    button_next: mouse button to play the next entry
    button_previous: mouse button to play the previous entry
    color_paused: text color when song is paused, defaults to color_degraded
    color_playing: text color when song is playing, defaults to color_good
    color_stopped: text color when song is stopped, defaults to color_bad
    format: see placeholders below
    format_video: see placeholders below, keep in mind that {artist} and {album}
            are empty
    format_error: define output if one or more informations couldn't read,
            keep in mind that some playceholders may be work
    format_none: define output if no player is running
    state_paused: text for placeholder {state} when song is paused
    state_playing: text for placeholder {state} when song is playing
    state_stopped: text for placeholder {state} when song is stopped
    shuffle_on: text for placeholder {shuffle} when shuffle mode is activated
    shuffle_off: text for placeholder {shuffle} when shuffle mode is deactivated
    loop_none: text for placeholder {loop} when loop mode is deactivated
    loop_track: text for placeholder {loop} when loop mode is in track mode
    loop_playlist: text for placeholder {loop} when loop mode is in playlist mode
    player_priority: priority of the players.
            Keep in mind that the state has a higher priority than
            player_priority. So when player_priority is "mpd,bomi" and mpd is
            paused and bomi is playing than bomi wins.

Format of status string placeholders:
    {player} show name of the player
    {state} playback status of the player
    {album} album name
    {artist} artiste name (first one)
    {title} name of the song
    {time} played time of the song
    {length} time duration of the song
    {shuffle} show if shuffle mode is activated or not
    {loop} show if loop mode is activated or not

i3status.conf example:

```
mpris {
    format = "{player}: {state} {artist} - {title} [{time} / {length}]"
    format_video = "{player}: {state} {title} [{time} / {length}]"
    format_none = "no player"
    format_error = "{player}: {state} Unknown"
    player_priority = "mpd,cantata,vlc,bomi"
}
```

Requires:
    pydbus

@author Pierre Guilbert, Jimmy Garpehäll, sondrele, Andrwe, Moritz Lüdecke
"""

from datetime import timedelta
from time import time, sleep
import re
from pydbus import SessionBus


SERVICE_BUS = 'org.mpris.MediaPlayer2'
INTERFACE = SERVICE_BUS + '.Player'
SERVICE_BUS_URL = '/org/mpris/MediaPlayer2'
SERVICE_BUS_REGEX = '^' + re.sub(r'\.', '\.', SERVICE_BUS) + '.'
UNKNOWN = 'Unknown'


def _get_time_str(microtime):
    time = str(timedelta(microseconds=microtime))
    if time[0] == '0':
        time = time[2:]
        if time[0] == '0':
            time = time[1:]

    return time


class Py3status:
    """
    """
    # available configuration parameters
    button_play = None
    button_stop = None
    button_pause = None
    button_pause_toggle = 1
    button_next = 4
    button_previous = 5
    color_paused = None
    color_playing = None
    color_stopped = None
    format = '{state} {artist} - {title}'
    format_video = '{state} {title}'
    format_error = '{state} Unknown'
    format_none = 'no player running'
    state_paused = '▮▮'
    state_playing = '▶'
    state_stopped = '◾'
    shuffle_off = '⇉'
    shuffle_on = '⤨'
    loop_none = '⇥'
    loop_track = '⟲'
    loop_playlist = '⟳'
    player_priority = None

    def _get_player(self, player):
        """
        Get dbus object
        """
        try:
            return self._dbus.get(SERVICE_BUS + '.%s' % player, SERVICE_BUS_URL)
        except Exception:
            return None

    def _get_state(self, player):
        """
        Get the state of a player
        """
        player = self._get_player(player)
        if player is None:
            return 'None'

        return player.PlaybackStatus

    def _detect_running_player(self):
        """
        Detect running player process, if any
        """
        players_paused = []
        players_stopped = []
        players = []
        players_prioritized = []

        _dbus = self._dbus.get('org.freedesktop.DBus')
        for player in _dbus.ListNames():
            if SERVICE_BUS in player:
                player = re.sub(r'%s' % SERVICE_BUS_REGEX, '', player)
                players.append(player)

        if self.player_priority is None:
            players_prioritized = players
        else:
            player_priority = self.player_priority.split(',')

            for player_name in player_priority:
                if player_name in players:
                    players.remove(player_name)
                    players_prioritized.append(player_name)
            players_prioritized += players

        for player_name in players_prioritized:
            player_state = self._get_state(player_name)

            if player_state == 'Playing':
                return player_name
            elif player_state == 'Paused':
                players_paused.append(player_name)
            elif player_state == 'Stopped':
                players_stopped.append(player_name)

        if players_paused:
            return players_paused[0]
        if players_stopped:
            return players_stopped[0]

        return 'None'

    def _get_text(self, i3s_config):
        """
        Get the current metadatas
        """
        is_video = False
        album = UNKNOWN
        artist = UNKNOWN
        state = UNKNOWN
        title = UNKNOWN
        time = '0'
        length = '0'
        shuffle = UNKNOWN
        loop = UNKNOWN

        if self._player is None:
            return (self.format_none, i3s_config['color_bad'])

        try:
            player = self._player.Identity
            metadata = self._player.Metadata
            playback_status = self._player.PlaybackStatus

            if playback_status.strip() == 'Playing':
                color = self.color_playing or i3s_config['color_good']
                state = self.state_playing
            elif playback_status.strip() == 'Paused':
                color = self.color_paused or i3s_config['color_degraded']
                state = self.state_paused
            else:
                color = self.color_stopped or i3s_config['color_bad']
                state = self.state_stopped

            shuffle = self.shuffle_on if self._player.Shuffle else self.shuffle_off

            loop_status = self._player.LoopStatus
            if loop_status.strip() == 'Track':
                loop = self.loop_track
            elif loop_status.strip() == 'Playlist':
                loop = self.loop_playlist
            else:
                loop = self.loop_none

            try:
                album = metadata.get('xesam:album')
                artist = metadata.get('xesam:artist')[0]
            except Exception:
                is_video = True

            title = metadata.get('xesam:title')

            _microtime = metadata.get('mpris:length')
            length = _get_time_str(_microtime)
            _microtime = self._player.Position
            time = _get_time_str(_microtime)

        except Exception:
            return (self.format_error.format(player=player,
                                             state=state,
                                             title=title,
                                             artist=artist,
                                             album=album,
                                             time=time,
                                             length=length,
                                             shuffle=shuffle,
                                             loop=loop),
                    i3s_config['color_bad'])

        if is_video:
            title = re.sub(r'\....$', '', title)
            return (self.format_video.format(player=player,
                                             state=state,
                                             title=title,
                                             time=time,
                                             length=length,
                                             shuffle=shuffle,
                                             loop=loop), color)
        else:
            return (self.format.format(player=player,
                                       state=state,
                                       title=title,
                                       artist=artist,
                                       album=album,
                                       time=time,
                                       length=length,
                                       shuffle=shuffle,
                                       loop=loop), color)

    def mpris(self, i3s_output_list, i3s_config):
        """
        Get the current "artist - title" and return it.
        """
        self._dbus = SessionBus()

        running_player = self._detect_running_player()
        self._player = self._get_player(running_player)

        (text, color) = self._get_text(i3s_config)
        response = {
            'cached_until': time() + i3s_config['interval'],
            'full_text': text,
            'color': color
        }

        return response

    def on_click(self, i3s_output_list, i3s_config, event):
        """
        Handles click events
        """
        button = event['button']

        if button == self.button_play:
            self._player.Play()
        elif button == self.button_stop:
            self._player.Stop()
        elif button == self.button_pause:
            self._player.Pause()
        elif button == self.button_pause_toggle:
            self._player.PlayPause()
        elif button == self.button_next:
            self._player.Next()
        elif button == self.button_previous:
            self._player.Previous()


if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    x = Py3status()
    config = {
        'interval': 5,
        'color_bad': '#FF0000',
        'color_degraded': '#FFFF00',
        'color_good': '#00FF00'
    }

    while True:
        print(x.mpris([], config))
        sleep(1)
