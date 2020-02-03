import os
import urllib2

from PIL import Image

from common_libs import files


# Constants
#=======================================================================================================================
i_WIDTH = 320
df_ASPECT_RATIOS = {
    u'gbo':     1.1111,  # 160/144
    u'gba-crt': 1.5000,  # 240/160
    u'gbc':     1.1111,  # 160/144
    u'lnx':     1.5686,  # 160/102
    u'ngp':     1.0526,  # 160/152
    u'ngc':     1.0526,  # 160/152
    }


# Classes
#=======================================================================================================================
class Downloader(object):
    def __init__(self):
        pass

    def _download(self, pu_url, pu_local_path):
        """

        :param pu_url:
        :param pu_path:
        :return:
        """
        b_download = False

        try:
            o_data = urllib2.urlopen(pu_url).read()
        except (urllib2.HTTPError, AttributeError):
            o_data = None

        if o_data is not None:
            with open(pu_local_path, 'wb') as o_file:
                o_data = urllib2.urlopen(pu_url).read()
                o_file.write(o_data)
                b_download = True

        return b_download

    def download_images(self, po_dir, po_romdb_version):
        """
            Function to download the image(s) from ROMdb.

            :param po_dir: Destination directory for the downloaded images.
            :type po_dir: common_libs.files.FilePath

            :param po_romdb_version: ROMdb object.
            :type po_romdb_version: romdb_tools.libs.romdb_data.Version

            :return:
         """

        # Download of the image
        # ----------------------
        o_local_original_file = files.FilePath(po_dir.u_path, u'%s.png' % po_romdb_version.u_romset_crc32)
        b_dl = self._download(po_romdb_version.u_screenshot_ingame, o_local_original_file.u_path)

        # Resizing of the image
        # ----------------------
        if not b_dl:
            u_img = u''
        else:
            # Resizing preparation
            u_platform = po_romdb_version.u_dat_name.partition(u'_')[0]
            f_ratio = df_ASPECT_RATIOS.get(u_platform, 1.333)
            i_height = int(i_WIDTH / f_ratio)

            # Resizing
            o_image_src = Image.open(o_local_original_file.u_path)
            o_image_dst = o_image_src.resize((i_WIDTH, i_height), Image.BICUBIC)
            o_image_dst = o_image_dst.convert('RGB')

            # Saving to disc and removing the original one
            o_local_modified_file = files.FilePath(po_dir.u_path, u'%s.jpg' % po_romdb_version.u_romset_crc32)
            o_image_dst.save(o_local_modified_file.u_path)
            os.remove(o_local_original_file.u_path)
            u_img = o_local_modified_file.u_path

        return b_dl, u_img

