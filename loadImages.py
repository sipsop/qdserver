import os
import sys
import glob
import shutil
import filecmp
import subprocess

from qdserver import model

try:
    os.mkdir('images')
except FileExistsError as e:
    pass


def process_images(resize=False):
    images = (
        glob.glob('images/*.jpg') +
        glob.glob('images/*.png')
    )

    for filename in images:
        _, image = os.path.split(filename)
        shutil.copyfile(filename, image)
        resize_image(image)

def process_menu_images(resize=False):
    images = (
        glob.glob('MenuImages/*.jpg')   +
        glob.glob('MenuImages/*.png')   +
        glob.glob('MenuImages/*/*.jpg') +
        glob.glob('MenuImages/*/*.png')
    )

    for filename in images:
        _, image = os.path.split(filename)
        image = image.strip()
        item_id, _ = os.path.splitext(image)
        dest_image = os.path.join('static', image)
        same_image = os.path.exists(dest_image) and filecmp.cmp(filename, dest_image)
        shutil.copyfile(filename, dest_image)
        result = model.run(
            model.MenuItemDefs
                .get(item_id)
                .update({'images': ['/static/' + image]})
        )
        print(item_id, list(filter(result.get, result)))
        if resize and not same_image:
            resize_image(dest_image)


def resize_image(image):
    # convert dragon.gif    -resize 64x64  resize_dragon.gif
    # iphone 5 resolution = 320x568
    print("resizing...", image)
    dest, ext = os.path.splitext(image)
    # To resize exactly, use '32x32!'
    subprocess.check_call(['convert', image, '-resize', '32x32', dest + '-micro' + ext])
    subprocess.check_call(['convert', image, '-resize', '64x64', dest + '-tiny' + ext])
    subprocess.check_call(['convert', image, '-resize', '160x284', dest + '-small' + ext])
    subprocess.check_call(['convert', image, '-resize', '320x568', dest + '-medium' + ext])
    subprocess.check_call(['convert', image, '-resize', '640x1136', dest + '-large' + ext])


def main(resize=False):
    process_images(resize=resize)
    process_menu_images(resize=resize)

main(resize='--resize' in sys.argv)
