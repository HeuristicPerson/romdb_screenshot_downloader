#!/usr/bin/env python

import argparse
import glob
import lxml.etree as et
import os
import sys

from libs.common_libs import files
from libs.common_libs import dat_files

from libs import assets
from libs import progress
import romdb_rom_info


# Constants
#=======================================================================================================================
u_PRG_NAME = u'ROMdb Tools - EmulationStation Scrapper v1.1 - 2019-05-10'


# Preference order for covers
#----------------------------
lu_REG_PRF = [u'esp', u'eur', u'gbr', u'usa', u'jpn', u'fra', u'deu', u'bra', u'swe']


# Classes
#=======================================================================================================================
class CmdArgs:
    def __init__(self):
        self.u_rom_path = u''
        self.u_platform = u''
        self.u_dat_path = u''
        self.u_xml_path = u''
        self.u_img_path = u''


# Helper functions
#=======================================================================================================================
def _get_cmd_args():
    """
    Function to get the command line arguments
    :return:
    :rtype CmdArgs
    """
    # [1/?] Creating the parser
    #--------------------------
    o_parser = argparse.ArgumentParser()
    o_parser.add_argument('platform',
                          action='store',
                          help='Platform name. e.g. "ps1" (NOTE: See '
                               'https://romdb.geeklogger.com/documentation/platforms-aliases-and-dats for valid'
                               'platform names in ROMdb')
    o_parser.add_argument('rom_path',
                          action='store',
                          help='File to scrape. e.g. "/home/john/my_file.zip". You can also use wildcards e.g. '
                               '"/home/john/*.zip"')
    o_parser.add_argument('dat_path',
                          action='store',
                          help='.dat file with information about the ROMs. Only ClrMamePro and XML formats are valid. '
                               'e.g. "/home/john/snes.dat"')
    o_parser.add_argument('xml_path',
                          action='store',
                          help='EmulationStation gamelist file. e.g. "/home/john/gamelist.xml"')

    o_parser.add_argument('img_dir',
                          action='store',
                          help='Directory to save images. e.g. "/home/john/downloaded_images')

    # [2/?] Validation of the input parameters
    #-----------------------------------------
    o_args = o_parser.parse_args()

    # Dat file
    #---------
    o_dat_fp = files.FilePath(o_args.dat_path)
    if not o_dat_fp.is_file():
        print u'ERROR: cannot open .dat file "%s"' % o_dat_fp.u_path
        sys.exit()

    # Output xml
    #-----------
    o_xml_fp = files.FilePath(o_args.xml_path)
    if not o_xml_fp.o_root.is_dir():
        print u'ERROR: cannot find gamelist directory "%s"' % o_xml_fp.u_root
        sys.exit()

    # Downloaded images
    #------------------
    o_img_dir = files.FilePath(o_args.img_dir)
    if not o_img_dir.is_dir():
        print u'ERROR: cannot find directory to download images "%s"' % o_img_dir.u_path

    o_cmd_args = CmdArgs()
    o_cmd_args.u_rom_path = unicode(o_args.rom_path)
    o_cmd_args.u_platform = unicode(o_args.platform)
    o_cmd_args.u_dat_path = unicode(o_args.dat_path)
    o_cmd_args.u_xml_path = unicode(o_args.xml_path)
    o_cmd_args.u_img_path = unicode(o_args.img_dir)

    u_out = u'ROM(s) path: %s\n' % o_cmd_args.u_rom_path
    u_out += u'Platform:    %s\n' % o_cmd_args.u_platform
    u_out += u'Dat path:    %s\n' % o_cmd_args.u_dat_path
    u_out += u'Gamelist:    %s\n' % o_cmd_args.u_xml_path
    u_out += u'Image dir:   %s\n' % o_cmd_args.u_img_path
    u_out += u'%s' % (u'-' * len(u_PRG_NAME))

    print u_out

    return o_cmd_args


def _scrape_file(po_file, pu_platform, po_dat, po_img_dir):
    """
    Function to scrape data for one file from ROMdb.

    :param po_file: File to be scrapped.
    :type po_file: libs.common_libs.files.FilePath

    :param po_dat: Dat file object.
    :type po_dat: libs.hqtools.libs.dat_files.RomSetContainer

    :param po_img_dir: Directory to save the downloaded images.
    :type po_img_dir: libs.common_libs.filesFilePath

    :return: an xml object
    """

    o_xgame = None

    o_progress = progress.Progress(pu_platform, po_file.u_file)

    try:
        lo_romsets = po_dat.get_romsets_by_field(u'u_name', True, (po_file.u_name,))
        o_romset = lo_romsets[0]
        o_progress.b_dat = True

    except IndexError:
        o_romset = None

    if o_romset is not None:
        o_romdb_result = romdb_rom_info.query_romset_by_crc32(pu_platform, o_romset.u_ccrc32)

        if o_romdb_result is not None:
            o_progress.b_romdb = True

            # Getting the description
            #------------------------
            lu_descs = []
            for o_game in o_romdb_result.lo_parent_games:
                if len(o_romdb_result.lo_parent_games) == 1:
                    u_desc = o_romdb_result.lo_parent_games[0].u_synopsis
                else:
                    u_desc = u'## %s ##\n%s' % (o_game.u_title, o_game.u_synopsis)

                lu_descs.append(u_desc)
            u_desc = u'\n'.join(lu_descs)

            # Getting the date
            #-----------------
            if o_romdb_result.u_mdata_date is not None:
                u_date = o_romdb_result.u_mdata_date
            else:
                u_date = u''

            # Getting the players
            #--------------------
            # TODO: Read the multiplayer info from the ROMdb result version
            i_players = 0

            # Getting the genres
            #-------------------
            lu_genres = []
            for o_game in o_romdb_result.lo_parent_games:
                lu_genres += o_game.lu_genres
            lu_genres = list(set(lu_genres))
            u_genres = u', '.join(lu_genres)

            # Getting the screenshots
            #------------------------
            b_dl, u_img_path = assets.download_images(po_img_dir, o_romdb_result)

            o_progress.b_img = b_dl

            # GameList XML
            #-------------------------------------
            # XML format for Emulation Station
            #---------------------------------
            #    <?xml version="1.0"?>
            #    <gameList>
            #      <game>
            #        <path>./Akumajou Dracula X - Gekka no Yasoukyoku (Japan) (v1.0).7z</path>
            #        <name>Castlevania: Symphony of the Night</name>
            #        <desc>Five years ago, Richter Belmont, the latest in the Belmont lineage...</desc>
            #        <image>~/.emulationstation/downloaded_images/ps1/foo.png</image>
            #        <releasedate>19970320T000000</releasedate>
            #        <developer>Konami</developer>
            #        <publisher>Konami</publisher>
            #        <genre>Action, Adventure</genre>
            #      </game>
            #      ...
            #    </gameList>
            o_xgame = et.Element(u'game')

            o_xpath = et.SubElement(o_xgame, u'path')
            o_xpath.text = po_file.u_path

            o_xname = et.SubElement(o_xgame, u'name')
            o_xname.text = o_romset.u_name

            o_xdesc = et.SubElement(o_xgame, u'desc')
            o_xdesc.text = u_desc

            o_ximag = et.SubElement(o_xgame, u'image')
            o_ximag.text = u_img_path

            o_xrat = et.SubElement(o_xgame, u'rating')
            o_xrat.text = u'%s' % (o_romdb_result.o_mdata_rating.f_average / 100.0)

            o_xdev = et.SubElement(o_xgame, u'developer')
            o_xdev.text = u''

            o_xpub = et.SubElement(o_xgame, u'publisher')
            o_xpub.text = u''

            o_xdate = et.SubElement(o_xgame, u'releasedate')
            o_xdate.text = u_date

            o_xgenr = et.SubElement(o_xgame, u'genre')
            o_xgenr.text = u_genres

            o_xplay = et.SubElement(o_xgame, u'players')
            o_xplay.text = unicode(i_players)

            o_progress.b_xml = True

    return o_xgame, o_progress


def scrape(pu_rom_path, pu_platform, pu_dat_path, pu_gamelist, pu_img_dir, pb_print=False):
    """
    Main function to scrape a romset file (or set of files when using wildcards) information from ROMdb website and save
    it to a EmulationStation gamelist.xml file.

    :param pu_rom_path:
    :type pu_rom_path: unicode

    :param pu_platform: Alias of the platform to scrape (it must be the platform alias used by ROMdb. See
                        https://romdb.geeklogger.com/documentation/platforms-aliases-and-dats
    :type pu_platform: unicode

    :param pu_dat_path:
    :type pu_dat_path: unicode

    :param pu_gamelist:
    :type pu_gamelist: unicode

    :param pu_img_dir: Path of the directory to download images. e.g. u'/home/john/download_images_here'
    :type pu_img_dir: unicode

    :param pb_print: Whether to print progress information
    :type pb_print: bool

    :return: Nothing
    """

    # [0/?] Creating the images download directory
    #---------------------------------------------
    o_img_dir = files.FilePath(pu_img_dir, pu_platform)
    if not o_img_dir.is_dir():
        os.makedirs(o_img_dir.u_path)

    # [1/?] Reading the dat
    #----------------------
    try:
        o_dat = dat_files.RomSetContainer(pu_dat_path)
    except ValueError:
        o_dat = None

    # [2/?] Reading the ROMset(s)
    #----------------------------
    lo_files = []
    for u_file in sorted(glob.glob(pu_rom_path)):
        o_file = files.FilePath(u_file)
        lo_files.append(o_file)

    # [3/?] Reading the destination .xml
    #-----------------------------------
    o_gamelist = files.FilePath(pu_gamelist)
    if o_gamelist.is_file():
        o_parser = et.XMLParser(remove_blank_text=True)
        o_xml = et.parse(o_gamelist.u_path, o_parser)
        o_xtree = o_xml.getroot()
    else:
        o_xtree = et.Element(u'gameList')

    # [4/?] Scrapping the file(s) and adding/updating them in the xml file
    #---------------------------------------------------------------------
    i_scrapped = 0
    u_tot = unicode(len(lo_files))
    for i_file, o_file in enumerate(lo_files):
        o_xgame_remote, o_progress = _scrape_file(o_file, pu_platform, o_dat, o_img_dir)

        if o_xgame_remote is not None:
            i_scrapped += 1

            # When EmulationStation saves the gamelist files after closing the program (this option can be disabled but
            # you'll lose the times played counter or any modification of the meta-data you make while in the
            # front-end), it converts absolute ROM paths in the gamelist.xml to "relative" gamepaths with respect to
            # the system ROMs directory. e.g. from:
            #
            #     <path>/mnt/jupiter/multimedia/videogames/ps1/roms/X-Men vs. Street Fighter (USA).7z</path>
            #
            # To:
            #
            #     <path>./X-Men vs. Street Fighter (USA).7z</path>
            #
            # So, when trying to find already existing ROMs in the gamelist, we need to take this change in
            # consideration and search for the full path and the modified path.
            try:
                o_xgame_local = o_xtree.xpath(u'.//path[text()="%s"]' % o_file.u_path)[0].getparent()
            except IndexError:
                try:
                    o_xgame_local = o_xtree.xpath(u'.//path[text()="./%s"]' % o_file.u_file)[0].getparent()
                except IndexError:
                    o_xgame_local = None

            # If the game doesn't exist in the local xml, we simply copy the remote data
            if o_xgame_local is None:
                o_xgame_local = o_xgame_remote
                o_xtree.append(o_xgame_local)

            # If it already exists in the local xml, we update the required tags with the remote information
            else:
                for o_remote_xelem in o_xgame_remote.iterchildren():
                    o_local_xelem = o_xgame_local.find(o_remote_xelem.tag)

                    # If the remote tag doesn't exist locally, we copy it
                    if o_local_xelem is None:
                        o_xgame_local.append(o_remote_xelem)

                    # If it exists locally, we update it
                    else:
                        o_local_xelem.text = o_remote_xelem.text

                # TODO: I don't know if this line below does anything or not
                # o_xgame_local = et.fromstring(et.tostring(o_xgame_local, pretty_print=True))

        print u'%s/%s | %s' % (unicode(i_file + 1).rjust(len(u_tot), u' '),
                               u_tot,
                               o_progress.to_line())

    with open(pu_gamelist, 'w') as o_file:
        o_file.write(et.tostring(o_xtree, pretty_print=True, xml_declaration=True, encoding='UTF-8', standalone="yes"))

    if pb_print:
        u_out = u'%s\n' % (u'-' * len(u_PRG_NAME))
        u_scr = unicode(i_scrapped).rjust(len(u_tot))
        u_out += u'%s/%s files scrapped' % (u_scr, u_tot)
        print u_out


# Main code
#=======================================================================================================================
if __name__ == '__main__':
    print u'%s\n%s' % (u_PRG_NAME, u'=' * len(u_PRG_NAME))

    o_cmd_args = _get_cmd_args()

    scrape(
        o_cmd_args.u_rom_path,
        o_cmd_args.u_platform,
        o_cmd_args.u_dat_path,
        o_cmd_args.u_xml_path,
        o_cmd_args.u_img_path,
        pb_print=True)
