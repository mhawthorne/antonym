import logging


class Tree:

    def __init__(self):
        self.__index = {}
        self.__roots = set([])

    def is_empty(self):
        return len(self.__roots) == 0

    def add_root(self, node):
        self.__roots.add(node)

    def iterate_root_keys(self):
        for r in self.__roots:
            yield r.key
    
    def iterate_roots(self):
        for r in self.__roots:
            yield r
    
    def find(self, key):
        result = None
        for r in self.__roots:
            result = r.find(key)
            if result:
                break
        return result
        
    def descendent_count(self):
        return sum([r.descendent_count() + 1 for r in self.__roots])
    
    def describe_full(self):
        lines = []
        for r in self.__roots:
            lines.append("\n%s" % r.describe_full())
        return "\n".join(lines)

    def __repr__(self):
        # TODO: make this less expensive after debugging
        return self.describe_full()
        
        # return "%s{root_count:%d; descendent_count:%d; roots:%s}" % (self.__class__.__name__,
        #     len(self.roots),
        #     self.descendent_count(),
        #     sorted([n.key for n in self.roots]))


class TreeNode:
    """
    attributes:
        key
        value
        children
    """
    
    def __init__(self, key, value=None):
        self.key = key
        self.value = value
        self.__properties = {}
        self.__children = {}

    def add(self, node):
        self.__children[node.key] = node

    def has_children(self):
        return len(self.__children) != 0
        
    def iterate_children(self):
        for v in self.__children.values():
            yield v
    
    def has_child(self, key):
        return self.__children.has_key(key)
        
    def find_descendent(self, key, walked_keys=None):
        result = self.__children.get(key, None)
        if not result:
            for child_key, node in self.__children.iteritems():
                if walked_keys:
                    if child_key in walked_keys:
                        continue
                else:
                    walked_keys = set([])
                walked_keys.add(child_key)
                result = node.find_descendent(key, walked_keys)
                if result:
                    break
        return result
        
    def set(self, key, value):
        self.__properties[key] = value
        
    def get(self, key, default):
        return self.__properties.get(key, default)
    
    def has(self, key):
        return self.__properties.has_key(key)
        
    def child_count(self):
        return len(self.__children)
   
    def descendent_count(self):
        return sum([c.descendent_count() + 1 for c in self.__iterate_children()])
 
    def __iterate_children(self, walked_keys=None):
        for key, node in self.__children.iteritems():
            if walked_keys:
                if key in walked_keys:
                    # node has been walked, skip
                    continue
            else:
                walked_keys = set([])
                
            yield node
            walked_keys.add(key)
            
            # recursively walks node's children
            # node.__iterate_children(walked_keys)
        
    def describe_short(self):
        return "%s('%s', id:%s, child_count:%d, descendent_count:%d)" % (self.__class__.__name__,
            self.key,
            id(self),
            self.child_count(),
            self.descendent_count())

    def describe_full(self, indent=0, parents=None):
        level = "[%d]" % indent
        lines = ["%s %s%s" % (level, " " * 2 * indent, self)]
        
        if not parents:
            parents = set([])
            
        # adds self to list of parents to avoid infinite recursion
        parents.add(self.key)
        
        for c in self.__children.values():
            if c.key in parents:
                # child is also a parent, don't recurse into it
                lines.append("%s %s%s ^" % (level, " " * 2 * (indent + 1), c.key))
                continue
            lines.append(c.describe_full(indent + 1, parents))
        return "\n".join(lines)

    def __repr__(self):
        return "('%s')" % self.key
        # return "('%s', id:%s)" % (self.key, id(self))
             
    def __hash__(self):
        return hash(self.key)

    def __eq__(self, other):
        return hash(self) == hash(other)


class TreeIterator:
    """ abstract class """
    
    def next(self):
        raise UnsupportedOperationException()
        
    def previous(self):
        raise UnsupportedOperationException()


class SimpleTreeIterator(TreeIterator):

    def __init__(self, tree):
        # logging.debug("__init__ tree:%s" % tree.describe_full())
        self.__tree = tree
        self.__seen_keys = []
        self.__current = None

    # TODO: avoid infinite loops
    # avoiding a node I've already seen is too harsh
    
    def has_next(self):
        if not self.__current:
            result = not self.__tree.is_empty()
            # logging.debug("has_next tree.is_empty(): %s" % self.__tree.is_empty())
        else:
            result = self.__current.has_children()
        # logging.debug("has_next %s" % result)
        return result
        
    def next(self):
        if not self.__current:
            next = self.__select(self.__tree.iterate_roots())
        else:
            next = self.__select(self.__current.iterate_children())
        
        self.__current = next
        self.__seen_keys.append(next.key)
        return next

    def previous(self):
        raise NotImplementedException()
    
    def __select(self, iterator):
        selected = [i for i in iterator][0]
        # logging.debug("__select selected:%s" % selected)
        return selected


def add_words_to_tree(tree, phrase):
    # logging.debug("phrase:'%s'" % phrase)
    words = phrase.split()
    # logging.debug("words:%s" % words)
    # adds first word of phrase as root
    head = words.pop(0)
    prev_node = TreeNode(head)
    tree.add_root(prev_node)
    # logging.debug("added root %s" % prev_node)

    for w in words:
        word_node = tree.find(w)
        if not word_node:
            word_node = TreeNode(w)
        prev_node.add(word_node)
        # logging.debug("%s -> %s" % (prev_node, word_node))
        prev_node = word_node

    # adds "end" child to last word of phrase
    prev_node.set("end", True)
    
    
class TreeSpeaker:

    def __init__(self):
        self.__tree = Tree()

    def ingest(self, phrase):
        add_words_to_tree(self.__tree, phrase)
        
    def speak(self, min_length, max_length):
        return str(self.__tree)
        
    def compile(self):
        pass