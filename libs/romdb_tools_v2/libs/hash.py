def unicode_crc32(pi_crc32):
    """
    Function to profuce an unicode CRC32 from an integer one.
    :param pi_crc32:
    :return:
    """
    u_crc32 = unicode(hex(pi_crc32)[2:].rjust(8, '0'))
    return u_crc32
