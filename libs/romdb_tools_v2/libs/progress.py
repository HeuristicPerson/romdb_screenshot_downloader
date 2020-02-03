# -*- coding: utf-8 -*-

"""
Library with screen reporting utilities.
"""


class Progress(object):
    """
    Class with information about the scrapping progress for a file.
    """
    def __init__(self, pu_platform, pu_file):
        self._u_platform = pu_platform
        self._u_name = pu_file

        self.b_dat = False     # Whether the file is found in the dat file
        self.b_romdb = False   # Whether the romset is found in ROMdb
        self.b_img = False     # Whether the image has been downloaded
        self.b_xml = False     # Whether the data has been saved to xml

    def to_line(self):

        # Found in dat file
        #------------------
        u_dat = u' · '
        if self.b_dat:
            u_dat = u'dat'

        # Found in ROMdb
        #---------------
        u_romdb = u' · '
        if self.b_romdb:
            u_romdb = u'Rdb'

        # Image downloaded and processed
        #-------------------------------
        u_img = u' · '
        if self.b_img:
            u_img = u'Img'

        # XML written
        #------------
        u_xml = u' · '
        if self.b_xml:
            u_xml = u'xml'

        # Final output
        #-------------
        u_out = u'%s %s %s %s | %s > %s' % (u_dat, u_romdb, u_img, u_xml, self._u_platform, self._u_name)

        return u_out
