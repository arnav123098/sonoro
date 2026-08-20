import subprocess
from yt_dlp import YoutubeDL

class MusicPlayer:
    player_path = r"C:\Program Files\MPV Player\mpv.exe"
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['android'],
                'player_skip': ['webpage', 'configs']
            }
        }
    }

    def __init__(self):
        self.player = None

    def play(self, query):
        print("Extracting stream URL...")

        with YoutubeDL(MusicPlayer.ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)
            stream_url = info['entries'][0]['url']
            title = info['entries'][0]['title']

        print(f"Now playing {title}...")

        self.player = subprocess.Popen([
            MusicPlayer.player_path,
            "--no-video",
            "--no-terminal",
            "--force-window=no",
            stream_url
        ])

        return {'event_name': 'playing song', 'content': f"Now playing {title}..."}

    def stop(self):
        self.player.terminate()
        self.player = None

        return {'event_name': 'stopped song', 'content': 'stopped the current song'}

    def cleanup(self):
        if self.player is not None:
            self.player.kill()
            self.player = None
