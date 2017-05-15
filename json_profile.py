# -*- coding: utf-8 -*-
""" Usage: python json_profile.py <json_file> """

import codecs
import json
import sys

WILDCARD = 0  # Any unique hashable non-string value will work here.

class ObjList(list):
    """ This acts just like a list, but it's a separate type so we can distinguish a subobject of
        the original input from a list of subobjects that was derived using wildcards.
    """

    def add(self, other):
        if other is None:
            return
        if isinstance(other, ObjList):
            self.extend(other)
        else:
            self.append(other)

def flat_tuple(*args):

    if len(args) == 1:
        return flat_tuple(*args[0]) if type(args[0]) is tuple else (args[0],)

    return tuple(sub_arg for a in args for sub_arg in flat_tuple(a))

def steps(obj):
    """ Returns an iterable. Each step is either a string key or WILDCARD. """

    if isinstance(obj, ObjList):
        # Individual subobjects could be primitive or complex; handle both together.
        return {step for subobj in obj for step in steps(subobj)}

    if isinstance(obj, list):
	return [WILDCARD]

    if isinstance(obj, dict):
        return obj.iterkeys()

    return []  # Primitive objects have no steps to iterate.

def size_of_obj(obj):
    """ Returns the length of `obj` when serialized compactly. """

    if isinstance(obj, ObjList):
        return sum(size_of_obj(subobj) for subobj in obj)

    return len(json.dumps(obj, separators=(',',':')))

def at(obj, path):
    """ Returns the subset of `obj` at `path`.

        If `path` is a list of strings (eg ['a', 'b']) then the returned value is a simple
        sub-object (eg obj.a.b). If `path` contains any WILDCARDs, then these are treated as
        wildcards across list indexes; the return value is an ObjList of all subobjects at any
        path that matches the wildcards. For example, path=['a', WILDCARD, 'b'] will result in the
        ObjList [obj.a[0].b, obj.a[1].b, .., obj.a[n].b], where obj.a is a list and n = len(obj.a).

        It's not an error if a part of the path doesn't match an object; instead, that subobject is
        considered empty.
    """

    if type(path) not in [tuple, list]:
        path = (path,)
    path = flat_tuple(*path)

    if len(path) == 0:
        return obj

    is_obj_list = isinstance(obj, ObjList)

    if is_obj_list or path[0] == WILDCARD:
        if not isinstance(obj, list):
            return None
        subpath = path if is_obj_list else path[1:]
        at_list = ObjList()
        for subobj in obj:
            at_list.add(at(subobj, subpath))
        return at_list

    if isinstance(obj, dict) and path[0] in obj:
        return at(obj[path[0]], path[1:])

    return None

def find_heaviest_path(obj, obj_size=None):
    """ Returns the greediest path in `obj` as a list of path keys and a list of size percentages.

        Each size percentage is a value in [0, 1] that represents the percentage of that
        sub-object's size relative to the base object's size.
    """

    # This will be an empty list if obj is a primitive (and in some other cases).
    sizes = [(size_of_obj(at(obj, s)), s) for s in steps(obj)]
    if len(sizes) == 0:
        return [], []

    obj_size = obj_size or size_of_obj(obj)

    max_size, max_step = max(sizes)
    sub_path, sub_percents = find_heaviest_path(at(obj, max_step), max_size)
    max_percent = float(max_size) / obj_size

    return [max_step] + sub_path, [max_percent * percent for percent in [1.0] + sub_percents]

def decorated(key, str_prefix=u''):
    return u'[]' if key == WILDCARD else (str_prefix + unicode(key))

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

def print_interesting_splits(path, obj, heavy_path=None, heavy_percents=None, to_print=3,
        params=None):

    if params is None:
        params = {'main_size': size_of_obj(obj), 'main_obj': obj}

    if to_print == 0:
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

        print_interesting_splits(subpath, at(obj, max_key), heavy_path[1:], subpercents, to_print,
                params)

        return

    path_string = get_path_string(path)
    obj_size = size_of_obj(obj)
    main_percent = 100.0 * obj_size / params['main_size']
    print u'--------------------------------------------------------------------------------'
    print u'Size of keys at %s [%5.1f%% of total object size]' % (path_string, main_percent)
    percents = [float(size_of_obj(at(obj, s))) / obj_size for s in steps(obj)]
    for s, percent in zip(steps(obj), percents):
        pieces = ['%30s' % s,
                  progress_bar(percent),
                  '%5.1f%%' % (100.0 * percent)]
        print u' '.join(pieces)

    to_print -= 1
    if to_print == 0:
        return

    for s, percent in zip(steps(obj), percents):

        sub_num_to_print = int(percent * to_print)
        if s == max_key and sub_num_to_print == 0:
            sub_num_to_print = 1

        print_interesting_splits(path + [s], at(obj, s), to_print=sub_num_to_print, params=params)

def shortened_path_and_percents(path, percents):
    """ Shorten path elements with wildcards; eg, ['a', WILDCARD, 'b'] becomes ['a', '[].b'].

        The percents are accordingly reduced.
    """

    short_paths = []
    short_percents = []

    i = 0
    while i < len(path):

        short_path = []

        while True:

            is_wildcard = (path[i] == WILDCARD)

            short_path.append('[]' if is_wildcard else path[i])
            short_percent = percents[i]

            if not is_wildcard or i + 1 == len(path):
                break

            i += 1

        short_paths.append(u'.'.join(short_path))
        short_percents.append(short_percent)

        i += 1

    return short_paths, short_percents


if __name__ == '__main__':

    if len(sys.argv) < 2:
        print __doc__
        sys.exit(2)

    sys.stdout = codecs.getwriter('utf-8')(sys.stdout)

    with open(sys.argv[1]) as f:
        obj = json.load(f)

    obj_size = size_of_obj(obj)

    print u'--------------------------------------------------------------------------------'
    print u'Heaviest path:'
    path, percents = find_heaviest_path(obj, obj_size)
    path, percents = shortened_path_and_percents(path, percents)

    for key, percent in zip(path, percents):
        pieces = ['%30s' % key,
                  progress_bar(percent),
                  '%5.1f%%' % (100.0 * percent)]
        print u' '.join(pieces)

    # Print out a few interesting splits under the main object.
    print_interesting_splits([], obj, path, percents)


#################################################################################
# Temporary test objects.

obj1 = [1, 2, 3]
obj2 = {'a': 1, 'b': 2, 'c': [1, 2, 3, 4]}
obj3 = {'a': [{'c': 1, 'd': 2},
              {'c': 100, 'e': 3},
              {'c': [1, 2, 3], 'd': 50}],
        'b': {'d': {'g': 42}}}
obj4 = [[1, 2, 3], [4, 5], [{'a': 10}, {'a': 20}]]
obj5 = {}

objs = [obj1, obj2, obj3, obj4, obj5]
