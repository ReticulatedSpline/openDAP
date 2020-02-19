import os
import vlc
import cfg
from glob import glob
from typing import NamedTuple
from mutagen.easyid3 import EasyID3 as ID3


class MediaItem(NamedTuple):
    index: int
    path: str


class PlaylistItem(NamedTuple):
    name: str
    is_dir: bool
    items: list


class Library:
    """handle scanning and storing media"""
    def __init__(self):
        self.music = list()
        self.playlists = self.scan_playlists()
        for ext in cfg.file_types:
            file = os.path.join(cfg.music_dir, ext)
            self.music.extend(glob(file))

    def scan_playlists(self):
        self.playlists = list()
        for root, dirs, files in os.walk(cfg.playlist_dir):
            for file in files:
                tracks = list()
                path = os.path.join(root, file)
                with open(path, 'r') as playlist:
                    for line in playlist:
                        tracks.append(line)
                item = PlaylistItem(file, False, tracks)
                self.playlists.append(item)


class Player:
    """track player state and wrap calls to VLC"""

    def __init__(self, library: Library):
        self.queue = list()
        self.vlc = vlc.Instance()
        self.player = self.vlc.media_player_new(library.music[0])
        self._update_song()

    def _get_id3(self, key: str):
        metadata = ID3(self.queue[0])
        return str(metadata[key]).strip('[\']')

    def _update_song(self):
        if self.queue:
            self.media = self.vlc.media_new(self.queue[0])
            self.media.get_mrl()
            self.player.set_media(self.media)

    def get_metadata(self):
        """Return a dictionary of title, artist, current/total runtimes."""
        if not self.queue:
            return None
        else:
            # default states when not playing a track are negative integers
            curr_time = self.player.get_time() / 1000   # time returned in ms
            if curr_time < 0:
                curr_time = 0
            run_time = self.player.get_length() / 1000
            if run_time < 0:
                run_time = 0
                playing = False
            else:
                playing = True
            info = {"playing": playing,
                    "title": self._get_id3('title'),
                    "artist": self._get_id3('artist'),
                    "curr_time": curr_time,
                    "run_time": run_time}
            return info

    def play(self):
        """start playing the current track."""
        self.player.play()

    def pause(self):
        """pause the current track. position is preserved."""
        self.player.pause()

    def skip_forward(self):
        """skip the the beginning of the next track and start playing."""
        # TODO

    def skip_back(self):
        """skip to the beginning of the last track and start playing."""
        # TODO
