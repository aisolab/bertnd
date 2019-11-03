import argparse
import pickle
import torch
import torch.nn as nn
from pathlib import Path
from torch.utils.data import DataLoader
from transformers.modeling_bert import BertConfig
from transformers.tokenization_bert import BertTokenizer
from model.net import BertClassifier
from model.data import Corpus
from model.utils import PreProcessor, PadSequence
from model.metric import evaluate, acc
from utils import Config, CheckpointManager, SummaryManager

parser = argparse.ArgumentParser()
parser.add_argument("--data_dir", default="ind_trec_ood_sst2", help="directory containing config.json of data")
parser.add_argument("--model_dir", default="experiments/ind_trec_ood_sst2",
                    help="directory containing config.json of model")
parser.add_argument("--type", default="bert-base-uncased", help="pretrained weights of bert")
parser.add_argument("--data", default="test_ind", help="evaluating specific data")


if __name__ == "__main__":
    args = parser.parse_args()
    data_dir = Path("dataset") / args.data_dir
    model_dir = Path(args.model_dir)
    ptr_dir = Path("pretrained")
    data_config = Config(data_dir / "config.json")
    model_config = Config(model_dir / "config.json")

    # tokenizer
    ptr_tokenizer = BertTokenizer.from_pretrained(
        args.type, do_lower_case="uncased" in args.type
    )
    vocab_filepath = ptr_dir / "{}-vocab.pkl".format(args.type)
    with open(vocab_filepath, mode="rb") as io:
        vocab = pickle.load(io)
    pad_sequence = PadSequence(
        length=model_config.length, pad_val=vocab.to_indices(vocab.padding_token)
    )
    preprocessor = PreProcessor(
        vocab=vocab, split_fn=ptr_tokenizer.tokenize, pad_fn=pad_sequence
    )

    # model (restore)
    checkpoint_manager = CheckpointManager(model_dir)
    checkpoint = checkpoint_manager.load_checkpoint("best.tar")
    config_filepath = ptr_dir / "{}-config.json".format(args.type)
    config = BertConfig.from_pretrained(config_filepath, output_hidden_states=False)
    model = BertClassifier(
        config, num_classes=model_config.num_classes, vocab=preprocessor.vocab
    )
    model.load_state_dict(checkpoint["model_state_dict"])

    # evaluation
    filepath = getattr(data_config, args.data)
    ds = Corpus(filepath, preprocessor.preprocess)
    dl = DataLoader(ds, batch_size=model_config.batch_size, num_workers=4)

    device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
    model.to(device)

    summ = evaluate(model, dl, {"loss": nn.CrossEntropyLoss(), "acc": acc}, device)

    summary_manager = SummaryManager(model_dir)
    summary_manager.load("summary.json")
    summary_manager.update({"{}".format(args.data): summ})
    summary_manager.save("summary.json")

    print("loss: {:.3f}, acc: {:.2%}".format(summ["loss"], summ["acc"]))
