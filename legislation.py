#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Dec 19 18:06:44 2021

@author: ruixin
"""

import spacy 
import en_core_web_sm
from spacy.matcher import Matcher
from spacy.util import DummyTokenizer
from spacy.matcher import PhraseMatcher

class TokenizerWithFormatting(DummyTokenizer):
    # https://github.com/explosion/spaCy/issues/4160
    # https://github.com/explosion/spaCy/issues/5698
    def __init__(self, nlp):
        self.vocab = nlp.vocab
        self.tokenizer = nlp.tokenizer
        
        self.orph_paren_matcher = Matcher(self.vocab)
        pattern = [{'TEXT': {'REGEX': r'.\([^\(\)]+$'}}, {'ORTH': ')'}] # e.g. SLR(R ) and 8(b)(i ) 
        self.orph_paren_matcher.add('OrphanedParenthesis', [pattern])

    def __call__(self, text):
        doc = self.tokenizer(text)
        matches = self.orph_paren_matcher(doc)
        with doc.retokenize() as retokenizer:
            for _, start, end in matches:
                retokenizer.merge(doc[start:end]) # SLR(R ) => SLR(R)
        return doc

def num_pos_tagger(doc):
    for token in doc:
        for ch in token.text:
            if ch.isdigit():
                token.pos_ = 'NUM'
                break
    return doc

def get_para_no():
    for para in para_list:
        para_no = para_list.index(para) +1
        if match.text in para and (f"{str(para_no)}: {matched_word} ({title})") in match_with_titles:
            continue
        elif match.text in para:
            break
    return para_no

#gets the list of titles and code of a statute 
titles = []
codes = []
with open('legis_name.txt', 'r') as f:
    text = f.read()
    statutes = text.split('\n')[1:-1]
    for item in statutes:
        item = item.split(',')
        title = item[0].strip()
        shorthand = item[1].strip()
        index = 0
        for i in range(len(shorthand)):
            if shorthand[i].isdigit():
                index = i
                break
        statute_code = shorthand[:index]
        titles.append(title)
        codes.append(statute_code)


with open('2000_SGCA_55.txt', 'r') as f:
    test = f.read()
#test text
# test ="""Burswood Nominees similarly involved the registration of an Australian judgment for 
# gambling debts under the RECJA. In fact, like the present case, the underlying debt giving rise to 
# the Australian judgment in Burswood Nominees was also a debt incurred pursuant to an Australian casino’s 
# CCF (at [3]). The court held that, although the debt arising from the CCF took the form of a loan, it was 
# in substance a claim for money won upon a wager, which would have been caught by s 5(2) of the CLA if the 
# claim had been brought in a Singapore court in the first instance (at [21]–[22]). However, the court went 
# on to hold that, while s 5(2) of the CLA elucidates Singapore’s domestic public policy, s 3(2)(f) of the 
# RECJA requires a higher threshold of public policy to be met in order for the registration of a foreign judgment 
# to be refused (at [24]). The meeting of this higher threshold of public policy, described by the court as 
# “international” public policy, involves asking whether the domestic public policy in question was so important as to 
# form part of the core of essential principles of justice and morality shared by all nations (at [42]). The court held 
# that the domestic public policy encapsulated in s 5(2) of CLA did not meet this higher threshold (at [42]–[46]). 
# It therefore declined to set aside the registration of the Australian judgment."""

# test = "it has been 121(1) of the CPC states that"

#change to custom tokenizer 
nlp = en_core_web_sm.load()
nlp.tokenizer = TokenizerWithFormatting(nlp)
nlp.add_pipe(num_pos_tagger, name="pos_num", after='tagger')
doc = nlp(test)
para_list = doc.text.split('\n')
matcher = Matcher(nlp.vocab, validate=True)


#TODO add to patterns 
pattern = [
    [{"POS": "NUM"},{"LOWER":"of"},{"LOWER":"the"},{"TEXT":{"IN": codes}}],
    [{"POS": "NUM"},{"LOWER":"of"},{"TEXT":{"IN": codes}}],
    [{"POS": "NUM"},{"TEXT":{"IN": codes}}]
]
matcher.add("FindStatute", pattern)


#get matches for codes
matches = matcher(doc)
matchlist = []
for match_id, start, end in matches:
    string_id = nlp.vocab.strings[match_id]  # Get string representation
    span = doc[start:end]
    # item = (start, span)
    if span not in matchlist: 
        matchlist.append(span)  

#get matches for titles
titles_matcher = PhraseMatcher(nlp.vocab)
patterns = [nlp.make_doc(text) for text in titles]
titles_matcher.add("TitlesList", patterns)
title_matches = titles_matcher(doc)
if len(title_matches) != 0:
    for match_id, start, end in title_matches:
        string_id = nlp.vocab.strings[match_id]  
        start = 0
        for i in range(end, 0, -1):
            if doc[i].pos_ == 'NUM':
                start = i
                if start == end: #handles error that start index = end index
                    start = 0
                break
        if start != 0: #only when there is a number before the statute title
            span = doc[start:end]  
            # item = (start, span)
            if span not in matchlist: 
                matchlist.append(span)

#retreive the titles for respective statute codes found 
match_with_titles = []
for match in matchlist:
    words = str(match).split(' ')
    title = ''
    for word in words:
        if word in codes:
            index = codes.index(word)
            title = titles[index]
            break
    if len(title) != 0: #match has a statute code
        matched_word = ' '.join(words) 
        para_no = get_para_no()
        match_with_titles.append(f"{str(para_no)}: {matched_word} ({title})")
    else: #match has a title
        matched_word = ' '.join(words) 
        para_no = get_para_no()
        match_with_titles.append(f"{str(para_no)}: {matched_word}")


#output
if len(match_with_titles) == 0:
    print('No matches could be found')
else: 
    print(match_with_titles)