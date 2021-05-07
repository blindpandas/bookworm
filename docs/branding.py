# coding: utf-8

import shutil
from pathlib import Path
from invoke import task
from PIL import Image
from PIL.ImageColor import getrgb


COLOR_BLACK = tuple(range(0, 50))
COLOR_WHITE = tuple(range(155, 255))
LOGOS_SRC= Path.cwd() / 'theme' / 'branding'
LOGOS_DST = Path.cwd() / 'theme' / 'branding' / 'colored'
LOGO_CONTENT_DIR = Path.cwd() / "content" / "static" / "images"
LOGO_SIZES = (
    ("", "ico", 32),
    ("16x16", "png", 16),
    ("32x32", "png", 32),
    ("64x64", "png", 64),
    ("128x128", "png", 128),
    ("180x180", "png", 180),
    ("256x256", "png", 256),
    ("512x512", "png", 512),
)
APP_LOGOS_SRC = LOGOS_SRC / "apps"
APP_LOGOS_DST = LOGOS_DST / "apps"
APP_LOGOS_COLORS = {
    'bookworm': ('#77216F', '#AEA79F'),
}

def recolor_image(image, old_color_range, color):
    new_color = getrgb(color)
    img = image.convert('RGBA')
    data = img.getdata()
    new_data = []
    for item in data:
        if (item[-1] != 0) and (item[0] in old_color_range):
            new_data.append(new_color)
        else:
            new_data.append(item)
    img.putdata(new_data)
    return img


@task
def recolor_main_logo(c, color="#325d88"):
    print("Recoloring main logo.")
    LOGOS_DST.mkdir(parents=True, exist_ok=True)
    recolor_image(Image.open(LOGOS_SRC / "logo.png"), COLOR_BLACK, color).save(LOGOS_DST / "logo.png")
    print("Done recoloring the logo")


@task
def app_logo(c):
    APP_LOGOS_DST.mkdir(parents=True, exist_ok=True)
    for app_logo in APP_LOGOS_SRC.glob("*.png"):
        app_name = app_logo.stem
        if app_name not in APP_LOGOS_COLORS:
            raise ValueError(f"Unknown app logo: '{app_name}'")
        black, white = APP_LOGOS_COLORS[app_name]
        print(f"Recoloring app logo: {app_logo.name}")
        print(f"Replacing white with '{white}' and black with '{black}'")
        img = recolor_image(Image.open(app_logo), COLOR_BLACK, black)
        recolor_image(img, COLOR_WHITE, white)
        img.save(APP_LOGOS_DST / app_logo.name )
        print(f"Saved recolored app logo: {app_logo}")


@task(pre=(recolor_main_logo, app_logo,))
def branding(c):
    print("Saving logos with different sizes")
    for logo in LOGOS_DST.rglob("*.png"):
        img = Image.open(logo)
        for suffix, ext, size in LOGO_SIZES:
            filename = f"{logo.stem}{suffix}.{ext}"
            img.resize((size, size)).save(str(LOGO_CONTENT_DIR / filename))
            print(f"Saved logo '{logo.stem}' with size: {size}x{size}")
    print("Branding task finished.")
