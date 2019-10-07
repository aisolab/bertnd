import pickle
from model.utils import Vocab
from pretrained.tokenization import BertTokenizer

# loading BertTokenizer
ptr_tokenizer = BertTokenizer.from_pretrained('pretrained/vocab.korean.rawtext.list', do_lower_case=False)
idx_to_token = list(ptr_tokenizer.vocab.keys())

# generate vocab
vocab = Vocab(idx_to_token, padding_token='[PAD]', unknown_token='[UNK]', bos_token=None, eos_token=None,
              reserved_tokens=['[CLS]', '[SEP]', '[MASK]'], unknown_token_idx=1)

# save vocab
with open('pretrained/vocab.pkl', mode='wb') as io:
    pickle.dump(vocab, io)
