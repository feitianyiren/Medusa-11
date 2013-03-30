# User configured settings for Medusa.

directories = {"Film", "Television"}

video_extensions = {"asf",
                    "avi",
                    "divx",
                    "flv",
                    "m4v",
                    "mkv",
                    "mp4",
                    "mpg",
                    "ogm",
                    "m2ts"}

audio_extensions = {"mp3", "m4a"}

ignore_files = {"Thumbs.db"}

port = 8822 # The port for Receivers and the Webmote to communicate on.

# Internal configurations.

from socket import gethostname
hostname = gethostname()

from os.path import dirname
database_file = dirname(__file__) + "/files/medusa.db"
log_file = dirname(__file__) + "/files/medusa.log"

from sys import platform
