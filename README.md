phrasegen
=========

Phrase generator (phrasegen) for creating random(?) password phrases from given input, file or urls.

Try these in your *nix command line to get the idea:

  % cat phrasegen.py | phrasegen.py --stdin --maxword=10 --wordscount=8 --minword=3 

  % phrasegen.py --maxword=13 --wordscount=8 --minword=3 --dont-cut-long-for-maxlimit --urls="http://web.eduskunta.fi/Resource.phx/eduskunta/index.htx?lng=fi"



