from AudifyMusic.core.bot import Audify
from AudifyMusic.core.dir import dirr
from AudifyMusic.core.git import git
from AudifyMusic.core.userbot import Userbot
from AudifyMusic.misc import dbb, heroku

from .logging import LOGGER

dirr()
git()
dbb()
heroku()

app = Audify()
userbot = Userbot()


from .platforms import *

Apple = AppleAPI()
Carbon = CarbonAPI()
SoundCloud = SoundAPI()
Spotify = SpotifyAPI()
Resso = RessoAPI()
Telegram = TeleAPI()
YouTube = YouTubeAPI()
