# coding: utf-8

import cv2
import numpy as np
import math
import re
import pytesseract


# function to resize the image without distortion i.e resizing with ratios
def image_resize(image: np.ndarray, width=None, height=None, inter=cv2.INTER_CUBIC):
    # initialize the dimensions of the image to be resized and
    # grab the image size
    dim = None
    (h, w) = image.shape[:2]

    # if both the width and height are None, then return the
    # original image
    if width is None and height is None:
        return image

    # check to see if the width is None
    if width is None:
        # calculate the ratio of the height and construct the
        # dimensions
        r = height / float(h)
        dim = (int(w * r), height)

    # otherwise, the height is None
    else:
        # calculate the ratio of the width and construct the
        # dimensions
        r = width / float(w)
        dim = (width, int(h * r))

    # resize the image
    resized = cv2.resize(image, dim, interpolation=inter)

    # return the resized image
    return resized


# function to remove shadows from the image
def remove_shadows(image: np.ndarray):
    # split the image channels into b,g,r
    b = image[:, :, 0]
    g = image[:, :, 1]
    r = image[:, :, 2]
    rgb_planes = [b, g, r]

    # iniatialising the final shadow free normalised image list for planes
    result_norm_planes = []

    # removing the shadows in individual planes
    for plane in rgb_planes:
        # dialting the image to spead the text to the background
        dilated_image = cv2.dilate(plane, np.ones((7, 7), np.uint8))

        # blurring the image to get the backround image
        bg_image = cv2.medianBlur(dilated_image, 21)

        # subtracting the plane-background from the image-plane
        diff_image = 255 - cv2.absdiff(plane, bg_image)

        # normalisng the plane
        norm_image = cv2.normalize(
            diff_image,
            None,
            alpha=0,
            beta=255,
            norm_type=cv2.NORM_MINMAX,
            dtype=cv2.CV_8UC1,
        )

        # appending the plane to the final planes list
        result_norm_planes.append(norm_image)

    # merging the shadow-free planes into one image
    normalised_image = cv2.merge(result_norm_planes)

    # returning the normalised image
    return normalised_image


# function to remove shadows from the image
def de_shadow(image):
    # splitting the image into channels
    bA = image[:, :, 0]
    gA = image[:, :, 1]
    rA = image[:, :, 2]

    # dialting the image channels individually to spead the text to the background
    dilated_image_bB = cv2.dilate(bA, np.ones((7, 7), np.uint8))
    dilated_image_gB = cv2.dilate(gA, np.ones((7, 7), np.uint8))
    dilated_image_rB = cv2.dilate(rA, np.ones((7, 7), np.uint8))

    # blurring the image to get the backround image
    bB = cv2.medianBlur(dilated_image_bB, 21)
    gB = cv2.medianBlur(dilated_image_gB, 21)
    rB = cv2.medianBlur(dilated_image_rB, 21)

    # blend_modes library works with 4 channels, the last channel being the alpha channel
    # so we add one alpha channel to our image and the background image each
    image = np.dstack((image, np.ones((image.shape[0], image.shape[1], 1)) * 255))
    image = image.astype(float)
    dilate = [bB, gB, rB]
    dilate = cv2.merge(dilate)
    dilate = np.dstack((dilate, np.ones((image.shape[0], image.shape[1], 1)) * 255))
    dilate = dilate.astype(float)

    # now we divide the image with the background image
    # without rescaling i.e scaling factor = 1.0
    blend = divide(image, dilate, 1.0)
    blendb = blend[:, :, 0]
    blendg = blend[:, :, 1]
    blendr = blend[:, :, 2]
    blend_planes = [blendb, blendg, blendr]
    blend = cv2.merge(blend_planes)
    # blend = blend*0.85
    blend = np.uint8(blend)

    # returning the shadow-free image
    return blend


# function to get the median of all the angles of the text words in the image
def get_median_angle(binary_image):
    # applying morphological transformations on the binarised image
    # to eliminate maximum noise and obtain text ares only
    erode_otsu = cv2.erode(binary_image, np.ones((7, 7), np.uint8), iterations=1)
    negated_erode = ~erode_otsu
    opening = cv2.morphologyEx(
        negated_erode, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8), iterations=2
    )
    double_opening = cv2.morphologyEx(
        opening, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8), iterations=5
    )
    double_opening_dilated_3x3 = cv2.dilate(
        double_opening, np.ones((3, 3), np.uint8), iterations=4
    )

    # finding the contours in the morphologically transformed image
    contours_otsu, _ = cv2.findContours(
        double_opening_dilated_3x3, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
    )

    # iniatialising the empty angles list to collet the angles of each contour
    angles = []

    # obtaining the angles of each contour using a for loop
    for cnt in range(len(contours_otsu)):
        # the last output of the cv2.minAreaRect() is the orientation of the contour
        rect = cv2.minAreaRect(contours_otsu[cnt])

        # appending the angle to the angles-list
        angles.append(rect[-1])

    # finding the median of the collected angles
    angles.sort()
    median_angle = np.median(angles)

    # returning the median angle
    return median_angle


# funtion to correct the median-angle to give it to the cv2.warpaffine() function
def corrected_angle(angle):
    if 0 <= angle <= 90:
        corrected_angle = angle - 90
    elif -45 <= angle < 0:
        corrected_angle = angle - 90
    elif -90 <= angle < -45:
        corrected_angle = 90 + angle
    return corrected_angle


# function to rotate the image
def rotate(image: np.ndarray, angle, background_color):
    old_width, old_height = image.shape[:2]
    angle_radian = math.radians(angle)
    width = abs(np.sin(angle_radian) * old_height) + abs(
        np.cos(angle_radian) * old_width
    )
    height = abs(np.sin(angle_radian) * old_width) + abs(
        np.cos(angle_radian) * old_height
    )
    image_center = tuple(np.array(image.shape[1::-1]) / 2)
    rot_mat = cv2.getRotationMatrix2D(image_center, angle, 1.0)
    rot_mat[1, 2] += (width - old_width) / 2
    rot_mat[0, 2] += (height - old_height) / 2
    return cv2.warpAffine(
        image,
        rot_mat,
        (int(round(height)), int(round(width))),
        borderValue=background_color,
    )


# getting the white background binarised image
def get_otsu(image):
    # binarizing the image using otsu's binarization method
    _, otsu = cv2.threshold(image, 180, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return otsu


# function to correct the 2d skew of the image
def correct_skew(image):
    # resizing the image to 2000x3000 to sync it with
    #  the morphological tranformations in get_median_angle() function
    image_resized = image_resize(image, 2000, 3000)

    otsu = get_otsu(image_resized)
    # find median of the angles
    median_angle = get_median_angle(otsu)

    # rotating the image
    rotated_image = rotate(image, corrected_angle(median_angle), (255, 255, 255))
    # after rotating the image using above function, the image is rotated
    # such that the text is alligned along any one of the 4 axes i.e 0, 90, 180 or 270
    # so we are going to use tesseract's image_to_osd function to set it right

    while True:

        # tesseract's image_to_osd() function works best with images with more visible characters.
        # so we are binarizing the image before passing it to the function
        # otherwise, due to less clarity in the image tesseract raises an expection: 0 dpi exception

        otsu = get_otsu(rotated_image)
        osd_rotated_image = pytesseract.image_to_osd(otsu)

        # using regex we search for the angle(in string format) of the text
        angle_rotated_image = re.search("(?<=Rotate: )\d+", osd_rotated_image).group(0)

        if angle_rotated_image == "0":
            # no further rotation
            rotated_image = rotated_image
            # break the loop once we get the correctly deskewed image
            break
        elif angle_rotated_image == "90":
            rotated_image = rotate(rotated_image, 90, (255, 255, 255))
            continue
        elif angle_rotated_image == "180":
            rotated_image = rotate(rotated_image, 180, (255, 255, 255))
            continue
        elif angle_rotated_image == "270":
            rotated_image = rotate(rotated_image, 90, (255, 255, 255))
            continue
    return rotated_image
