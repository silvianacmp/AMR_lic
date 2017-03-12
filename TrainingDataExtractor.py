from AMRGraph import AMR
from tqdm import tqdm
import AMRData
import ActionSequenceGenerator
import NamedEntityReplacer
import SentenceAMRPairsExtractor
import logging


# Given a file with sentences and aligned amrs,
# it returns an array of (sentence, action_sequence, amr_string))
def generate_training_data(file_path, verbose=True):
    if verbose is False:
        logging.disable(logging.WARN)

    sentence_amr_pairs = SentenceAMRPairsExtractor.extract_sentence_amr_pairs(file_path)
    fail_sentences = []
    training_data = []

    for i in tqdm(range(0, len(sentence_amr_pairs))):
        try:
            logging.warn("Started processing example %d", i)
            (sentence, amr_str) = sentence_amr_pairs[i]
            amr = AMR.parse_string(amr_str)
            (new_amr, new_sentence, _) = NamedEntityReplacer.replace_named_entities(amr, sentence)
            custom_amr = AMRData.CustomizedAMR()
            custom_amr.create_custom_AMR(new_amr)
            action_sequence = ActionSequenceGenerator.generate_action_sequence(custom_amr, sentence)
            training_data.append((new_sentence, action_sequence, amr_str))
        except Exception as e:
            logging.warn(e)
            fail_sentences.append(sentence)
            logging.warn("Failed at: %d", i)
            logging.warn("%s\n", sentence)

    logging.critical("Failed: %d out of %d", len(fail_sentences), len(sentence_amr_pairs))
    return training_data
