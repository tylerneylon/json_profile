# json_profile
*A tool to find data bottlenecks.*

This is a tool that can help you analyze a json object
to determine if one path within your object is taking up
most of the room. It treats lists as if they were intended to
be homogeneously composed of same-schema elements; however,
it won't barf if that isn't true.

Usage:

    python json_profile.py <json_filename>

The output consists of a breakdown of the heaviest path,
meaning the sequence of keys such that each key uses up
the most room at its level compared with its peers.

Another output element is a set of peer-key breakdowns
at various subpaths. The script tries to find the most
interesting breakdowns, which are ones that use up a lot
of room, yet have peers that are neither single-key-dominant
nor made up of many equally-small pieces.

Below is an example from a json object I received from this url:

    curl http://pokeapi.co/api/v2/type/3/ > pokemon.json

Here is the output:

```
$ python json_profile.py pokemon.json
--------------------------------------------------------------------------------
Heaviest path:
                       pokemon ▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░  69.3%
                    [].pokemon ▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░  51.8%
                           url ▓▓▓▓▓▓░░░░░░░░░░░░░░  31.0%
--------------------------------------------------------------------------------
Size of keys at <root> [100.0% of total object size]
                          name ░░░░░░░░░░░░░░░░░░░░   0.1%
                    generation ░░░░░░░░░░░░░░░░░░░░   0.5%
              damage_relations ▓░░░░░░░░░░░░░░░░░░░   7.0%
                  game_indices ░░░░░░░░░░░░░░░░░░░░   4.8%
             move_damage_class ░░░░░░░░░░░░░░░░░░░░   0.6%
                         moves ▓▓░░░░░░░░░░░░░░░░░░  11.9%
                       pokemon ▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░  69.3%
                            id ░░░░░░░░░░░░░░░░░░░░   0.0%
                         names ░░░░░░░░░░░░░░░░░░░░   5.0%
--------------------------------------------------------------------------------
Size of keys at pokemon[] [ 68.5% of total object size]
                          slot ░░░░░░░░░░░░░░░░░░░░   1.2%
                       pokemon ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░  75.7%

```
