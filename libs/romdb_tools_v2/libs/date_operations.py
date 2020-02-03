"""
Library with date/time functions for ROMdb tools.
"""

import datetime


# Main functions
#=======================================================================================================================
def unicode_to_datetime(pu_date):
    """
    Function to convert a ROMdb date string to datetime object. In ROMdb dates can have question marks as wildcards for
    unknown parts of the dates. e.g. 1997-08-??
    :param pu_date:
    :return:
    """
    if pu_date and u'?' not in pu_date[:4]:
        o_datetime = datetime.datetime.strptime(pu_date[:4], u'%Y')
    else:
        o_datetime = None

    return o_datetime

