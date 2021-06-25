from odoo import models, fields, api, tools
import logging
from PIL import Image
import numpy
import face_recognition

_logger = logging.getLogger(__name__)


class partner_images_inherit(models.Model):
    _inherit = 'res.partner'

    dl_image = fields.Image("DL Image", max_width=600, max_height=300, verify_resolution=True, store=True)
    dl_image_variant = fields.Image("Oriented DL Image", compute="_orient_dl_image")
    med_id_image = fields.Image("Med ID", max_width=600, max_height=300, verify_resolution=True)
    med_id_image_variant = fields.Image("Oriented Med Image", compute="_orient_dl_image")
    # internal_log = fields.Text("Internal Notes")

    @api.onchange("dl_image")
    def _orient_dl_image(self):
        for record in self:
            _logger.info("In _orient_dl_image function")
            if str(record.dl_image) == "False":
                # Bypass if no image exists when entering "edit" mode
                record.dl_image_variant = False
                _logger.info("DL image has not been loaded yet.")
            else:
                # If image exists and is vertically oriented, set correct
                # orientation by rotation by 90 degrees
                image = tools.base64_to_image(record.dl_image)
                _logger.info("Image type:" + str(type(image)))
                _logger.info("Image format:" + str(image.format))
                _logger.info("Image size:" + str(image.size))
                image_width = image.width
                _logger.info("Image width:" + str(image_width))
                image_height = image.height
                _logger.info("Image height:" + str(image_height))
                if image_width < image_height:
                    image = image.transpose(Image.ROTATE_90)
                    _logger.info("Image format:" + str(image.format))
                # If image exists and is horizontally oriented but flipped,
                # set correct orientation by rotation by 180 degrees.
                # This won't work in all cases (e.g., Texas DL), but fine
                # tuning the threshold may help (150 seems to work in most cases)
                threshold = 175
                image = image.resize((600, 400))
                _logger.info("Image format:" + str(image.format))
                image_width = image.width
                _logger.info("Image width:" + str(image_width))
                image_height = image.height
                _logger.info("Image height:" + str(image_height))
                height_adj = image_height / 5
                bottom_box_height_start = image_height - height_adj
                top_box = (0, 0, image_width, height_adj)
                bottom_box = (0, bottom_box_height_start, image_width, image_height)
                top_cropped_image = image.crop(top_box)
                bottom_cropped_image = image.crop(bottom_box)
                top_cropped_image = top_cropped_image.convert("L")
                bottom_cropped_image = bottom_cropped_image.convert("L")
                top_pixels = top_cropped_image.getdata()
                bottom_pixels = bottom_cropped_image.getdata()
                _logger.info("top_pixels:" + str(top_pixels))
                _logger.info("bottom_pixels:" + str(bottom_pixels))
                # Threshold is 0 (black) to 255 (white).  Anything under this threshold
                # is considered black and anything above is consider white.
                top_total = 0
                for top_pixel in top_pixels:
                    if top_pixel < threshold:
                        top_pixel = 0
                    else:
                        top_pixel = 255
                    top_total += top_pixel
                _logger.info("top_total:" + str(top_total))
                bottom_total = 0
                for bottom_pixel in bottom_pixels:
                    if bottom_pixel < threshold:
                        bottom_pixel = 0
                    else:
                        bottom_pixel = 255
                    bottom_total += bottom_pixel
                _logger.info("bottom_total:" + str(bottom_total))
                # If top has more white than bottom, it indicates the DL image is upside
                # down. Usually the bottom of DL has more white space than the header,
                # but this is not always the case and may have to be revisited for specific states.
                # Georgia would be an example of a header that has more white space than the bottom.
                if top_total > bottom_total:
                    image = image.transpose(Image.ROTATE_180)
                    _logger.info("Image format:" + str(image.format))
                record.dl_image = tools.image_to_base64(image, format='PNG')
                record.dl_image_variant = record.dl_image

                # Update thumbnail contact image if it does not exist
                # _logger.info("The value of image_1920:" + str(record.image_1920))
                if record.image_1920:
                    # Bypass if thumbnail image already exists
                    # record.image_1920_variant = record.image_1920
                    _logger.info("Thumbnail contact image exists")
                else:
                    _logger.info("Thumbnail contact image does not exist; adding it")
                    # Find the image on the Driver's License to save as customer logo image
                    pixel_image_array = numpy.array(image)
                    _logger.info("Image type:" + str(type(pixel_image_array)))
                    face_locations = face_recognition.face_locations(pixel_image_array)
                    if len(face_locations) > 0:
                        _logger.info("Faces found:" + str(len(face_locations)))
                        # Find all the face locations
                        largest_face_image = 0
                        index = 0
                        face_index = 0
                        for face_location in face_locations:
                            top, right, bottom, left = face_location
                            _logger.info("A face is located at pixel location Top:" + str(top) +
                                         ", Left:" + str(left) + ", Bottom:" + str(bottom) +
                                         ", Right:" + str(right))
                            current_face_size = right - left
                            if current_face_size > largest_face_image:
                                largest_face_image = current_face_size
                                face_index = index
                            index += 1
                        # The largest face image has been determined.
                        top, right, bottom, left = face_locations[face_index]
                        _logger.info("Largest face image is located at pixel location Top:" +
                                     str(top) + ", Left:" + str(left) + ", Bottom:" +
                                     str(bottom) + ", Right:" + str(right))
                        # Since face_recognition crops only the face, expand the image
                        # area to get more of the head and hair
                        top = int(top - top / 3)
                        bottom += 20
                        left -= 20
                        right += 20
                        face_image = pixel_image_array[top:bottom, left:right]
                        pil_image = Image.fromarray(face_image)
                        # Increase headshot and keep aspect ratio
                        height = 300
                        wpercent = (height / float(pil_image.size[1]))
                        width = int(pil_image.size[0] * float(wpercent))
                        pil_image = pil_image.resize((width, height), Image.ANTIALIAS)
                        record.image_1920 = tools.image_to_base64(pil_image, format='PNG')
                        # _logger.info(str(image_1920))
                    else:
                        _logger.info("No faces found on DL ID")

    @api.onchange("med_id_image")
    def _orient_med_image(self):
        for record in self:
            _logger.info("In _orient_med_image function")
            if str(record.med_id_image) == "False":
                # Bypass if no image exists when entering "edit" mode
                record.med_id_image_variant = False
                _logger.info("Med ID image has not been loaded yet.")
            else:
                # If image exists and is vertically oriented, set correct
                # orientation by rotation by 90 degrees
                med_image = tools.base64_to_image(record.med_id_image)
                _logger.info("Med image type:" + str(type(med_image)))
                _logger.info("Med image format:" + str(med_image.format))
                _logger.info("Med image size:" + str(med_image.size))
                med_image_width = med_image.width
                _logger.info("Med image width:" + str(med_image_width))
                med_image_height = med_image.height
                _logger.info("Med image height:" + str(med_image_height))
                if med_image_width < med_image_height:
                    med_image = med_image.transpose(Image.ROTATE_90)
                # If image exists and is horizontally oriented but flipped,
                # set correct orientation by rotation by 180 degrees.
                # This won't work in all cases (e.g., Texas DL), but fine
                # tuning the threshold may help (150 seems to work in most cases)
                threshold = 175
                med_image = med_image.resize((600, 400))
                med_image_width = med_image.width
                _logger.info("Med image width:" + str(med_image_width))
                med_image_height = med_image.height
                _logger.info("Med image height:" + str(med_image_height))
                med_height_adj = med_image_height / 5
                med_bottom_box_height_start = med_image_height - med_height_adj
                med_top_box = (0, 0, med_image_width, med_height_adj)
                med_bottom_box = (0, med_bottom_box_height_start, med_image_width, med_image_height)
                med_top_cropped_image = med_image.crop(med_top_box)
                med_bottom_cropped_image = med_image.crop(med_bottom_box)
                med_top_cropped_image = med_top_cropped_image.convert("L")
                med_bottom_cropped_image = med_bottom_cropped_image.convert("L")
                med_top_pixels = med_top_cropped_image.getdata()
                med_bottom_pixels = med_bottom_cropped_image.getdata()
                _logger.info("Med ID top_pixels:" + str(med_top_pixels))
                _logger.info("Med ID bottom_pixels:" + str(med_bottom_pixels))
                # Threshold is 0 (black) to 255 (white).  Anything under this threshold
                # is considered black and anything above is consider white.
                med_top_total = 0
                for med_top_pixel in med_top_pixels:
                    if med_top_pixel < threshold:
                        med_top_pixel = 0
                    else:
                        med_top_pixel = 255
                    med_top_total += med_top_pixel
                _logger.info("Med ID top_total:" + str(med_top_total))
                med_bottom_total = 0
                for med_bottom_pixel in med_bottom_pixels:
                    if med_bottom_pixel < threshold:
                        med_bottom_pixel = 0
                    else:
                        med_bottom_pixel = 255
                    med_bottom_total += med_bottom_pixel
                _logger.info("Med ID bottom_total:" + str(med_bottom_total))
                # If top has more white than bottom, it indicates the DL image is upside
                # down. Usually the bottom of DL has more white space than the header,
                # but this is not always the case and may have to be revisited for specific states.
                # Georgia would be an example of a header that has more white space than the bottom.
                if med_top_total > med_bottom_total:
                    med_image = med_image.transpose(Image.ROTATE_180)
                record.med_id_image = tools.image_to_base64(med_image, format='PNG')
                record.med_id_image_variant = record.med_id_image
