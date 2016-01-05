"""
PyQuiz Utilities
simple, configurable quiz application

@author: Alvin Wan
@site: alvinwan.com
"""

from random import random, getrandbits
from markdown import markdown

def quizzable(obj):
    """Return if obj is quizzable."""
    return hasattr(obj, '__quiz__') and hasattr(obj, '__check__')

def check(obj, response, *args):
    """Check a quizzable object.

    :param obj: quizzable object
    :param answers: single response or list of responses to quiz
    :return: markdown string
    """
    if not quizzable(obj):
        raise TypeError(repr(O), 'is not quizzable.')
    return obj.__check__(quiz, response, *args)

def quiz(obj, *args):
    """
    Returns markdown for a quizzable.

    :param obj: quizzable object
    :return: markdown string
    """
    if not quizzable(obj):
        raise TypeError(repr(O), 'is not quizzable.')
    return obj.__quiz__(*args)


class Quizzable:
    """base quizzable object"""

    def __quiz__(self):
        """returns markdown of quiz"""
        raise NotImplementedError()

    def __check__(self):
        """returns markdown of results"""
        raise NotImplementedError()


class Quiz(Quizzable):
    """base quiz class"""

    def __init__(self, questions=(), threshold=90,
        code_filter=lambda code: True, name=None):
        """Default constructor

        :param tuple questions: tuple of Questions"""
        self.qs = questions
        self.threshold = threshold
        self.code_filter = code_filter

        self.vocabulary = Vocabulary(self.terms())
        self.qs = self.questions()

        self.name = name or self.__class__.__name__

    @staticmethod
    def from_markdown(path):
        """Loads information from a markdown file.

        :param str path: path to .md file
        :return: new Quiz object
        """
        questions, question = [], {}
        file_contents = open(path, 'r').read()
        for i, line in enumerate(filter(bool, file_contents.splitlines())):
            if line.startswith('Q:'):
                if question:
                    questions.append(question)
                    question = {}
                question['q'] = line[2:]
            elif line[0] in ('-', '*'):
                question['a'].setdefault([]).append(line[1:].strip())
            else:
                raise SyntaxError('Line %d in %s not a supported format.' % \
                    (i, path))
        return Quiz([Question(d['q'], *d['a']) for d in questions])

    def terms(self):
        """Returns all vocabulary terms for a quiz"""
        raise NotImplementedError()

    def questions(self):
        """Returns all questions for a quiz"""
        if self.qs:
            return self.qs
        raise NotImplementedError()

    def __check__(self, responses):
        """Checks answers and returns markdown of results"""
        if isinstance(responses, str):
            responses = [responses]
        html = '\n'.join([check(q, response)
            for q, response in zip(self.qs, responses)])
        return self.header() + html

    def __quiz__(self):
        """Returns markdown of quiz"""
        return '\n'.join([quiz(q, str(i)) for i, q in enumerate(self.qs)])

    def compute_score(self):
        """Compute score for quiz"""
        return sum(q.score for q in self.qs) // sum(q.total for q in self.qs)

    def header(self):
        """Message prepended to quiz results."""
        score = self.compute_score()
        passed = score > self.threshold
        message = 'You Passed' if passed else 'Try again?'
        header = '# %s with %d%\n' % (message, score)
        if passed:
            header += 'Code: %s' % str(self.generate_code())
        return header

    def generate_code(self):
        """Generates hash code that matches the given code_filter"""
        code = None
        while not code:
            _code = hash(getrandbits(128))
            if self.filter_code(_code):
                code = _code
        return code

class Question(Quizzable):

    def __init__(self, question, *options,
        check=lambda options, response: options[0] == response,
        score=None, total=1, vocabulary=None):
        self.question = question
        self.options = map(str, options)
        self.check = check
        self.score = score
        self.total = total
        self.vocabulary = vocabulary

    def __check__(self, response):
        """Checks answer and returns markdown of result."""
        is_correct = self.check(self.options, response)
        self.score = bool(is_correct) * total
        markdown = ['##%s\n' % self.question]
        for o in self.options:
            if o == response:
                form = '- Correct: %s' if is_correct else '- You chose: %s'
                markdown.append(form % o)
            elif self.check(self.options, o):
                markdown.append('- Answer: %s' % o)
            else:
                markdown.append('- %s' % o)
        return '\n'.join(markdown)

    def __quiz__(self, suffix=''):
        """Returns markdown of quiz."""
        return '\n'.join(['##%s\n' % self.question] + \
            ['- <input type="radio" name="q%s" value="%s" />' % (suffix, o) for o in self.options])


class Vocabulary:
    """Collection of terms"""

    def __init__(self, terms):
        self.terms = terms

    def multiple_choice(self, term=None, term_filter=lambda term: True,
        num_options=5):
        """Generate multiple choice.

        :param Term term: term to test
        :param function term_filter: filter to determine what terms are used
        :return: multiple choice Question
        """
        random_term = lambda: self.terms[int(random() * (len(terms) - 1))]
        args, terms = [], terms
        term_side = bool(int(random()))
        if not term:
            term = random_term()
            terms.append(term)
            args.append(tuple(term) if term_side else term[::-1]))
        for i in range(min(num_options, len(self.terms))):
            _term = random_term()
            while _term in terms:
                _term = random_term()
            terms.append(_term)
            args.append(_term[0 if term_side else 1])
        return Question(*args, vocabulary=self)


class Term:
    """Representation of a vocabulary term"""

    def __init__(self, term, definition):
        self.term = term
        self.definition = definition

    def __tuple__(self):
        return (self.term, self.definition)

    def __getitem__(self, i):
        if i in (0, 1):
            return tuple(self)[i]
        else:
            raise IndexError('Term can only be indexed at 0 and 1.')

def files_by_tag(tag):
    """Extracts files by tag from the configuration file.

    :param str tag: tag
    :return: list of filenames
    """
    files, _tag = [], None
    for line in open('pyquiz.cfg', 'r').read().splitlines():
        line = line.strip()
        if line.startswith('live:'):
            _tag = line[:-1]
        if not line:
            _tag = None
        if _tag:
            files.append(line)
        else _tag:
            continue
    return files


def md2quiz(md):
    """Converts markdown to an HTML quiz.

    :param str markdown: markdown
    :return: HTML
    """
    return '<form method="POST">%s<input type="submit" value="submit quiz"></form>' % markdown(md, output_format='html5')

def rq2responses(request):
    """Converts a request to a list of responses.

    :param request: Flask Request object
    :return: list of response strings
    """
    name_format, i, responses = 'q%d', 0, [] # standardize
    while True:
        name = name_format % i
        if name in request.form:
            responses.append(request.form[name])
        i += 1
    return responses
