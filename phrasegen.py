#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Phrase generator (phrasegen) for creating password phrases from given input, file or urls.
#
# Copyright (C) 2012-2014 Jani Päijänen
# License: Simplified BSD License
#
#


import random
from optparse import OptionParser
import operator
import re
import sys
import urllib
import urlparse
import Queue
import threading
import re
import logging
import os

logging.basicConfig(format='%(asctime)s %(filename)s %(lineno)d  %(message)s')
logger = logging.getLogger(__name__)
#logging.getLogger(__name__).addHandler(logging.NullHandler())
#logger.setLevel(logging.DEBUG)
logger.setLevel(logging.ERROR)


try:
  from BeautifulSoup import BeautifulSoup, Comment
except ImportError, e:
  print >> sys.stderr, "install BeautifulSoup"
  logger.fatal("install BeautifulSoup")
  sys.exit(1)
import time 

class MyOpener (urllib.FancyURLopener):
  version = 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.15) Gecko/20131019 phrasegen/1.0.2'


Newlines = re.compile (r'[\r\n]\s+')

encoding_guess_list=['utf8', 'cp775', 'cp1250', 'iso-8859-1', 'iso-8859-15', 'iso-8859-13', 'iso-8859-16', 'latin1', ]
def try_unicode(string, errors='strict'):
    if isinstance(string, unicode):
        return string
    assert isinstance(string, str), repr(string)
    for enc in encoding_guess_list:
        try:
            return string.decode(enc, errors)
        except UnicodeError, exc:
            continue
    raise UnicodeError('Failed to convert %r' % string)

def test_try_unicode():
    for start, should in [
        ('\xfc', u'ü'),
        ('\xc3\xbc', u'ü'),
        ('\xbb', u'\xbb'), # postgres/psycopg2 latin1: RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK
        ]:
        result=try_unicode(start, errors='strict')
        if not result==should:
            raise Exception(u'Error: start=%r should=%r result=%r' % (
                    start, should, result))
    


queue_urls = Queue.Queue ()
queue_content = Queue.Queue ()
queue_content_stilized = Queue.Queue ()

def Dout(msg=None):
  print (msg)

class ThreadUrl (threading.Thread):
  """Threaded Url Grab"""
  def __init__ (self, queue, out_queue):
      threading.Thread.__init__ (self)
      self.queue = queue
      self.out_queue = out_queue

      logger.debug("ThreadURL %s" % u"constructor")

  def run (self):
      while True:
          #grabs host from queue
          url=None
          text=""
          if self.queue != None:
            url = self.queue.get ()

          try:
            if url != None:
              #logger.debug("")
              #Dout ("ThreadURL %s" % url)
              myopener = MyOpener ()
              #logger.debug("")
              #page = urllib.urlopen(url)
              page = myopener.open (url)
              
            if page:
              text = page.read ()
              page.close ()
          except Exception, e: 
            logger.error(url + " "  + str(e))


          #place chunk into out queue
          self.out_queue.put (try_unicode(text))

          #signals to queue job is done
          self.queue.task_done ()

class DatamineThread(threading.Thread):
    """Threaded Url Grab"""
    def __init__(self, out_queue, stilized_queue):
        threading.Thread.__init__(self)
        self.out_queue = out_queue
        self.stilized_queue = stilized_queue

    def run(self):
        while True:
      
            #grabs host from queue
            text = self.out_queue.get()

            try:
              self.stilized_queue.put(stilize_page(text))
            except Exception, e:
              logger.debug(str(e))

            #signals to queue job is done
            self.out_queue.task_done()

def fetch_url(url):
  myopener = MyOpener()
  #page = urllib.urlopen(url)
  page = myopener.open(url)
    
  text = try_unicode(page.read())
  page.close()
  return stilize_page(text)

def stilize_page(text):
  try:
    bs = BeautifulSoup(text, convertEntities=BeautifulSoup.HTML_ENTITIES)
    # kill javascript content
    #for s in bs.findAll('script'):
    #   s.replaceWith('')

    #for s in bs.findAll('img'):
    #   s.replaceWith('')

    #http://mail.python.org/pipermail/tutor/2007-July/055899.html
    #remove unnecessary things (scripts, styles, ...)
    for script in bs("script"):
        bs.script.extract()

    for style in bs("style"):
        bs.style.extract()
       
    #remove comments
    comments = bs.findAll(text=lambda text:isinstance(text, Comment))
    [comment.extract() for comment in comments]
  
    #

    txt=None
    # find body and extract text
    if (bs.find('body') != None):
      #print bs.originalEncoding
      txt = bs.find('body').getText('\n')
      #txt = bs.find('body').renderContents()
      # remove multiple linebreaks and whitespace
      return Newlines.sub('\n', txt)
  except Exception, e:
    msg = str(e) .join(" stilize_page")
    print >> sys.stderr, msg
    logger.debug(msg)

  return None

#def Dout(msg, level=5):
#  print (msg)
#  pass

def scramble_word_contents(word, wordlen):

  pos_ma=0
  pos_mi=0

  # allow swapping all but first and last chars, if long enough
  if wordlen-2 > 0:
    pos_ma = random.randint(1, wordlen-2)
    pos_mi = random.randint(1, wordlen-2)
  else:
    pos_ma = 0
    pos_mi = 0

  if pos_ma < pos_mi:
    temp_holder = pos_ma
    pos_ma = pos_mi
    pos_mi = temp_holder

  #logger.debug("")
  #logger.debug("len, min, max: %d, %d, %d, %s" % (wordlen, pos_mi, pos_ma, word))
  #logger.debug("")

  #if (pos_ma != pos_mi) and (pos_mi < wordlen) and (pos_ma > 0):
  if (pos_ma > pos_mi) and (pos_ma < wordlen):
    tchr = word[:pos_mi]
    tchr += word[pos_ma]
    tchr += word[pos_mi+1:pos_ma]
    tchr += word[pos_mi]
    tchr += word[pos_ma+1:]
    word = tchr
    #if len (tmp) == 0:
      #i=0
      #Dout("-%s-%d  %s" % (tmp, len(tmp), w ) )
      #continue

  return word


def cutword(word, wordlen, min_length, max_length, cut_long_for_maxlimit, cut_long_for_minlimit):
  tmp = ""
  if ( (cut_long_for_minlimit == True) and ( wordlen >= min_length) ) : 
    if (cut_long_for_maxlimit == False):
      if wordlen <= max_length:
        tmp = word
        i = 1
    else:
        tmp = word[:max(min_length, max_length)]
        i = 1
  elif (cut_long_for_minlimit == False):
    tmp = word[:min(min_length, max_length)]
    i=1


  return tmp

def randomize_filecontents(data,  min_length, max_length, cut_long_for_maxlimit, cut_long_for_minlimit, scramble_force, scramble_random, db=None, fout=None):

  contents = []
  for line in data:
    liner = []

    if line == None : continue    

    line = re.sub("\s\s+" , " ", line)

    if len(line) == 0: continue

    tmp = ""
    for w in line.strip().split():
      l = len(w)
      if l == 0: continue
      if l < min_length: continue

      w = cutword(w, l, min_length, max_length, cut_long_for_maxlimit, cut_long_for_minlimit)

      l = len(w)
      do_swap = False

      if scramble_force == True or scramble_random == True:
        if scramble_random == True:
          do_swap = random.randint(1,100) >= 30
        else:
          do_swap = True
      
        
      if do_swap == True and l>3 :
        #logger.debug(w)
        w = scramble_word_contents(w, l)
        #logger.debug(w)
        #logger.error(w)
        
      #liner.append(w)
      contents.append(w)
    #logger.error(liner)
    #contents += liner
    

  #result = []
  random.shuffle(contents)

  return contents

def do_writefile (result, fout, wordcount):
  i = 0
  if fout != None:
    out = open(fout, "w")
    for r in result:
      try:
        out.write(r)
        i += 1
        if i >=wordcount:
          out.write(os.linesep)
          i = 0
        else:
          out.write(" ")
      except Exception, e:
        pass
    out.close()
  else:
    for r in result:
      try:
        #logger.debug(r)
        #print (r)
        #sys.stdout.buffer.write(b(r) )
        os.write(sys.stdout.fileno(), r.encode("utf-8"))
        i += 1
        if i >=wordcount:
          os.write(sys.stdout.fileno(),  os.linesep)
          i = 0
        else:
          os.write(sys.stdout.fileno(), " ")
      except UnicodeEncodeError, e:
        logger.fatal(str(e))
        #print >> sys.stderr, str(e)
        pass
      except UnicodeDecodeError, e:
        pass
    if i != 0:
      os.write(sys.stdout.fileno(), os.linesep)

   
def do_readfile(filename):
  data = []
  f = open(filename, "r")
  for line in f:
    line = try_unicode( line.strip ())
    if len (line) == 0: continue
    data.append (line)
  f.close()      
  return data


def main (default_urls=False):

  parser = OptionParser()

  parser.add_option("-r", "--randfile", dest="randomizefile",type="string", action="store",
                    help="file contents to randomize")

  parser.add_option ( "--wordscount", dest="wordscount", default=5,
                    type="int", help="Count of words in phrase.")

  parser.add_option ( "--minword", dest="minword", default=2,
                    type="int", help="Minimum word length")

  parser.add_option ( "--maxword", dest="maxword", default=17,
                    type="int", help="Maximum word length")

  parser.add_option ( "--dont-cut-long-for-maxlimit", dest="cut_long_for_maxlimit", default=True,
                    action="store_false",
                    help="Default: cut long words to meet maxlimit")
                    
  parser.add_option ( "--cut-long-for-minlimit", dest="cut_long_for_minlimit", default=True,
                    action="store_false",
                    help="False: cut long words to make them shorter. True: use words not shorter than minword limit.")
  
  parser.add_option ( "--urls", dest="urls", default=None, action="store", type="string",
                    help="List of URLs separated by space.")

  parser.add_option ( "-d", "--default-urls", dest="default_urls", default=False, action="store_true",
                    help="Use list of default URLS")

  parser.add_option ( "--stdin", dest="stdin", default=False, 
                    action="store_true", help="Read from stdin")

  parser.add_option ( "--scramble-force", dest="scramble_force", default=False, 
                      action="store_false", help="Always swap position of word's letters, but first and last. 70% of words. Applies to word length > 3. Default=False")

  parser.add_option ( "--scramble-random", dest="scramble_random", default=True, 
                    action="store_true", help="Swap position of word's letters, but first and last. 70% of words. Applies to word length > 3. Default=True")

  parser.add_option ( "--fout", dest="fout", default=None, 
                    action="store", type="string", help="outfile. If omitted, write to stdout")


  parser.add_option("-q", "--quiet",
                    action="store_false", dest="verbose", default=True,
                    help="don't print status messages to stdout")

  (options, args) = parser.parse_args()
  
  urls = None

  if options.scramble_force  == True:
    options.scramble_random = False

  urls_list = None
  if options.default_urls == True:
    urls_list = []
    urls_list.append ("https://fi.wikipedia.org/wiki/Special:Random")
    urls_list.append ("http://hikipedia.info/wiki/Toiminnot:Satunnainen_sivu")
    urls_list.append ("http://www.gutenberg.org/files/7000/7000-h/7000-h.htm")
    urls_list.append ("https://fi.wikipedia.org/wiki/Luettelo_E-koodatuista_aineista")
    urls_list.append ("https://se.wikipedia.org/wiki/Special:Random")
    urls_list.append ("https://de.wikipedia.org/wiki/Special:Random")
    urls_list.append ("https://en.wikipedia.org/wiki/Special:Random")
    urls_list.append ("http://en.wikiquote.org/wiki/Special:Random")
    urls_list.append ("http://fi.wikiquote.org/wiki/Special:Random")
    urls_list.append ("http://se.wikiquote.org/wiki/Special:Random")
    urls_list.append ("http://de.wikiquote.org/wiki/Special:Random" )
    urls_list.append ("https://en.wikipedia.org/wiki/Wikipedia:List_of_all_single-digit-single-letter_combinations")
    urls_list.append ("https://en.wikipedia.org/wiki/List_of_medical_roots,_suffixes_and_prefixes")
    urls_list.append ("https://en.wikipedia.org/wiki/List_of_abbreviations_used_in_medical_prescriptions")
    urls_list.append ("https://en.wikipedia.org/wiki/Acronyms_in_healthcare")
    urls_list.append ("https://en.wikipedia.org/wiki/E_number")
    urls_list.append ("https://en.wikipedia.org/wiki/List_of_food_additives,_Codex_Alimentarius")
    urls_list.append ("https://en.wikipedia.org/wiki/List_of_food_additives")
    urls_list.append ("https://en.wikipedia.org/wiki/Wikipedia:List_of_all_single-letter-double-digit_combinations")
    urls_list.append ("http://www.hs.fi")
    urls_list.append ("http://www.ksml.fi")
    urls_list.append ("http://www.ilkka.fi")
    urls_list.append ("http://www.turunsanomat.fi")
    urls_list.append ("http://www.parikkalan-rautjarvensanomat.fi")
    urls_list.append ("http://www.saynatsalonsanomat.fi")
    urls_list.append ("http://www.kaleva.fi")
    urls_list.append ("http://www.maaseuduntulevaisuus.fi")    
    random.shuffle(urls_list)

  if options.randomizefile == None and options.stdin == False and urls == None and options.urls ==None:
 #options.urls == None :
    parser.print_help()
    print ("Phrase generator (phrage) for creating random(?) password phrases from given URLs.")
    print ("Try either row from below to see how it works. ")
    print (' egrep -v "^[ ]*$|^#" "phrasegen.py" | grep -v ===  | phrasegen.py --stdin --maxword=13 --wordscount=8 --minword=3 --dont-cut-long-for-maxlimit | sed s@\ @@g | cut -c 1-32')

  data = []

  if options.randomizefile != None:
    data = do_readfile(options.randomizefile)
  elif options.stdin == True:
    #data = []
    for line in sys.stdin:
      line = try_unicode(line.strip())
      if len (line) == 0: continue
      data.append (line)
    #randomize_filecontents(data, options.wordscount, options.minword, options.maxword, options.cut_long_for_maxlimit, options.cut_long_for_minlimit)
  elif options.urls != None or urls_list != None:
    thethreads = []
    local_urls = ""

    if options.urls != None:
      local_urls = options.urls.split()

    if urls_list != None:

      for u in urls_list:
        local_urls = local_urls + u.split()

    urlcount = len(local_urls)

    try:

      #Dout("Thread count: %d" % urlcount)
      logger.debug("Thread count: %d" % urlcount)

      #spawn a pool of threads, and pass them queue instance
      for i in range(urlcount):
          t = ThreadUrl (queue_urls, queue_content)
          thethreads.append(t)
          t.setDaemon (True)
          t.start()

    except Exception, e:
      logger.error(str(e) + " exception at urls" )
      for t in thethreads:
        t.stop()

    for u in local_urls:
      queue_urls.put (u.strip())

    try:
      for i in range(urlcount):
          dt = DatamineThread (queue_content, queue_content_stilized)
          dt.setDaemon (True)
          dt.start()
          thethreads.append(dt)
    except Exception, e:
      for t in thethreads:
        t.stop()
      logger.erro(str(e) + " exception at datamine " )

    #wait on the queue until everything has been processed
    queue_urls.join()
    queue_content.join()

    starttime = time.time()

    while  queue_content_stilized.empty() != True:
      data.append (queue_content_stilized.get())
      if  time.time()-starttime > 25:
        for t in thethreads:
          t.terminate()
        logger.fatal("Timeout")
        sys.exit(100)  
        


  data = randomize_filecontents (data, options.minword, options.maxword, options.cut_long_for_maxlimit, options.cut_long_for_minlimit,  options.scramble_force, options.scramble_random, options.fout)
  do_writefile(data, options.fout, options.wordscount)

if __name__ == "__main__":

  main()

