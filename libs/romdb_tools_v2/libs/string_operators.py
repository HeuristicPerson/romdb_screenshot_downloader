def sentence_split(pu_sentence, pi_length=64):
    """
    Function to divide a long sentence into different lines of max length.
    :param pu_sentence:
    :param pi_length:
    :return:
    """
    lu_words = pu_sentence.split()

    lu_lines = []
    u_line = u''

    for u_word in lu_words:
        u_expanded_line = u'%s %s' % (u_line, u_word)

        if len(u_expanded_line) <= pi_length:
            u_line = u_expanded_line

        else:
            lu_lines.append(u_line.strip())
            u_line = u'%s' % u_word

    else:
        lu_lines.append(u_line)

    return lu_lines