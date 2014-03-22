phrasegen
=========

Phrase generator (phrasegen) for creatingpassword phrases from given input, file or urls.

Try this in you *nix command line:

  # phrasegen.py --maxword=13 --wordscount=8 --minword=3 --dont-cut-long-for-maxlimit --scramble-random --urls="http://web.eduskunta.fi/Resource.phx/eduskunta/index.htx?lng=fi"

  # cat phrasegen.py | phrasegen.py --stdin --maxword=10 --wordscount=8 --minword=3 --scramble-force

