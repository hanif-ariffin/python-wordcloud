import requests
from html2text import html2text
from nltk.probability import FreqDist
from nltk.corpus import brown
from collections import Counter
from pickle import dump, load
from wordcloud import WordCloud
from nltk.tokenize import TweetTokenizer
import matplotlib.pyplot as plt
import os

# See https://github.com/4chan/4chan-API for more info

tokenizer = TweetTokenizer()

for board in requests.get('https://a.4cdn.org/boards.json').json()['boards']:
  try:
    print('Board: {} ({})'.format(board['board'], board['title']))

    try:
      # Load word counts for this board from a file, if available
      with open('{}.counts'.format(board['board']), 'rb') as file:
        counter = load(file)

    except:
      # Create list of thread IDs
      threads = [
        thread['no']
        for page in requests.get('https://a.4cdn.org/{}/threads.json'.format(board['board'])).json()
        for thread in page['threads']
      ] + requests.get('https://a.4cdn.org/{}/archive.json'.format(board['board'])).json()
      
      threads = threads[:200] # Limit to last 200 threads at most (faster)

      # Count words in every thread and every post
      counter = Counter()
      for index, thread in enumerate(threads):
        print('Thread {} ({} / {})'.format(thread, index, len(threads)))
        for post in requests.get('https://a.4cdn.org/{}/thread/{}.json'.format(board['board'], thread)).json()['posts']:
          if 'sub' in post:
            text = html2text(post['sub']).lower()
            counter.update(token for token in tokenizer.tokenize(text) if token.isalpha())
          if 'com' in post:
            text = html2text(post['com']).lower()
            counter.update(token for token in tokenizer.tokenize(text) if token.isalpha())
      
      # Store word counts for this board in a file
      with open('{}.counts'.format(board['board']), 'wb') as file:
        dump(counter, file)

    # Create word cloud and save it if it doesn't exist
    if not os.path.isfile('{}.png'.format(board['board'])):

      # Reference frequencies of English words 
      freq = FreqDist(word.lower() for word in brown.words())
      for word in counter:
        counter[word] /= 1 + freq[word]

      del counter[board['board']] # Remove board name
      for word in tokenizer.tokenize(board['title'].lower()):
        del counter[word] # Remove other keywords

      cloud = WordCloud(scale=10, max_words=2000).fit_words(counter)
      plt.imsave('{}.png'.format(board['board']), cloud)

  except Exception as e:
    print('ERROR: {}'.format(e))
    continue # Error occurred, skip this board for now