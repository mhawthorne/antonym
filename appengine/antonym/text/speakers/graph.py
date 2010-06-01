import logging
import random

from networkx import DiGraph

from antonym.core import NotImplementedException
from antonym.text import TextException
from antonym.text.speakers.core import calculate_length, Symbols


def _not_implemented():
    raise NotImplementedException()


class AbstractKeyedGraph:

    def add_node(self, key, **kw):
        _not_implemented()

    def find_node_by_key(self, key):
        _not_implemented()

    def iterator(self):
        """
        returns:
            GraphIterator
        """
        _not_implemented()

    def randomized_iterator(self):
        _not_implemented()
        
class DefaultKeyedGraph(AbstractKeyedGraph):

    def __init__(self):
        self.__root_nodes = {}

    def add_node(self, node, **kw):
        self.__root_nodes[node.key] = node

    def find_node_by_key(self, key):
        # TODO: use shortest path algorithm
        result = self.__root_nodes.get(key, None)
        if not result:
            for r in self.__root_nodes.values():
                result = r.find_by_key(key)
                if result:
                    break
        return result

    def describe_full(self):
        lines = []
        for r in self.__root_nodes.values():
            lines.append("\n%s" % r.describe_full())
        return "\n".join(lines)

    def __repr__(self):
        # TODO: make this less expensive after debugging
        return self.describe_full()


class AbstractKeyedGraphNode:
            
    def add_neighbor(self, node):
        _not_implemented()

    def find_by_key(self, key, walked_keys=None):
        _not_implemented()
        
    def get(self, key, default=None):
        _not_implemented()
        
    def set(self, **kw):
        _not_implemented()
        
    def has(self, key):
        _not_implemented()
    
    def describe_short(self):
        _not_implemented()
        
    def describe_full(self, indent=0, parents=None):
        _not_implemented()
        
    def iterator(self):
        """
        returns:
            GraphIterator
        """
        _not_implemented()

    def randomized_iterator(self):
        _not_implemented()


class DefaultNode(AbstractKeyedGraphNode):

    def __init__(self, key, **kw):
        self.key = key
        self.__neighbors = {}
        self.__properties = kw
        
    def add_neighbor(self, node):
        self.__neighbors[node.key] = node

    def find_by_key(self, key, walked_keys=None):
        result = self.__neighbors.get(key, None)
        if not result:
            for neighbor_key, node in self.__neighbors.iteritems():
                if walked_keys:
                    if neighbor_key in walked_keys:
                        continue
                else:
                    walked_keys = set([])
                walked_keys.add(neighbor_key)
                result = node.find_by_key(key, walked_keys)
                if result:
                    break
        return result

    def get(self, key, default=None):
        return self.__properties.get(key, default)
        
    def set(self, **kw):
        self.__properties.update(kw)
        
    def has(self, key):
        return self.__properties.has_key(key)
    
    def describe_short(self):
        return "%s('%s', key:%s, id:%s, neighbor_count:%d, props:%s)" % (self.__class__.__name__,
            self.key,
            id(self),
            len(self.__neighbors),
            self.__properties)

    def describe_full(self, indent=0, parents=None):
        """
        params:
            parents - set of keys already listed for the current root node.
                used to avoid infinite recursion.
        """
        level = "[%d]" % indent
        prop_str = self.__properties if self.__properties else ""
        lines = ["%s %s%s %s" % (level, " " * 2 * indent, self, prop_str)]
        
        if not parents:
            parents = set([])
            
        # adds self to list of parents to avoid infinite recursion
        parents.add(self.key)
        
        for n in self.__neighbors.values():
            if n.key in parents:
                # child is also a parent, don't recurse into it
                lines.append("%s %s%s ^" % (level, " " * 2 * (indent + 1), n.key))
                continue
            lines.append(n.describe_full(indent + 1, parents))
        return "\n".join(lines)
        
    def __repr__(self):
        return "('%s')" % self.key
             
    def __hash__(self):
        return hash(self.key)

    def __eq__(self, other):
        return hash(self) == hash(other)


class NetworkXKeyedGraph(AbstractKeyedGraph):
    
    def __init__(self):
        self.__nx_graph = DiGraph()
        self.__nodes = {}
        
    def add_node(self, key, **kw):
        if self.__nodes.has_key(key):
            node = self.__nodes[key]
        else:
            node = NetworkXNode(key, self.__nx_graph)
            self.__nodes[key] = node
        self.__nx_graph.add_node(node, **kw)
        return node

    def find_node_by_key(self, key):
        return self.__nodes.get(key, None)

    def iterator(self):
        class Iterator(AbstractGraphIterator):
            def __init__(self, nx_graph):
                self.__iterator = nx_graph.nodes_iter()
                
            def next(self):
                return self.__iterator.next()
                
        return Iterator(self.__nx_graph)
                
        
class NetworkXNode(AbstractKeyedGraphNode):
    
    def __init__(self, key, nx_graph, **kw):
        self.key = key
        self.__nx_graph = nx_graph
        self.__properties = kw

    def add_neighbor(self, node):
        self.__nx_graph.add_edge(self, node)

    def set(self, **kw):
        pass

    def iterator(self):
        for n in self.__nx_graph.successors(self):
            yield n
            for n2 in n.iterator():
                yield n2
        raise StopIteration()

    def randomized_iterator(self):
        successors = self.__nx_graph.successors(self)
        for n in random.sample(successors, len(successors)):
            yield n
            for n2 in n.randomized_iterator():
                yield n2
        raise StopIteration()
        
    def __repr__(self):
        return "%s (%s)" % (self.key, id(self))

    def __hash__(self):
        return hash(self.key)


class AbstractGraphIterator:

    def __iter__(self):
        return self
        
    def next(self):
        _not_implemented()

    def previous(self):
        _not_implemented()        


def add_words_to_graph(graph, phrase):
    # logging.debug("phrase:'%s'" % phrase)
    words = phrase.split()
    # logging.debug("words:%s" % words)
    # adds first word of phrase as root
    head = words.pop(0)
    prev_node = GraphNode(head)
    graph.add_node(prev_node)
    # logging.debug("added root %s" % prev_node)

    for w in words:
        word_node = graph.find_by_key(w)
        if not word_node:
            word_node = GraphNode(w)
        prev_node.add_neighbor(word_node)
        # logging.debug("%s -> %s" % (prev_node, word_node))
        prev_node = word_node

    # adds "end" child to last word of phrase
    prev_node.set("end", True)


def add_words_to_nx_graph(graph, phrase):
    # logging.debug("phrase:'%s'" % phrase)
    words = phrase.split()
    
    # gets "start" symbol
    start_node = graph.find_node_by_key(Symbols.START)
    if not start_node:
        start_node = graph.add_node(Symbols.START)
    
    # adds first word of phrase as root
    head = words.pop(0)
    prev_node = graph.add_node(head)
    start_node.add_neighbor(prev_node)
    
    for w in words:
        node = graph.add_node(w)
        prev_node.add_neighbor(node)
        # graph.add_edge(prev_word, w)
        prev_node = node

    # adds "end" child to last word of phrase
    prev_node.set(end=True)

    end_node = graph.find_node_by_key(Symbols.END)
    if not end_node:
        end_node = graph.add_node(Symbols.END)
        
    prev_node.add_neighbor(end_node)


class GraphSpeaker:

    def __init__(self):
        self.__graph = Graph()

    def ingest(self, phrase):
        add_words_to_graph(self.__graph, phrase)

    def speak(self, min_length, max_length):
        return str(self.__graph)
        
    def compile(self):
        pass


class NxGraphSpeaker:
    
    def __init__(self):
        self.__graph = NetworkXKeyedGraph()

    def ingest(self, phrase):
        add_words_to_nx_graph(self.__graph, phrase)

    def speak(self, min_length, max_length):
        start_node = self.__graph.find_node_by_key(Symbols.START)
        if start_node:
            iterator = start_node.randomized_iterator()
        else:
            iterator = self.__graph.randomized_iterator()
        
        # initial cut will not allow duplicate words
        words = []
        for n in iterator:
            # logging.debug("words: %s" % words)
                                    
            # avoids dulplicate words (for now)
            if n.key in words: break
            
            length = calculate_length(words)
            
            # if word has been used as an end and I am past min lenth, break
            if (n.key is Symbols.END) and (length >= min_length):
                break
            
            # breaks if we have reached max length
            if length >= max_length:
                raise TextException("could not achieve valid ending: %s" % self.__join(words))

            words.append(n.key)
            
        return self.__join(words)
        
    def compile(self):
        pass

    def __join(self, words):
        return " ".join(words)