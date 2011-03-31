import logging
import random

from networkx import shortest_path, DiGraph

from antonym.core import IllegalStateException, NotImplementedException
from antonym.text import TextException
from antonym.text.speakers.core import calculate_length, tokenize_sentences, SelectingSpeaker, Symbols


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

    def __iter__(self):
        return self.iterator()

    def randomized_iterator(self):
        _not_implemented()
      
    def size(self):
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
    
    def source(self):
        return self.__nx_graph

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
                
    def size(self):
        return len(self.__nx_graph)

    def __repr__(self):
        return str(dict(id=hash(self), size=self.size()))


class NetworkXNode(AbstractKeyedGraphNode):
    
    def __init__(self, key, nx_graph, **kw):
        self.key = key
        self.__nx_graph = nx_graph
        self.__properties = kw

    def add_neighbor(self, node):
        self.__nx_graph.add_edge(self, node)

    def neighbors(self):
        return self.__nx_graph.successors(self)

    def set(self, **kw):
        pass

    def iterator(self):
        for n in self.__nx_graph.successors(self):
            yield n
            for n2 in n.iterator():
                yield n2
        raise StopIteration()

    def _randomized_iterator(self):
        return NxGraphIterator(self, self.__nx_graph)
    
    def randomized_iterator(self):
        successors = self.__nx_graph.successors(self)
        
        # indicates that this node can end a phrase
        n_can_end = False
        successor_count = len(successors)
        n_can_end = Symbols.END in [s.key for s in successors]
        # logging.debug("n_can_end:%s, successors:%s" % (n_can_end, successors))
        
        for n in random.sample(successors, successor_count):
            if n.key is Symbols.END:
                # won't return "end" since, if I'm not yet at the end of a phrase, I reach an undesired stopping point
                continue
            yield n, n_can_end
            for n2, n2_can_end in n.randomized_iterator():
                yield n2, n2_can_end
        raise StopIteration()
     
    def has(self, key):
        return self.__nx_graph[self].has_key(key)

    def __repr__(self):
        return "%s (%s)" % (self.key, id(self))

    def __hash__(self):
        return hash(self.key)


class AbstractGraphIterator:

    def __iter__(self):
        return self

    def has_next(self):
        _not_implemented()

    def next(self):
        _not_implemented()

    def previous(self):
        _not_implemented()


class NxGraphIterator(AbstractGraphIterator):

    def __init__(self, node, graph):
        self.__graph = graph
        self.__current = node
        
        # initial followers are successors
        self.__followers = self.__graph.successors(self.__current)
        
    def has_next(self):
        return bool(self.__followers)
        
    def next(self):
        self.__move(self.__graph.successors(self.__current))

    def previous(self):
        self.__move(self.__graph.predecessors(self.__current))

    def __move(self, followers):
        # indicates that this node can end a phrase
        can_end = (Symbols.END in [s.key for s in followers] )
        
        # logging.debug("can_end:%s, followers:%s" % (can_end, followers))
        self.__current = random.choice(followers)
        self.__followers = followers
        return self.__current, can_end


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
    # TODO: decide if 50 is the right choice here
    for sentence in tokenize_sentences(phrase, 50, transform_call=lambda s: s.lower()):
        words = sentence.split()
    
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
        # prev_node.set(end=True)
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


# TODO: share code between nx speakers

def _join(words):
    return " ".join(words)


class NxGraphShortestPathSpeaker:
    
    def __init__(self):
        self.__graph = NetworkXKeyedGraph()

    def ingest(self, phrase):
        add_words_to_nx_graph(self.__graph, phrase)

    def compile(self):
        pass
    
    def speak(self, min_length, max_length):
        start_node = self.__graph.find_node_by_key(Symbols.START)
        end_node = self.__graph.find_node_by_key(Symbols.END)
        
        # find random first node
        graph_source = self.__graph.source()
        first_word_node = random.choice(graph_source.successors(start_node))
        nodes = shortest_path(graph_source, source=first_word_node, target=end_node)
        return " ".join(n.key for n in nodes[0:len(nodes)-1])


class Phrase:
    
    def __init__(self):
        self.__items = []
        
    def add(self, word, can_end=False):
        self.__items.append((word, can_end))
    
    def pop(self):
        self.__items.pop()
        
    def join(self):
        return " ".join([w for w in self.__word_iterator()])
    
    def char_count(self):
        return calculate_length([w for w in self.__word_iterator()])
        
    def word_count(self):
        return len(self.__items)
        
    def __word_iterator(self):
        for i in self.item_iterator():
            yield i[0] 

    def items(self):
        return self.__items

    def item_iterator(self):
        for i in self.__items:
            yield i


class NxGraphSpeaker:

    def __init__(self):
        self.__graph = NetworkXKeyedGraph()

    def ingest(self, phrase):
        add_words_to_nx_graph(self.__graph, phrase)

    def compile(self):
        pass
    
    def describe(self):
        # return "\n".join([str(n) for n in sorted(self.__graph, key=lambda n: n.key)])
        return "\n".join([str(self.__describe(n)) for n in sorted(self.__graph, key=lambda i: i.key)])
    
    def __describe(self, node):
        return node, [n.key for n in node.neighbors()]
        
    def speak(self, min_length, max_length):
        start_node = self.__graph.find_node_by_key(Symbols.START)
        if not start_node:
            raise IllegalStateException("Node '%s' not found" % Symbols.START)
            
        phrase = Phrase()
        status = 1
        
        # multiple back-and-forth attempts
        for i in xrange(2):
            attempt = i + 1
            logging.debug("phrase building attempt %d" % attempt)
            status = self.__phrase_forward(phrase, start_node, min_length, max_length) and \
                self.__phrase_backtrack(phrase, min_length, max_length)
                
            # breaks upon success
            if not status: break
            
        if status:
            raise TextException("could not build phrase in %d attempt(s)" % attempt)
        else:
            joined = phrase.join()
            logging.debug("success! phrase: '%s'" % joined)
            return joined
    
    def __phrase_forward(self, phrase, start_node, min_length, max_length):
        status = 0
        iterator = start_node.randomized_iterator()
        for n, can_end in iterator:
            if n.key is Symbols.END:
                # skips end
                continue

            logging.debug("__phrase_forward word:%s can_end:%s" % (n, can_end))

            length = phrase.char_count()

            # breaks if we have reached max length
            if length >= max_length:
                status = 1
                # raise TextException("could not achieve valid ending: %s" % self.__join(words))
                break

            if can_end and (length >= min_length):
                logging.debug("found end; length(%d) > min_length(%d); breaking" % (length, min_length))
                break

            phrase.add(n.key, can_end)
            
        return status
        
    def __phrase_backtrack(self, phrase, min_length, max_length):
        status = 1
        for word, can_end in reversed(phrase.items()):
            logging.debug("__phrase_backtrack word:%s can_end:%s" % (word, can_end))
            if can_end:
                # if I can end and I'm greater than the min, length, I won
                # if I'm less than the min_length, I lost
                status = (phrase.char_count <= min_length)
                break
            phrase.pop()
        return status
        
    def _speak(self, min_length, max_length):
        start_node = self.__graph.find_node_by_key(Symbols.START)
        if not start_node:
            raise IllegalStateException("Node '%s' not found" % Symbols.START)
            
        iterator = start_node.randomized_iterator()
    
        # initial cut will not allow duplicate words
        words = []
        for n, can_end in iterator:
            logging.debug("word: %s" % n)
        
            length = calculate_length(words)
        
            # if word has been used as an end and I am past min lenth, break
            # if (n.key is Symbols.END) and (length >= min_length):
            #     logging.debug("found end after min_length; breaking")
            #     break

            if can_end and (length >= min_length):
                logging.debug("found end after min_length; breaking")
                break
        
            # breaks if we have reached max length
            if length >= max_length:
                raise TextException("could not achieve valid ending: %s" % self.__join(words))

            # TODO: backtrack and try to find ending

            words.append(n.key)
        
        return self.__join(words)
        
    def __join(self, words):
        return " ".join(words)

    def __repr__(self):
        return "%s{graph:%s}" % (self.__class__.__name__, repr(self.__graph))


class NxGraphSelectingSpeaker(SelectingSpeaker):
    
    def __init__(self):
        self.__graph = NetworkXKeyedGraph()
        
    def ingest(self, phrase):
        add_words_to_nx_graph(self.__graph, phrase)
    
    # def select(self, selected):
    #     pass
    
    def select(self, selected, min_length, max_length):
        if not selected:
            # nothing selected, so choosing start node
            node = self.__graph.find_node_by_key(Symbols.START)
        else:
            # words have been selected, finding node for last selected word
            node = self.__graph.find_node_by_key(selected[len(selected)-1])
            
        iterator = node.randomized_iterator()
        next_node = iterator.next()
        next_word = next_node.key
        
        # calculates size of current mixture
        selected.append(next_word)
        length = calculate_length(selected)
        
        if length >= max_length:
            if next_word is Symbols.END:
                # returning None if I have found an end node
                result = None
            else:
                # fails since I have not found a valid end node
                raise TextException("could not achieve valid ending: %s" % self.__join(selected))
        elif length >= min_length and next_node.has(Symbols.END):
            # I am past the min length and I can end.  so let's end.
            pass
        else: 
            result = (next_word,)
        return result
    
    def __join(self, words):
        return " ".join(words)
