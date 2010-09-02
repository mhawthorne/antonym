import random


# TODO: optimize
def select_weighted_with_replacement(items):
    items = [i for i in generate_weighted_with_replacement(items, 1)]
    return items.pop()


def generate_weighted_with_replacement(items, count):
    """
    params:
        items - list of (value, weight) tuples
        count - number of items to grab
        
    returns:
        list
    """
    total = float(sum(w for v, w in items))
    i = 0
    v, w = items[0]
    while count:
        x = total * (1 - random.random() ** (1.0 / count))
        total -= x
        while x > w:
            x -= w
            i += 1
            v, w = items[i]
        w -= x
        yield v
        count -= 1
