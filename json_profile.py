# -*- coding: utf-8 -*-
""" Usage: python json_profile.py <json_file> """

import codecs
import json
import sys

def keys(obj):
    """ Returns obj.iterkeys() when obj is a dict; xrange(len(obj)) otherwise. """
    assert isinstance(obj, dict) or isinstance(obj, list)
    return obj.iterkeys() if isinstance(obj, dict) else xrange(len(obj))

def size_of_obj(obj):
    """ Returns the length of `obj` when serialized compactly. """
    return len(json.dumps(obj, separators=(',',':')))

def find_heaviest_path(obj, obj_size=None):
    """ Returns the greediest path in `obj` as a list of path keys and a list of size percentages.

        Each size percentage is a value in [0, 1] that represents the percentage of that
        sub-object's size relative to the base object's size.
    """

    obj_size = obj_size or size_of_obj(obj)

    if isinstance(obj, dict) or isinstance(obj, list):
        max_size, max_key = max((size_of_obj(obj[k]), k) for k in keys(obj))
        sub_path, sub_percents = find_heaviest_path(obj[max_key], max_size)
        max_percent = float(max_size) / obj_size
        return [max_key] + sub_path, [max_percent * percent for percent in [1.0] + sub_percents]

    # Primitive objects can't be decomposed; return empty lists.
    return [], []

def decorated(key, str_prefix=u''):
    return u'[%d]' % key if type(key) is int else (str_prefix + unicode(key))

def progress_bar(percent, length=20):
    done_length = int(percent * length)
    return u'▓' * (done_length) + u'░' * (length - done_length)

def get_path_string(path):

    if len(path) == 0:
        return u'<root>'

    path_str = u''.join(decorated(key, str_prefix=u'.') for key in path)
    if path_str.startswith(u'.'):
        path_str = path_str[1:]

    return path_str

def print_interesting_splits(path, obj, heavy_path=None, heavy_percents=None, num_to_print=3):

    if num_to_print == 0:
        return

    if heavy_path is None or heavy_percents is None:
        heavy_path, heavy_percents = find_heaviest_path(obj)

    if len(heavy_percents) == 0:
        return

    max_key = heavy_path[0]
    max_percent = heavy_percents[0]

    # Don't print out boring splits.
    if max_percent < 0.15 or max_percent > 0.8:

        subpath = path + [max_key]
        subpercents = [p / max_percent for p in heavy_percents[1:]]

        print_interesting_splits(subpath, obj[max_key], heavy_path[1:], subpercents, num_to_print)

        return

    print u'--------------------------------------------------------------------------------'
    print u'Size of keys at %s' % get_path_string(path)
    obj_size = size_of_obj(obj)
    percents = [float(size_of_obj(obj[k])) / obj_size for k in keys(obj)]
    for k, percent in zip(keys(obj), percents):
        pieces = ['%20s' % k,
                  progress_bar(percent),
                  '%5.1f%%' % (100.0 * percent)]
        print u' '.join(pieces)

    num_to_print -= 1
    if num_to_print == 0:
        return

    for k, percent in zip(keys(obj), percents):

        sub_num_to_print = int(percent * num_to_print)
        if k == max_key and sub_num_to_print == 0:
            sub_num_to_print = 1

        print_interesting_splits(path + [k], obj[k], num_to_print=sub_num_to_print)


if __name__ == '__main__':

    if len(sys.argv) < 2:
        print __doc__
        exit(2)

    sys.stdout = codecs.getwriter('utf-8')(sys.stdout)

    with open(sys.argv[1]) as f:
        obj = json.load(f)

    obj_size = size_of_obj(obj)

    print u'--------------------------------------------------------------------------------'
    print u'Heaviest path:'
    path, percents = find_heaviest_path(obj, obj_size)
    for key, percent in zip(path, percents):
        pieces = ['%20s' % decorated(key),
                  progress_bar(percent),
                  '%5.1f%%' % (100.0 * percent)]
        print u' '.join(pieces)

    # Print out a few interesting splits under the main object.
    print_interesting_splits([], obj, path, percents)
