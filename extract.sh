#!/bin/bash

python -m wikiextractor.WikiExtractor \
   -b 10M \
   -o extracted \
   --json \
   --no-templates \
   zhwiki-20250701-pages-articles-multistream.xml.bz2