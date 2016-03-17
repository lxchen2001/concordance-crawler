from traceback import format_exc
import logging
import requests
import ConcordanceCrawler.core.links as links
from ConcordanceCrawler.core.visitor import *
from ConcordanceCrawler.core.bazwords import *
from ConcordanceCrawler.core.visible_text import filter_link_by_format

class CrawlerConfigurator(object):
	'''configurable attributes of ConcordanceCrawler can be set via
	this method'''

	def setup(self, **kwargs):
		visitor = Visitor()
		for atr in kwargs.keys():
			if atr in Visitor.attributes:
				setattr(visitor, atr, kwargs[atr])
			elif atr in ConcordanceCrawler.attributes:
				setattr(self, atr, kwargs[atr])
			else:
				raise AttributeError("Attribute '{0}' is not known and cannot be set.".format(atr))
		self.visitor = visitor
	
class ConcordanceCrawler(CrawlerConfigurator):	
	attributes = ["bazgen", "filter_link"]

	def __init__(self, words, bazgen=None):
		'''words: a list of strings, words, whose concordances should be
		crawled. It should a single word, or a single word and its other forms.
		The first one is considered as a basic form, links will be find only
		with this form.'''
		self.basic_word = words[0]
		self.all_words = words
		if bazgen:
			self.bazgen = bazgen
		else:
			self.bazgen = RandomShortWords()
		self.filter_link = filter_link_by_format
		self.visitor = Visitor() # it will work even without setup
		self.page_limited = False
		self._exceptions_handlers = dict()
		self._ignored_exceptions = set()

		# if False, yield links ends
		self.crawling_allowed = True


	def yield_concordances(self,words):
		'''Generator crawling concordances'''

		for link in self._yield_links():
#			link['link'] = 'http://gimli.ms.mff.cuni.cz/////'
			if not self.crawling_allowed:
				break
			for con in self._yield_concordances_from_link(link):
				yield con

	def crawl_links(self):
		return links.crawl_links(self.basic_word,1, bazword_gen=self.bazgen)

	def _yield_links(self):
		'''Generator yielding links from search engine result page. It scrapes
		one serp, parses links and then yields them. Then again.
		'''
		while self.crawling_allowed:
			try:
				links = self.crawl_links()
				for l in links:
					if self.filter_link(l["link"]):
						yield l
			except Exception as e:
				if any((issubclass(type(e),t) for t in self._exceptions_handlers.keys())):
					self._handle_exception(e)
				elif all(not issubclass(type(e),t) for t in self._ignored_exceptions):
					raise

	def set_exception_handler(self, exc_class, handler):
		if exc_class in self._ignored_exceptions:
			raise Exception("cannot set exception handler on '{0}', it's already among "
				"ignored exceptions".format(exc_class))
		self._exceptions_handlers[exc_class] = handler

	def ignore_exception(self,exc_class):
		if exc_class in self._exceptions_handlers.keys():
			raise Exception("cannot ignore exception '{0}', it's already among "
				"handled exceptions".format(exc_class))
		self._ignored_exceptions.add(exc_class)

	def _handle_exception(self,exc):
		'''finds the most suitable exception handler and calls it'''
		mro = type(exc).mro()
		for c in mro:
			if c in self._exceptions_handlers.keys():
				self._exceptions_handlers[c](exc)
				return
		# TODO -- remove?
		print("handler is not found")

	def concordances_from_link(self, link):
		return self.visitor.concordances_from_link(link,self.all_words)

	def _yield_concordances_from_link(self,l):
		'''This generator gets link as an argument, downloads the page, parses
		concordances and yields them.

		Args:
			l -- link, a dictionary structure coming from module visitor of
			ConcordanceCrawler
		'''
		# this comments are for debugging:
		#l['link']='https://www.diffchecker.com/'
		#l['link']='http://en.bab.la/dictionary/english-hindi/riding'
		#print("link:",l['link'])
		try:
			# here is the link visited
			concordances = self.concordances_from_link(l)
			if not concordances:
				return
			for i,c in enumerate(concordances):
				# maximum limit of concordances per page reached
				if self.page_limited and i>self.max_per_page:
					break
				# here is formed the output structure for concordance
				res = c
				yield res
		except Exception as e:
			if any((issubclass(type(e),t) for t in self._exceptions_handlers.keys())):
				self._handle_exception(e)
			elif all(not issubclass(type(e),t) for t in self._ignored_exceptions):
				raise

		






if __name__=='__main__':
	print("ahoj")
	#setup_logger(0)
	x = ConcordanceCrawler("exception", RandomShortWords())
	try:
		x.setup(abc="nic")
	except AttributeError:
		print("it's ok")
	import ConcordanceCrawler.core.language_analysis as language_analysis
	def mypredict(*a, **kw):
		print("mypredict is called!")
		return language_analysis.predict_language(*a,**kw)
	x.setup(predict_language = mypredict)
	x.log_state()

	for i in x._yield_concordances_from_link({"link":'https://docs.python.org/2/library/exceptions.html'}):
		print(i)
	print("done")