import os
import vlc
import cfg
from glob import glob
from typing import NamedTuple
from mutagen.easyid3 import EasyID3 as ID3


class DiskItem(NamedTuple):
    is_dir: bool
    path: str


class Library:
    """handle scanning and storing media"""
    def __init__(self):
        self.music = list()
        for ext in cfg.music_formats:
            file = os.path.join(cfg.music_dir, '*' + ext)
            self.music.extend(glob(file))

    def get_disk_items(self, root: str):
        items = list()
        for item in os.listdir(root):
            abs_path = os.path.join(root, item)
            ext = os.path.splitext(abs_path)[-1]
            if os.path.isfile(abs_path):
                if ext and (ext in cfg.music_formats or ext in cfg.playlist_formats):
                    items.append(DiskItem(False, abs_path))
            elif os.path.isdir(abs_path):
                items.append(DiskItem(True, abs_path))
        return items


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
