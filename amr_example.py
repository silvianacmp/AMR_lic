from __future__ import print_function
import dynet as dy
import deep_dynet.support as ds
import deep_dynet.transition_parser as ddtp
import logging
from os import listdir, path, makedirs
import TrainingDataExtractor as tde
import json as js
from smatch import smatch_amr
from smatch import smatch_util
import numpy as np
import matplotlib.pyplot as plt


def generate_parsed_data(parsed_path, dump_path):
    dump_path = dump_path + ".dump"
    # print(dump_path)
    if path.exists(dump_path):
        with open(dump_path, "rb") as f:
            return js.load(f)
    data = tde.generate_training_data(parsed_path, False)
    if not path.exists(path.dirname(dump_path)):
        makedirs(path.dirname(dump_path))
    with open(dump_path, "wb") as f:
        js.dump(data, f)  # , indent=4, separators=(',', ': ')
    return data


def read_data(type, filter_path = "deft"):
    mypath = 'resources/alignments/split/' + type
    print(mypath + " with filter " + filter_path)
    data = []
    directory_content = listdir(mypath)
    original_corpus = filter(lambda x: "dump" not in x, directory_content)
    original_corpus = filter(lambda x: filter_path in x, original_corpus)
    for f in original_corpus:
        mypath_f = mypath + "/" + f
        dumppath_f = mypath + "/dumps/" + f
        print(mypath_f)
        data += generate_parsed_data(mypath_f, dumppath_f)
    return data


def process_data(data, vocab_words, vocab_acts):
    for d in data:
        sentence = d[0]
        actions = d[1]
        amr_str = d[2]
        yield (
            ds.word_sentence_to_vocab_index(sentence.split(), vocab_words),
            ds.oracle_actions_to_action_index(actions, vocab_acts),
            sentence,
            actions,
            amr_str
        )

vocab_acts = ds.Vocab.from_list(ddtp.acts)
vocab_words = ds.Vocab.from_file('resources/data/vocab.txt')

# tests = ["bolt", "dfa", "proxy", "xinhua", "deft"]
tests = ["deft"]
cases = []
for filter_path in tests:
    training_data = read_data("training", filter_path=filter_path)
    # dev_data = read_data("dev")
    test_data = read_data("dev", filter_path)
    print("%s Training size %d" % (filter_path, len(training_data)))
    print("%s Test size %d" % (filter_path, len(test_data)))


    # train = list(ds.read_oracle('resources/data/amr-examples.txt', vocab_words, vocab_acts))
    # dev = list(ds.read_oracle('resources/data/amr-examples-test.txt', vocab_words, vocab_acts))
    train = list(process_data(training_data, vocab_words, vocab_acts))
    test = list(process_data(test_data, vocab_words, vocab_acts))
    cases.append((filter_path, train, test))

for run in range(1):
    for (filter_path, train, test) in cases:
        model = dy.Model()
        trainer = dy.AdamTrainer(model)

        tp = ddtp.TransitionParser(model, vocab_words)

        log_errors_on_train = False
        if (log_errors_on_train):
            logging.disable(logging.NOTSET)
        # cmake .. -DEIGEN3_INCLUDE_DIR=/Users/flo/Documents/Doctorat/AMR/dynet-base/eigen -DBOOST_ROOT=/usr/local/opt/boost160/ -DPYTHON=/usr/bin/python
        accuracies = []
        rounds = 0
        best_epoch = 0
        fail_sentences = []
        for epoch in range(10):
            smatch_train_results = smatch_util.SmatchAccumulator()
            for (sentence, actions, original_sentence, original_actions, amr) in train:
                loss = None
                try:
                    parsed = tp.parse(sentence, actions)
                    loss = parsed[0]
                    parsed_amr = parsed[1]

                    parsed_amr_str = parsed_amr.amr_print()
                    original_amr = smatch_amr.AMR.parse_AMR_line(amr)
                    parsed_amr = smatch_amr.AMR.parse_AMR_line(parsed_amr_str)
                    smatch_f_score = smatch_train_results.compute_and_add(parsed_amr, original_amr)

                    # print("Generated")
                    # print(parsed_amr_str)
                    # print("Expected")
                    # print(amr)
                    # print(">>> %f" % smatch_f_score)

                except Exception as e:
                    logging.warn(e)
                    fail_sentences.append(original_sentence)
                    logging.warn("%s\n with actions %s\n", original_sentence, original_actions)
                if loss is not None:
                    # for some weird reason backward throws an failed assertion if there is no scalar value retrievall
                    loss.scalar_value()
                    loss.backward()
                    trainer.update()

            print ("Train:")
            smatch_train_results.print_all()

            dev_words = 0
            dev_loss = 0.0
            right_predictions = 0.0
            total_predictions = 0
            fail_sentences = []

            smatch_test_results = smatch_util.SmatchAccumulator()
            for (ds, da, original_sentence, original_actions, amr) in test:
                loss = None
                try:
                    parsed_sentence = tp.parse(ds, da)
                    loss = parsed_sentence[0]
                    parsed_amr = parsed_sentence[1]
                    right_predictions += parsed_sentence[2]
                    total_predictions += parsed_sentence[3]
                    dev_words += len(ds)

                    parsed_amr_str = parsed_amr.amr_print()
                    original_amr = smatch_amr.AMR.parse_AMR_line(amr)
                    parsed_amr = smatch_amr.AMR.parse_AMR_line(parsed_amr_str)
                    smatch_f_score = smatch_test_results.compute_and_add(parsed_amr, original_amr)

                    # print(">>> %f" % smatch_f_score)
                    if 1 > smatch_f_score > 0.9:
                        print("Generated")
                        print(parsed_amr_str)
                        print("Expected")
                        print(amr)

                except Exception as e:
                    logging.warn(e)
                    fail_sentences.append(original_sentence)
                    logging.warn("%s\n with actions %s\n", original_sentence, original_actions)
                if loss is not None:
                    dev_loss += loss.scalar_value()
            # print("Failed sentencs in test: %d" % len(fail_sentences))
            loss_dev_words = dev_loss / total_predictions
            accuracy = right_predictions / total_predictions
            # print('[validation] epoch {}: per-word loss: {} prediction accuracy: {}'.format(epoch, loss_dev_words, accuracy))
            accuracies.append(accuracy)
            hist_bins = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.99, 1]
            hist, bins = np.histogram(smatch_test_results.smatch_scores, bins=hist_bins)
            print("%s in bins %s" % (hist, bins))
            print("Test:")
            print("Accuracy %f" % accuracy)
            smatch_test_results.print_all()
            plt.hist(smatch_test_results.smatch_scores, hist_bins)
            plt.show()

        print("run ", run, ": accuracies ", accuracies)
        print("{} since {} max accuracy {} for {} rounds. Train {} Test {}".format(filter_path, np.argmax(accuracies), np.max(accuracies), rounds, len(train), len(test)))
