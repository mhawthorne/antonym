import re


class RegexRewriter:
    
    def __init__(self, replacements):
        """
        params:
            replacements - keys are regexes, values are strings to replace regex matches
        """
        self.__replacements = {}
        for pattern, replace in replacements.iteritems():
            self.__replacements[re.compile(pattern)] = replace
    
    def rewrite(self, text):
        """
        params:
            text - source text
        returns:
            rewritten text
        """
        result_text = text
        for regex, replace in self.__replacements.iteritems():
            result_text = regex.sub(replace, result_text)
        return result_text
        