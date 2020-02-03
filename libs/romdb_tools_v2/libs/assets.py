from common_libs import files


try:
    import download_custom as dl
    print 'imported dl_custom'
except ImportError:
    import download_default as dl
    print 'imported dl_default'


# Functions
#=======================================================================================================================
def download_images(po_dir, po_romdb_version):
    """
    Function to download the image(s) of the po_romdb_version and return the path of the downloaded file.

    :param po_dir:
    :type po_dir: files.FilePath

    :param po_romdb_version:
    :type po_romdb_version: romdb_tools.libs.romdb_data.Version

    :return:
    :rtype bool, unicode
    """

    o_downloader = dl.Downloader()
    b_dl, u_img_path = o_downloader.download_images(po_dir, po_romdb_version)
    return b_dl, u_img_path
