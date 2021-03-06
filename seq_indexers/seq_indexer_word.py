"""
.. module:: SeqIndexerWord
    :synopsis: SeqIndexerWord converts list of lists of words as strings to list of lists of integer indices and back.

.. moduleauthor:: Artem Chernodub
"""

import string
import numpy as np
import re
import torch
#from jellyfish import soundex
from autocorrect import spell

from seq_indexers.seq_indexer_base_embeddings import SeqIndexerBaseEmbeddings

class SeqIndexerWord(SeqIndexerBaseEmbeddings):
    def __init__(self, gpu=-1, check_for_lowercase=True, embeddings_dim=0, verbose=True):
        SeqIndexerBaseEmbeddings.__init__(self, gpu=gpu, check_for_lowercase=check_for_lowercase, zero_digits=True,
                                          pad='<pad>', unk='<unk>', load_embeddings=True, embeddings_dim=embeddings_dim,
                                          verbose=verbose)
        self.original_words_num = 0
        self.lowercase_words_num = 0
        self.zero_digits_replaced_num = 0
        self.zero_digits_replaced_lowercase_num = 0

    def get_embeddings_word(self, word, embeddings_word_list):
        if word in embeddings_word_list:
            self.original_words_num += 1
            return word
        elif self.check_for_lowercase and word.lower() in embeddings_word_list:
            self.lowercase_words_num += 1
            return word.lower()
        elif self.zero_digits and re.sub('\d', '0', word) in embeddings_word_list:
            self.zero_digits_replaced_num += 1
            return re.sub('\d', '0', word)
        elif self.check_for_lowercase and self.zero_digits and re.sub('\d', '0', word.lower()) in embeddings_word_list:
            self.zero_digits_replaced_lowercase_num += 1
            return re.sub('\d', '0', word.lower())
        return None

    def load_items_from_embeddings_file_and_unique_words_list(self, emb_fn, emb_delimiter, unique_words_list):
        # Get the full list of available case-sensitive words from text file with pretrained embeddings
        embeddings_words_list = [emb_word for emb_word, _ in SeqIndexerBaseEmbeddings.load_embeddings_from_file(emb_fn,
                                                                                                          emb_delimiter,
                                                                                                          verbose=True)]
        # Create reverse mapping word from the embeddings file -> list of unique words from the dataset
        emb_word_dict2unique_word_list = dict()
        out_of_vocabulary_words_list = list()
        for unique_word in unique_words_list:
            emb_word = self.get_embeddings_word(unique_word, embeddings_words_list)
            if emb_word is None:
                out_of_vocabulary_words_list.append(unique_word)
            else:
                if emb_word not in emb_word_dict2unique_word_list:
                    emb_word_dict2unique_word_list[emb_word] = [unique_word]
                else:
                    emb_word_dict2unique_word_list[emb_word].append(unique_word)
        # Add pretrained embeddings for unique_words
        for emb_word, emb_vec in SeqIndexerBaseEmbeddings.load_embeddings_from_file(emb_fn, emb_delimiter,verbose=True):
            if emb_word in emb_word_dict2unique_word_list:
                for unique_word in emb_word_dict2unique_word_list[emb_word]:
                    self.add_item(unique_word)
                    self.add_emb_vector(emb_vec)
        if self.verbose:
            print('\nload_vocabulary_from_embeddings_file_and_unique_words_list:')
            print('    First 50 OOV words:')
            for i, oov_word in enumerate(out_of_vocabulary_words_list):
                print('        out_of_vocabulary_words_list[%d] = %s' % (i, oov_word))
                if i > 49:
                    break
            print(' -- len(out_of_vocabulary_words_list) = %d' % len(out_of_vocabulary_words_list))
            print(' -- original_words_num = %d' % self.original_words_num)
            print(' -- lowercase_words_num = %d' % self.lowercase_words_num)
            print(' -- zero_digits_replaced_num = %d' % self.zero_digits_replaced_num)
            print(' -- zero_digits_replaced_lowercase_num = %d' % self.zero_digits_replaced_lowercase_num)

    def get_unique_characters_list(self, verbose=False, init_by_printable_characters=True):
        if init_by_printable_characters:
            unique_characters_set = set(string.printable)
        else:
            unique_characters_set = set()
        if verbose:
            cnt = 0
        for n, word in enumerate(self.get_items_list()):
            len_delta = len(unique_characters_set)
            unique_characters_set = unique_characters_set.union(set(word))
            if verbose and len(unique_characters_set) > len_delta:
                cnt += 1
                print('n = %d/%d (%d) %s' % (n, len(self.get_items_list), cnt, word))
        return list(unique_characters_set)
