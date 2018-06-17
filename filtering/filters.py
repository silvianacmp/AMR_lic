from amr_util import TrainingDataStats
from amr_util.amr_projectivity import get_projective_order, is_perfectly_aligned
from amr_util.amr_projectivity import AmrNotPerfectlyAlignedTreeException

"""
this file contains the filters that can be applied on the data
each filter contains an is_ok method:
    sentence: a sentence given as a list of strings
    custom_amr: an amr graph given as a set of dictionaries (instance of a CustomizedAMR)
    amr_id: a string, the id of a sentence-amr pair
    returns: a boolean
"""


class NoMissingAllignmentInfoFilter():

    def __init__(self):
        self.name = "NoMissingAllignmentInfoFilter"

    """
    this filter checks that alignment information is not missing
    aka, each node in the graph has at least 1 token associated with it
    """
    def is_ok(self,sentence,amr, custom_amr,amr_id):

        # for key in custom_amr.relations_dict.keys():
        #     aligned_tokens = custom_amr.relations_dict[key][2]
        #     if len(aligned_tokens) == 0:
        #         # this node has no aligned token
        #         return False
        # return True

        unaligned_nodes = {}
        TrainingDataStats.get_unaligned_nodes(amr,unaligned_nodes)
        return len(unaligned_nodes) == 0


class TreeFilter():

    def __init__(self):
        self.name = "TreeFilter"

    """
    this filter checks the amr is a tree
    for a graph to be a tree, it should be conex (assume true) and have n-1 edges
    """
    def is_ok(self, sentence, amr, custom_amr, amr_id):
        no_of_edges = len(custom_amr.relations_dict)-1

        nodes = []

        for key in custom_amr.relations_dict.keys():
            node = key[0]
            if node not in nodes:
                nodes.append(node)
            elif node in ['-','interogative','expressive']:
                nodes.append(node)

        no_of_nodes = len(nodes)

        if no_of_nodes == 1:
            return True

        return no_of_nodes-1 == no_of_edges


class TokenToNodeAlignmentFilter():

    """
    this filter checks there is a 1:0..n allignment between the tokens of a sentence and the nodes of the graph
    """
    def __init__(self,n):
        self.n = n
        self.name = "TokenTo"+str(n)+"Node(s)AlignmentFilter"

    #check each token has up to n nodes associated with it
    def is_ok(self,sentence,amr,custom_amr,amr_id):

        for token in range(0,len(sentence)):
            if token in custom_amr.tokens_to_concept_list_dict.keys():
                if len(custom_amr.tokens_to_concept_list_dict[token]) > self.n:
                    return False
        return True

class PerfectALignmentFilter():
    """
    this filter checks that for each token there is at most one node
    and for each node at least one token
    """
    def __init__(self):
        self.name = "ProjectiveTreeFilter"

    def is_ok(self, sentence, amr, custom_amr, amr_id):
        return is_perfectly_aligned(custom_amr)


class ProjectiveTreeFilter():

    """
    this filter checks that the tokens in the sentence are in projective order
    preconditions: amr is an aligned tree
    """
    def __init__(self):
        self.name = "ProjectiveTreeFilter"


    def is_ok(self,sentence,amr,custom_amr,amr_id):

        try:
            projective_order = get_projective_order(custom_amr,amr_id)
        except AmrNotPerfectlyAlignedTreeException as e:
            return False

        return all(projective_order[i] <= projective_order[i+1] for i in xrange(len(projective_order)-1))
