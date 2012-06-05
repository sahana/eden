# -*- coding: utf-8 -*-

""" Sahana Eden Image Model

    This is used to store modified copies of images held in other tables.
    The modifications can be:
     * different file type (bmp, jpeg, gif, png etc)
     * different size (thumbnails)

    @copyright: 2009-2012 (c) Sahana Software Foundation
    @license: MIT

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.
"""

__all__ = ["S3Image",
           # Representation Methods
           "image_represent",
           # Utility Methods
           "image_modify",
           "image_resize",
           "image_size",
           "image_delete_all",
           "image_format",
          ]

import os

from gluon import *
from gluon.dal import Row
from gluon.storage import Storage

from ..s3 import *

# Import the specialist libraries
try:
    from PIL import Image
    from PIL import ImageOps
    from PIL import ImageStat
    PILImported = True
except(ImportError):
    try:
        import Image
        import ImageOps
        import ImageStat
        PILImported = True
    except(ImportError):
        PILImported = False

# =============================================================================
class S3Image(S3Model):
    """ Image Model """

    names = ["image_library",
            ]

    def model(self):

        db = current.db
        T = current.T
        s3 = current.response.s3
        define_table = self.define_table

        UNKNOWN_OPT = current.messages.UNKNOWN_OPT

        tablename = "image_library"

        table = define_table(tablename,
                             # Original image file name
                             Field("original_name"),
                             # New image file name
                             Field("new_name",
                                   "upload",
                                   autodelete=True,
                                   ),
                             # New file format name
                             Field("format"),
                             # New requested file dimensions
                             Field("width",
                                   "integer",
                                  ),
                             Field("height",
                                   "integer",
                                  ),
                             # New actual file dimensions
                             Field("actual_width",
                                   "integer",
                                  ),
                             Field("actual_height",
                                   "integer",
                                  )
                            )

    # -------------------------------------------------------------------------

def image_represent(image_name,
                    format = None,
                    size = (),
                   ):
    """
        Get the image that matches the required image type

        @param image_name: the name of the original image
        @param format:     the file format required
        @param size:       the size of the image (width, height)
    """

    db = current.db
    s3db = current.s3db

    table = s3db.image_library
    query = (table.original_name == image_name)
    if format:
        query = query & (table.format == format)
    if size:
        query = query & (table.width == size[0]) & (table.height == size[1]) 
    image = db(query).select(limitby=(0, 1)).first()
    if image:
        return image.new_name
    else:
        return image_name

def image_modify(image_file,
                 image_name,
                 original_name,
                 size = (None, None),
                 to_format = None,
                ):
    """
        Resize the image passed in and store on the table

        @param image_file:    the image stored in a file object
        @param image_name:    the name of the original image
        @param original_name: the original name of the file
        @param size:          the required size of the image (width, height)
        @param to_format:     the format of the image (jpeg, bmp, png, gif, etc.)
    """
    if PILImported:
        from tempfile import TemporaryFile
        s3db = current.s3db
        table = s3db.image_library

        fileName, fileExtension = os.path.splitext(original_name)

        image_file.seek(0)
        im = Image.open(image_file)
        thumb_size = []
        if size[0] == None:
            thumb_size.append(im.size[0])
        else:
            thumb_size.append(size[0])
        if size[1] == None:
            thumb_size.append(im.size[1])
        else:
            thumb_size.append(size[1])
        im.thumbnail(thumb_size, Image.ANTIALIAS)

        if to_format:
            if to_format.upper() == "JPG":
                to_format = "JPEG"
            elif to_format.upper() == "BMP":
                im = im.convert("RGB")
        else:
            to_format = fileExtension[1:]
        save_im_name = "%s.%s" % (fileName, to_format)
        tempFile = TemporaryFile()
        im.save(tempFile,to_format)
        tempFile.seek(0)
        newfile = table.new_name.store(tempFile,
                                       save_im_name,
                                       table.new_name.uploadfolder
                                      )
        # rewind the original file so it can be read, if required
        image_file.seek(0)
        image_id = table.insert(original_name = image_name,
                                new_name = newfile,
                                format = to_format,
                                width = size[0],
                                height = size[1],
                                actual_width = im.size[0],
                                actual_height = im.size[1],
                               )
        return True
    else:
        return False

def image_resize(image_file,
                 image_name,
                 original_name,
                 size,
                ):
    """
        Resize the image passed in and store on the table

        @param image_file:    the image stored in a file object
        @param image_name:    the name of the original image
        @param original_name: the original name of the file
        @param size:          the required size of the image (width, height)
    """
    return image_modify (image_file,
                         image_name,
                         original_name,
                         size = size
                        )

def image_size(image_name, size):
    db = current.db
    s3db = current.s3db

    table = s3db.image_library
    query = (table.new_name == image_name)
    image = db(query).select(limitby=(0, 1)).first()
    if image:
        return (image.actual_width, image.actual_height)
    else:
        return size

def image_delete_all(original_image_name):
    """
        Method to delete all the images that belong to 
        the original file.
    """
    if deployment_settings.get_security_archive_not_delete():
       return 
    db = current.db
    table = current.s3db.image_library
    query = (table.original_name == original_image_name)
    set = db(query)
    set.delete_uploaded_files()
    set.delete()
    
def image_format(image_file,
                 image_name,
                 original_name,
                 to_format,
                ):
    """
        Change the file format of the image passed in and store on the table

        @param image_file:    the image stored in a file object
        @param image_name:    the name of the original image
        @param original_name: the original name of the file
        @param to_format:     the format of the image (jpeg, bmp, png, gif, etc.)
    """
    return image_modify (image_file,
                         image_name,
                         original_name,
                         to_format = to_format
                        )
