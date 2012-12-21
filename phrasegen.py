#!//usr/bin/python
# -*- coding: utf-8 -*-
#
# Phrase generator (phrasegen) for creating random(?) password phrases from given input, file or urls.
#
# Copyright (C) 2012 Jani Päijänen, jani dot paijanen [at] gmail dot com
# License: Freeware. 
# Please consider making a donation to some local charity program near you.


import random
from optparse import OptionParser
import operator
import re
import sys
import urllib
import urlparse
import Queue
import threading
try:
	from BeautifulSoup import BeautifulSoup, Comment
except ImportError, e:
	print >> sys.stderr, "install BeautifulSoup"
	sys.exit(1)
import time 

class MyOpener (urllib.FancyURLopener):
	version = 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.15) Gecko/20131019 phrage-net.py/1.0.1'


Newlines = re.compile (r'[\r\n]\s+')

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

	def run (self):
		  while True:
		      #grabs host from queue
		      url=None
		      text=""
		      if self.queue != None:
		        url = self.queue.get ()

		      try:
		        if url != None:
		          myopener = MyOpener ()
		          #page = urllib.urlopen(url)
		          page = myopener.open (url)
		          Dout ("url %s" % url)
		        if page:
		          text = page.read ()
		          page.close ()
		      except Exception, e: 
		        Dout (url + " "  + str(e))


		      #place chunk into out queue
		      self.out_queue.put (text)

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
              Dout (str(e))

            #signals to queue job is done
            self.out_queue.task_done()

def fetch_url(url):
	myopener = MyOpener()
	#page = urllib.urlopen(url)
	page = myopener.open(url)
	 
	text = page.read()
	page.close()
	return stilize_page(text)

def stilize_page(text):
	try:
		bs = BeautifulSoup(text, convertEntities=BeautifulSoup.HTML_ENTITIES)
		# kill javascript content
		#for s in bs.findAll('script'):
		#	  s.replaceWith('')

		#for s in bs.findAll('img'):
		#	  s.replaceWith('')

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
		Dout (msg)

	return None

def Dout(msg, level=5):
  print (msg)
  pass

def randomize_filecontents(data, words_count, min_length, max_length, cut_long_for_maxlimit, cut_long_for_minlimit, db=None, fout=None):

  contents = []
  #Dout data
  for line in data:
    liner = []
    i=0
    if line == None: continue
    for w in line.split():
  	  l = len(w)
  	  
  	  if ( (cut_long_for_minlimit == True) and l >= min_length) : 
  	    if (cut_long_for_maxlimit == False):
	        if l <= max_length:
  	    	  liner.append(w)
  	    	  i=1
  	    else:
 	    	  liner.append(w[:max(min_length, max_length)])
 	    	  i=1
  	  elif (cut_long_for_minlimit == False):
  	    liner.append(w[:min(min_length, max_length)])
  	    i=1

    if i > 0:
      contents += liner

  result = []
  random.shuffle(contents)
  con_length = len(contents)
  
  while con_length >1:
    line = ""
    r = 0
    while r < words_count:
      index = random.randint(0, con_length-1)
      #element = random.choice(contents)
      element = contents.pop(index)
      con_length = len(contents)
      if  con_length <= 1 : break
      #contents.remove(element)

      if len(line) > 0:
        line = line + " " + element
      else:
        line = element
      r += 1 
    
    result.append(line)

  if fout!=None:
    out=open(fout, "w")
    for r in result:
			try:
			  out.write(r +"\n")
			except Exception, e:
			  pass
    out.close()
  else:
    for r in result:
      try:
        Dout (unicode(r))
      except UnicodeEncodeError, e:
 	#print >> sys.stderr, str(e)
        pass
      except UnicodeDecodeError, e:
        pass
   



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

  parser.add_option ( "--any-url", dest="any_url", default=None, action="append", type="string",
                    help="List of URLS of which one will be randomly selected. Can be used several times.")

  parser.add_option ( "--default-urls", dest="default_urls", default=False, action="store_true",
                    help="Use list of default URLS")

  parser.add_option ( "--stdin", dest="stdin", default=False, 
                    action="store_true", help="Read from stdin")

  parser.add_option ( "--fout", dest="fout", default=None, 
                    action="store", type="string", help="File out")


  parser.add_option("-q", "--quiet",
                    action="store_false", dest="verbose", default=True,
                    help="don't print status messages to stdout")

  (options, args) = parser.parse_args()

  if options.default_urls == True:
    options.urls="https://fi.wikipedia.org/wiki/Special:Random http://hikipedia.info/wiki/Toiminnot:Satunnainen_sivu http://www.gutenberg.org/files/7000/7000-h/7000-h.htm  https://fi.wikipedia.org/wiki/Luettelo_E-koodatuista_aineista"

    if options.any_url == None:
      options.any_url = []

    options.any_url.append ("https://se.wikipedia.org/wiki/Special:Random")
    options.any_url.append ("https://de.wikipedia.org/wiki/Special:Random")
    options.any_url.append ("https://en.wikipedia.org/wiki/Special:Random")
    options.any_url.append ("http://en.wikiquote.org/wiki/Special:Random")
    options.any_url.append ("http://fi.wikiquote.org/wiki/Special:Random")
    options.any_url.append ("http://se.wikiquote.org/wiki/Special:Random")
    options.any_url.append ("http://de.wikiquote.org/wiki/Special:Random" )
    options.any_url.append ("https://en.wikipedia.org/wiki/Wikipedia:List_of_all_single-digit-single-letter_combinations")
    options.any_url.append ("https://en.wikipedia.org/wiki/List_of_medical_roots,_suffixes_and_prefixes")
    options.any_url.append ("https://en.wikipedia.org/wiki/List_of_abbreviations_used_in_medical_prescriptions")
    options.any_url.append ("https://en.wikipedia.org/wiki/Acronyms_in_healthcare")
    options.any_url.append ("https://en.wikipedia.org/wiki/E_number")
    options.any_url.append ("https://en.wikipedia.org/wiki/List_of_food_additives,_Codex_Alimentarius")
    options.any_url.append ("https://en.wikipedia.org/wiki/List_of_food_additives")
    options.any_url.append ("https://en.wikipedia.org/wiki/Wikipedia:List_of_all_single-letter-double-digit_combinations")
    options.any_url.append ("http://www.hs.fi")
    options.any_url.append ("http://www.ksml.fi")
    options.any_url.append ("http://www.ilkka.fi")
    options.any_url.append ("http://www.turunsanomat.fi")
    options.any_url.append ("http://www.parikkalan-rautjarvensanomat.fi")
    options.any_url.append ("http://www.saynatsalonsanomat.fi")
    options.any_url.append ("http://www.kaleva.fi")
    options.any_url.append ("http://www.maaseuduntulevaisuus.fi")


  if options.any_url != None:
      #print options.any_url
      for u in options.any_url:
        urls=u.split()
        #print "urls_provided %d" % len(urls)
        random.shuffle (urls)
        if options.urls == None: 
          options.urls=""
          options.urls = options.urls +  random.choice(urls)
        else:
          options.urls = options.urls + " " +  random.choice(urls)

  #if options.urls != None:
  #  Dout( "Using urls: %s" % options.urls)
  #  Dout("")


  if options.randomizefile == None and options.stdin == False and options.urls ==None:
    parser.print_help()
    Dout ("Phrase generator (phrage) for creating random(?) password phrases from given URLs.")
    Dout ("Try either row from below to see how it works. ")
    Dout (' egrep -v "^[ ]*$|^#" "phrasegen.py" | grep -v ===  | phrasegen.py --stdin --maxword=13 --wordscount=8 --minword=3 --dont-cut-long-for-maxlimit | sed s@\ @@g | cut -c 1-32')

  data = []
  if options.randomizefile != None:

    f = open(options.randomizefile, "r")
    for line in f:
      line = line.strip ()
      if len (line) == 0: continue
      data.append (line)
    #randomize_filecontents(data, options.wordscount, options.minword, options.maxword, options.cut_long_for_maxlimit, options.cut_long_for_minlimit)
    f.close()
  elif options.stdin == True:
    #data = []
    for line in sys.stdin:
      line = line.strip()
      if len (line) == 0: continue
      data.append (line)
    #randomize_filecontents(data, options.wordscount, options.minword, options.maxword, options.cut_long_for_maxlimit, options.cut_long_for_minlimit)
  elif options.urls != None:
    #data = []

    thethreads = []

    local_urls = options.urls.split()
    urlcount = len(local_urls)

    try:

      #Dout("Thread count: %d" % urlcount)

		  #spawn a pool of threads, and pass them queue instance
      for i in range(urlcount):
          t = ThreadUrl (queue_urls, queue_content)
          thethreads.append(t)
          t.setDaemon (True)
          t.start()


    except Exception, e:
      Dout ( str(e) + " exception at urls" ) 
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
      Dout ( str(e) + " exception at datamine " ) 

    #wait on the queue until everything has been processed
    queue_urls.join()
    queue_content.join()

    starttime = time.time()

    while	 queue_content_stilized.empty() != True:
			data.append (queue_content_stilized.get())
			if  time.time()-starttime > 25:
			  for t in thethreads:
			    t.terminate()
			  Dout("Timeout")
			  sys.exit(100)  
        

    #for u in options.urls.split():
      #print u
    #  data.append ( fetch_url(u))
    #print (data, options.wordscount, options.minword, options.maxword)

  randomize_filecontents (data, options.wordscount, options.minword, options.maxword, options.cut_long_for_maxlimit, options.cut_long_for_minlimit,  options.fout)
	

if __name__ == "__main__":

  main()

