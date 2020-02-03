"""
Small script to query ROMdb for information about a ROMSET providing the platform for it and a compressed file as
parameters. By now, the program is compatible with 7z, and zip format and only recognizes ROMs without headers (so, for
example, NES ROMs are incompatible yet).
"""

import argparse
import json
import os
import sys
import urllib


from libs import compressed_files
from libs import cons
from libs import romdb_data


# Classes
#=======================================================================================================================


# Helper functions
#=======================================================================================================================
def _get_args():
    """
    Function to obtain and validate the command line arguments.
    :return:
    """
    o_parser = argparse.ArgumentParser()
    o_parser.add_argument('platform', action='store', help='Platform alias')
    o_parser.add_argument('file', action='store', help='_File to query in ROMdb')
    o_parser.add_argument('-format', action='store', help='Parent games and sagas format. s=short, m=medium, f=full')

    o_arguments = o_parser.parse_args()

    # Arguments validation
    #---------------------
    u_file = o_arguments.file
    if not os.path.isfile(u_file):
        print 'ERROR: Can\'t open file "%s"' % u_file
        sys.exit()

    u_platform = o_arguments.platform

    return {'u_file': u_file, 'u_platform': u_platform}


def _get_file_romset(pu_file):
    """
    Function to get information from a ROM file.
    :return:
    """
    u_ext = pu_file.rpartition(u'.')[2]

    if u_ext == u'7z':
        o_romset = compressed_files.scan_7z_file(pu_file)
    elif u_ext == u'zip':
        o_romset = compressed_files.scan_zip_file(pu_file)
    else:
        print 'ERROR: Invalid ROM file extension "%s"' % u_ext
        sys.exit()

    return o_romset


def query_romset_by_crc32(pu_platform, pu_crc32):
    """
    Function to query a Version by the platform name (standard alias recognised by the library can be found in
    libs/cons.py) and the (clean, not considering headers or other non-data file, e.g. .cue files) CRC32 of the ROMset.

    :param pu_platform: Alias of the platform, they can be found in libs/cons.py. e.g. u'snt-crt' for SNES cartridges.
    :type pu_platform: unicode

    :param pu_crc32: Clean CRC32 of the ROMset (if several ROMs, the resulting summ of all the ROMs is used), not
                     including headers or non-data files like .cue files. e.g. u'01a34b67'
    :type pu_crc32: unicode

    :return: A ROMset object with all the relevant data or None when no romset is found in ROMdb.
    :rtype romdb_data.Version, None
    """
    u_url = u'%s/api/version/%s/%s' % (cons.u_URL, pu_platform, pu_crc32)

    # [2/?] Querying ROMdb about the romset
    #--------------------------------------
    o_response = urllib.urlopen(u_url)
    try:
        dx_json = json.loads(o_response.read())
    except ValueError:
        dx_json = {}

    # [3/?] Parsing the json and building a full Version object with all the information
    #-----------------------------------------------------------------------------------
    # Parsing the json data
    try:
        o_romdb_version = romdb_data.Version()
        o_romdb_version.from_json(dx_json)
    except KeyError:
        o_romdb_version = None

    return o_romdb_version


def query_romset_by_file(pu_platform, pu_file):
    """
    Function to query ROMdb about a ROMset from a file path. The function should be able to identify the proper data and
    remove unwanted pieces (headers, .cue files and so on).

    :param pu_platform: The alias of the platform that has to be queried. The alias can be found in libs/cons.py
    :type pu_platform: unicode

    :param pu_file: Path of the file to be queried. e.g. u'/home/john/my_file.zip'
    :type pu_file: unicode

    :return: A Version object with all the relevant data or None if no result is found in ROMdb.
    :rtype romdb_data.Version, None
    """

    # [1/?] Creating a romset-file object by reading the file
    #--------------------------------------------------------
    # TODO: When the platform is NES (for example), remove the header and compute the CRC32
    o_romset = _get_file_romset(pu_file)
    o_romset.u_platform = pu_platform

    return query_romset_by_crc32(pu_platform, o_romset.u_crc32)


# Main code
#=======================================================================================================================
if __name__ == '__main__':
    print 'ROMDB file info v1.0 - 2018-10-27'
    print '================================='
    dx_args = _get_args()

    o_version = query_romset_by_file(dx_args['u_platform'], dx_args['u_file'])

    #print dx_romdb_json
    print o_version.nice_text(ps_format='medium')
