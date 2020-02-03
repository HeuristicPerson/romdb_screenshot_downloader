#!/usr/bin/env python

"""
Script to backup the favourites from EmulationStation to a file that later can be restored although the ROMs had
changed their names (if they match the no-intro and redump dats).
"""

import codecs
import datetime

import argparse
import lxml.etree as et

from libs.common_libs import csv
from libs.common_libs import dat_files
from libs.common_libs import files


# Constants
#=======================================================================================================================
u_PRG_NAME = u'ES Favourites Backup v1.0 - 2019-05-11'


# Classes
#=======================================================================================================================
class CmdArgs:
    def __init__(self):
        self.foo = 'bar'


class Favorite:
    """
    Class to store information about a favorite game.

    :ivar u_crc32: unicode
    :ivar u_name: unicode
    :ivar u_platform: unicode
    """
    def __init__(self):
        self.u_crc32 = u''      # Clean CRC32 of the ROMset
        self.u_name = u''       # Name of the ROMset
        self.u_platform = u''   # Platform alias of the ROMset

    def __str__(self):
        return unicode(self).encode('utf8')

    def __unicode__(self):
        u_out = u'<Favorite>\n'
        u_out += u'  .u_platform: %s\n' % self.u_platform
        u_out += u'  .u_crc32:    %s\n' % self.u_crc32
        u_out += u'  .u_name:     %s\n' % self.u_name
        return u_out


# Helper functions
#=======================================================================================================================
def _get_cmd_args():
    """
    Function to get and parse the command line argumens.
    :return:
    """

    o_parser = argparse.ArgumentParser()
    o_parser.add_argument('gamelist', action='store', help='Path of the EmulationStation gamelist.xml file to read')
    o_parser.add_argument('dat', action='store', help='Path of the dat file to check the ROM names against')
    o_parser.add_argument('backup', action='store', help='Path of the filte to write the backup')

    o_args = o_parser.parse_args()

    # Validation of the gamelist

    # Validation of the dat file

    # Validation of the backup file


# Main functions
#=======================================================================================================================
def backup_favourites(pu_gamelists_dir, pu_backup_file, pu_dats_dir=None, pb_print=False):
    """
    Function to save the favourites to a backup file in disk.

    :param pu_gamelists_dir:
    :param pu_backup_file:
    :param pu_dats_dir:
    :param pb_print:
    :return:
    """
    to_favs = get_favourites_from_gamelists(pu_gamelists_dir, pu_dats_dir=pu_dats_dir, pb_print=pb_print)

    lu_comments = [
        u'Created with: %s' % u_PRG_NAME,
        u'Date: %s' % datetime.datetime.now(),
        ]

    o_csv = csv.ParsedCsv()
    o_csv.lu_comments = lu_comments
    o_csv.lu_headings = [u'Platform', u'cCRC32', u'Name']

    for o_fav in to_favs:
        o_csv.append_row([o_fav.u_platform, o_fav.u_crc32, o_fav.u_name])

    o_csv.save_to_disk(pu_file=pu_backup_file, pu_sep=u'\t', pu_com=u'#')


def get_favourites_from_gamelists(pu_gamelists_dir, pu_dats_dir=None, pb_print=False):
    """
    Function to backup the favorites of an EmulationStation gamelist.xml file to a txt.

    :param pu_gamelists_dir:
    :type pu_gamelists_dir: unicode

    :param pu_dats_dir:
    :type pu_dats_dir: unicode

    :param pb_print: Whether the function will print information about the favourites it's finding.
    :type pb_print: bool

    :return:
    :rtype tuple[Favorite]
    """
    o_gamelists_root = files.FilePath(pu_gamelists_dir)

    lo_gamelists = o_gamelists_root.content(pb_recursive=True, ps_type='files', ptu_exts=(u'xml',))
    u_gamelists = unicode(len(lo_gamelists))

    lo_favs = []

    for i_gamelist, o_gamelist in enumerate(lo_gamelists):
        u_platform = o_gamelist.lu_elements[-2]
        o_dat_fp = files.FilePath(pu_dats_dir, u'%s.dat' % u_platform)

        try:
            u_dat = o_dat_fp.u_path
        except AttributeError:
            u_dat = None

        if not o_dat_fp.is_file():
            u_dat = None

        if pb_print:
            u_gamelist = unicode(i_gamelist + 1).rjust(len(u_gamelists), u' ')
            u_heading = u'[%s/%s] %s' % (u_gamelist, u_gamelists, u_platform)

            print u'%s\n%s' % (u_heading, u'-' * len(u_heading))
            print u'    .xml: %s' % o_gamelist.u_path
            print u'    .dat: %s' % u_dat

        to_system_favs = get_favourites_from_gamelist(o_gamelist.u_path, pu_dat=u_dat)
        lo_favs += to_system_favs

        if pb_print:
            print u'    Favs: %i' % len(to_system_favs)

            for o_fav in to_system_favs:
                print u'          %s | %s' % (o_fav.u_crc32, o_fav.u_name)

        print

    return tuple(lo_favs)


def get_favourites_from_gamelist(pu_gamelist, pu_dat=None):
    """
    Function to get the favourite games from an EmulationStation gamelist.xml.
    :param pu_gamelist:
    :param pu_dat:
    :return:
    """

    # [1/?] Reading the XML and the dat file
    #---------------------------------------
    o_parser = et.XMLParser(remove_blank_text=True)
    o_xml = et.parse(pu_gamelist, o_parser)
    o_xtree = o_xml.getroot()

    if pu_dat is not None:
        o_dat = dat_files.RomSetContainer(pu_dat)
    else:
        o_dat = None

    # [2/?] Obtaining the platform name
    #----------------------------------
    # TODO: Figure out a way of setting the platform name if the gamelist.xml is not in the proper place.
    o_gamelist_fp = files.FilePath(pu_gamelist)
    u_platform = o_gamelist_fp.lu_elements[-2]

    # [3/?] Finding all the favourite games and trying to find all its information in the dat file
    #---------------------------------------------------------------------------------------------
    lo_favs = []
    for o_xfav_attribute in o_xtree.xpath(u'.//favorite[text()="true"]'):
        o_favorite = Favorite()

        o_xgame = o_xfav_attribute.getparent()

        o_favorite.u_name = o_xgame.find(u'name').text
        o_favorite.u_platform = u_platform

        if o_dat is None:
            o_favorite.u_crc32 = u'????????'
        else:
            lo_dat_romsets = o_dat.get_romsets_by_field(
                u'u_name',
                pb_first=True,
                ptx_search_values=(o_favorite.u_name,))

            try:
                o_favorite.u_crc32 = lo_dat_romsets[0].u_ccrc32
            except IndexError:
                o_favorite.u_crc32 = u'????????'

        lo_favs.append(o_favorite)

    return tuple(lo_favs)


# Main code
#=======================================================================================================================
if __name__ == '__main__':
    # --- TEST CODE ---
    u_gamelist = u'/tmp/32x.xml'
    u_dat = u'sample_data/dats_and_lists/Sega_32X_20190417.dat'
    # get_favourites_from_gamelists(u'/home/admin/.emulationstation/gamelists',
    #                               pu_dats_dir=u'/home/admin/emulation_data/dats', pb_print=True)
    backup_favourites(u'/home/admin/.emulationstation/gamelists',
                      u'/tmp/backup.csv',
                      pu_dats_dir=u'/home/admin/emulation_data/dats', pb_print=True)
    # ------ end ------