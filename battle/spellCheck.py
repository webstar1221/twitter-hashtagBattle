"""
description: Tokenize a tweet text and check whether a word is spelled correctly.
parameter: a query of statuses pulled from Twitter
return: number of typos
"""

import re
import enchant


def preprocess(query):

    emoticons_str = r"""
    (?:
        [:=;]  # Eyes
        [oO\-]?  # Nose (optional)
        [D\)\]\(\]/\\OpP]  # Mouth
    )"""

    regex_str = [
        emoticons_str,
        r'<[^>]+>',  # HTML tags
        r'(?:@[\w_]+)',  # @-mentions
        r"(?:\#+[\w_]+[\w\'_\-]*[\w_]+)",  # hash-tags
        r'http[s]?://(?:[a-z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-f][0-9a-f]))+',  # URLs

        r'(?:(?:\d+,?)+(?:\.?\d+)?)',  # numbers
        r"(?:[a-z][a-z'\-_]+[a-z])",  # words with - and '
        r'(?:[\w_]+)',  # other words
        r'(?:\S)'  # anything else
    ]

    tokens_re = re.compile(r'('+'|'.join(regex_str)+')', re.VERBOSE | re.IGNORECASE)

    # emoticon_re = re.compile(r'^'+emoticons_str+'$', re.VERBOSE | re.IGNORECASE)

    # def preprocess(s, lowercase=False):
    #     tokens = tokens_re.findall(s)
    #     if lowercase:
    #         tokens = [token if emoticon_re.search(token) else token.lower() for token in tokens]
    #
    #     tokens = [token for token in tokens if not re.compile(r'[^a-zA-Z]').search(token)]
    #     return tokens

    en_dict = enchant.Dict("en_US")
    num_typos = 0

    for status in query:
        tokens = tokens_re.findall(status.text)  # preserve @-mentions, emoticons, URLs and hastags as individual tokens
        word_tokens = [token for token in tokens if not re.compile(r'[^a-zA-Z]').search(token)]  # extract tokens involving only English characters

        for word in word_tokens:
            if not en_dict.check(word):  # spellChecking by PyEnchant library
                num_typos += 1

    return num_typos