#!/usr/bin/env python
# coding: utf-8

"""arXiv Search

Usage:
  arxiv.py id <arxiv_id> [--abstract] [--bib | --url | --pdf]
  arxiv.py search [-q=<query> | --query=<query>] [--author=<author>] [--category=<category>] [--period=<period>] [--limit=<limit>] [--score=<score>] [--abstract] [--bib | --url | --pdf]
  arxiv.py new [--author=<author>] [--category=<category>] [--period=<period>] [--limit=<limit>] [--score=<score>] [--abstract] [--bib | --url | --pdf]
  arxiv.py bib <arxiv_id> [--file=<file>]
  arxiv.py url <arxiv_id>
  arxiv.py pdf <arxiv_id>

Options:
  arxiv_id                      The ID of an arXiv paper 
  query                         A query string to search arXiv
  url, --url                    Opens the following arXiv id as a URL
  pdf, --pdf                    Opens the following arXiv id as a PDF
  bib, --bib                    Will print out bibtex entry for each matching result
  --category=<category>         The category to restrict searches to
  --author=<author>             The author to restrict searches to
  --limit=<limit>               The maximum number of results to retrieve
  --score=<score>               The score cutoff for the display of papers [default: 0]
  --period=<period>             The days into the past to retrieve results for  
  --abstract                    Will print out the abstract for each matching result
  --file=<file>                 The file to link to this entry.
"""

import os
import time
from docopt import docopt
args = docopt(__doc__, version='arXiv Search v1.2 (Noons Variant)')

from config import *
from score import score
from pyarxiv.arxiv import arXiv

arxiv = arXiv(DEFAULT_CATEGORIES, DEFAULT_LIMIT, INC_ABSTRACT, USE_BIBDESK, args['--file'])

# Retrieve and parse the query from arXiv
if args['<arxiv_id>']:
    r = arxiv.get_id(args['<arxiv_id>'])
else:
    if args['new'] and not args['--period']:
        args['--period'] = 0

    r = arxiv.search(**{
        'query':    args['-q'] or args['--query'],
        'period':   args['--period'],
        'author':   args['--author'], 
        'category': args['--category'],
        'limit':    args['--limit'],
    })

# Order articles by default category or not, then by date published
articles = sorted(r['articles'], 
    key=lambda x: (x['primary'] not in DEFAULT_CATEGORIES, x['published']))

# Filter articles that are below the score threshold
articles = [(a, score(a['title'], a['abstract'])) for a in articles]
articles = [(a, s) for (a, s) in articles if s >= int(args['--score'])]

# print "Showing: {0} of {1} retrieved results. Total results: {2}".format(
#     len(articles), len(r['articles']), r['total_results'])

if USE_BIBDESK:
    from pybibdesk.bibdesk import BibDesk
    bibdesk = BibDesk()

for (i, (a, key_score)) in enumerate(articles):
    # Output BibTeX references (and import into BibDesk if in use)
    if args['--bib'] or args['bib']:
        ref = arxiv.format_bibtex(a)
        print ref

        if USE_BIBDESK:
            bibdesk.import_reference(ref)
            
    # Open arXiv Link
    elif args['url'] or args['--url']:
        os.system("{0} {1}".format(OPEN_SOFTWARE, a['page_link']))

    # Open PDF Link
    elif args['pdf'] or args['--pdf']:
        os.system("{0} {1}".format(OPEN_SOFTWARE, a['pdf_link']))

    # Output formatted result
    else:
        mark = " ** " if a['primary'] not in DEFAULT_CATEGORIES else ""
        date = ""
        try:
            if a["published"]:
                date = time.strftime("%Y-%m-%d", a['published']) 
        except:
            pass

        print OUTPUT_FORMAT.format(**{
            'i':          (i+1),
            'mark':       mark,
            'cate':       a['primary'],
            'score':      key_score,
            'date':       date,
            'arxiv_id':   a['id'],
            'title':      arxiv.clean(a['title']),
            'author':     a['authors'],
        })

        if args['--abstract']:
            print "\n", a['abstract'], "\n"
