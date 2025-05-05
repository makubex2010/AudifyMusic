import os
import re
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps
from youtubesearchpython.__future__ import VideosSearch
from config import FAILED

# Constants
CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

PANEL_W, PANEL_H = 763, 545
PANEL_X = (1280 - PANEL_W) // 2
PANEL_Y = 88
TRANSPARENCY = 150  # Adjusted transparency for better panel visibility
INNER_OFFSET = 36

THUMB_W, THUMB_H = 542, 273
THUMB_X = PANEL_X + (PANEL_W - THUMB_W) // 2
THUMB_Y = PANEL_Y + INNER_OFFSET

TITLE_X = 377
META_X = 377
TITLE_Y = THUMB_Y + THUMB_H + 10
META_Y = TITLE_Y + 45

BAR_X, BAR_Y = 388, META_Y + 45
BAR_RED_LEN = 280
BAR_TOTAL_LEN = 480

ICONS_W, ICONS_H = 415, 45
ICONS_X = PANEL_X + (PANEL_W - ICONS_W) // 2
ICONS_Y = BAR_Y + 48

MAX_TITLE_WIDTH = 580

# Adjusted color scheme based on the example images
TEXT_COLOR_PRIMARY = (255, 255, 255)  # White text for titles
TEXT_COLOR_SECONDARY = (192, 192, 192)  # Light gray for secondary text
PROGRESS_COLOR = (255, 0, 0)  # Red for progress bar
PROGRESS_BG_COLOR = (160, 160, 160)  # Gray for remaining progress
PANEL_COLOR = (30, 30, 30)  # Slightly darker gray for panel background

def trim_to_width(text: str, font: ImageFont.FreeTypeFont, max_w: int) -> str:
    ellipsis = "…"
    if font.getlength(text) <= max_w:
        return text
    for i in range(len(text) - 1, 0, -1):
        if font.getlength(text[:i] + ellipsis) <= max_w:
            return text[:i] + ellipsis
    return ellipsis

async def get_thumb(videoid: str) -> str:
    cache_path = os.path.join(CACHE_DIR, f"{videoid}_v4.png")
    if os.path.exists(cache_path):
        return cache_path

    # YouTube video data fetch
    results = VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1)
    try:
        results_data = await results.next()
        result_items = results_data.get("result", [])
        if not result_items:
            raise ValueError("No results found.")
        data = result_items[0]
        title = re.sub(r"\W+", " ", data.get("title", "Unsupported Title")).title()
        thumbnail = data.get("thumbnails", [{}])[0].get("url", FAILED)
        duration = data.get("duration")
        views = data.get("viewCount", {}).get("short", "Unknown Views")
    except Exception:
        title, thumbnail, duration, views = "Unsupported Title", FAILED, None, "Unknown Views"

    is_live = not duration or str(duration).strip().lower() in {"", "live", "live now"}
    duration_text = "Live" if is_live else duration or "Unknown Mins"

    # Download thumbnail
    thumb_path = os.path.join(CACHE_DIR, f"thumb{videoid}.png")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail) as resp:
                if resp.status == 200:
                    async with aiofiles.open(thumb_path, "wb") as f:
                        await f.write(await resp.read())
    except Exception:
        return FAILED

    # Create base image
    base = Image.open(thumb_path).resize((1280, 720)).convert("RGBA")
    
    # Apply extreme blur like in the second image (40 instead of 25)
    bg = base.filter(ImageFilter.GaussianBlur(40))
    
    # Make background extremely bright - 1.3 instead of 0.7
    bg = ImageEnhance.Brightness(bg).enhance(1.3)
    
    # Frosted glass panel - slightly darker than before
    panel_area = bg.crop((PANEL_X, PANEL_Y, PANEL_X + PANEL_W, PANEL_Y + PANEL_H))
    overlay = Image.new("RGBA", (PANEL_W, PANEL_H), (*PANEL_COLOR, TRANSPARENCY))
    frosted = Image.alpha_composite(panel_area, overlay)
    mask = Image.new("L", (PANEL_W, PANEL_H), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, PANEL_W, PANEL_H), 40, fill=255)  # Slightly reduced radius
    bg.paste(frosted, (PANEL_X, PANEL_Y), mask)

    # Draw details
    draw = ImageDraw.Draw(bg)
    try:
        title_font = ImageFont.truetype("AudifyMusic/assets/font2.ttf", 32)
        regular_font = ImageFont.truetype("AudifyMusic/assets/font.ttf", 18)
    except OSError:
        title_font = regular_font = ImageFont.load_default()

    # Create rounded thumbnail
    thumb = base.resize((THUMB_W, THUMB_H))
    tmask = Image.new("L", thumb.size, 0)
    ImageDraw.Draw(tmask).rounded_rectangle((0, 0, THUMB_W, THUMB_H), 20, fill=255)
    bg.paste(thumb, (THUMB_X, THUMB_Y), tmask)

    # Text with new colors
    draw.text((TITLE_X, TITLE_Y), trim_to_width(title, title_font, MAX_TITLE_WIDTH), 
              fill=TEXT_COLOR_PRIMARY, font=title_font)
    draw.text((META_X, META_Y), f"YouTube | {views}", 
              fill=TEXT_COLOR_SECONDARY, font=regular_font)

    # Progress bar with new colors
    draw.line([(BAR_X, BAR_Y), (BAR_X + BAR_RED_LEN, BAR_Y)], 
              fill=PROGRESS_COLOR, width=6)
    draw.line([(BAR_X + BAR_RED_LEN, BAR_Y), (BAR_X + BAR_TOTAL_LEN, BAR_Y)], 
              fill=PROGRESS_BG_COLOR, width=5)
    draw.ellipse([(BAR_X + BAR_RED_LEN - 7, BAR_Y - 7), 
                 (BAR_X + BAR_RED_LEN + 7, BAR_Y + 7)], fill=PROGRESS_COLOR)

    # Time indicators with new colors
    draw.text((BAR_X, BAR_Y + 15), "00:00", 
              fill=TEXT_COLOR_SECONDARY, font=regular_font)
    end_text = "Live" if is_live else duration_text
    draw.text((BAR_X + BAR_TOTAL_LEN - (90 if is_live else 60), BAR_Y + 15), 
              end_text, fill=PROGRESS_COLOR if is_live else TEXT_COLOR_SECONDARY, font=regular_font)

    # Icons - with proper coloring
    icons_path = "AudifyMusic/assets/play_icons.png"
    if os.path.isfile(icons_path):
        ic = Image.open(icons_path).resize((ICONS_W, ICONS_H)).convert("RGBA")
        # Apply white tint to icons to match the theme
        r, g, b, a = ic.split()
        white_ic = Image.merge("RGBA", (r.point(lambda *_: 255), 
                                       g.point(lambda *_: 255), 
                                       b.point(lambda *_: 255), a))
        bg.paste(white_ic, (ICONS_X, ICONS_Y), white_ic)

    # Cleanup and save
    try:
        os.remove(thumb_path)
    except OSError:
        pass

    bg.save(cache_path)
    return cache_path
