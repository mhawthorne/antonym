import unittest

from antonym import rrandom


class RrandomTest(unittest.TestCase):

    def test_generate_weighted_with_replacement(self):
        zero = 'zero'
        one = 'one'
        two = 'two'
        seven = 'seven'
        
        item_hash = {zero: 0,
            one: 1,
            two: 2, 
            seven: 7}
        
        items = [p for p in item_hash.iteritems()]
        weight_sum = sum(p[1] for p in item_hash.iteritems())
        count = 100
        
        # tests this multiple times
        for i in xrange(100):
            results = [i for i in rrandom.generate_weighted_with_replacement(items, count)]
        
            # counts cardinality of results
            item_counts = {}
            for r in results:
                item_counts[r] = item_counts.setdefault(r, 0) + 1
            
            print item_counts
            seven_selected = item_counts[seven]
            seven_expected = (float(item_hash[seven]) / weight_sum) * count
            variance = seven_expected * 0.3
            seven_min = seven_expected - variance
            seven_max = seven_expected + variance
            self.assert_(seven_min <= seven_selected and seven_selected <= seven_max,
                "unexpected cardinality for %s: %d !<= %d !<= %d" % (seven, seven_min, seven_selected, seven_max))


if __name__ == '__main__':
    unittest.main()