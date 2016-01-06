"""
PyQuiz Utilities
simple, configurable quiz application

@author: Alvin Wan
@site: alvinwan.com
"""

from random import random, getrandbits
from markdown import markdown
import os

def quizzable(obj):
    """Return if obj is quizzable."""
    attrs = ('__question__', '__options__', '__check__', '__score__',
        '__passing__', '__total__')
    return [hasattr(obj, attr) for attr in attrs]

def check(obj, response, *args):
    """
    Check a quizzable object.

    :param obj: quizzable object
    :param answers: single response or list of responses to quiz
    :return: JSON object

    >>> qs = Question('Why?', 'Why not?', total=1)
    >>> result = check(qs, 'Why not?')
    >>> result['total'], result['score'], result['passing']
    (1, 1, True)
    >>> qz = Quiz(qs*2)
    >>> result = check(qz, ['Idk', 'Why not?'])
    >>> result['total'], result['score'], result['passing']
    (2, 1, False)
    """
    if not quizzable(obj):
        raise TypeError(repr(O), 'is not quizzable.')
    return obj.__check__(response, *args)

def score(obj, *args):
    """
    Returns score for checked quizzable.

    :param obj: quizzable object
    :return: float
    """
    if not quizzable(obj):
        raise TypeError(repr(O), 'is not quizzable.')
    return obj.__score__()

def passing(obj, *args):
    """
    Returns if checked quizzable has been passed.

    :param obj: quizzable object
    :return: boolean
    """
    if not quizzable(obj):
        raise TypeError(repr(O), 'is not quizzable.')
    return obj.__passing__()

def total(obj, *args):
    """
    Returns total for checked quizzable.

    :param obj: quizzable object
    :return: float
    """
    if not quizzable(obj):
        raise TypeError(repr(O), 'is not quizzable.')
    return obj.__total__()


class Quizzable:
    """base quizzable object"""

    def __check__(self):
        """returns JSON for checked quiz"""
        raise NotImplementedError()

    def __score__(self):
        """returns float for quizzable score"""
        raise NotImplementedError()

    def __total__(self):
        """returns float for quizzable total"""
        raise NotImplementedError()

    def __passing__(self):
        """returns whether quizzable has been passed"""
        raise NotImplementedError()


class Quiz(Quizzable):
    """base quiz class"""

    def __init__(self, questions=(), threshold=90, name=None,
        code_filter=lambda code: True):
        """
        Default constructor

        :param tuple questions: tuple of Questions
        """

        self.code_filter = code_filter
        self.vocab = Vocabulary(self.terms())
        self.qs = questions or self.questions()
        self.name = name or self.__class__.__name__
        self.threshold = threshold

    def copy(self):
        """returns new copy of quiz"""
        return Quiz(self.qz, self.threshold, self.name, self.code_filter)

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
        return []

    def questions(self):
        """Returns all questions for a quiz"""
        if self.qs:
            return self.qs
        raise NotImplementedError()

    def __check__(self, responses):
        """Checks answers and returns JSON results"""
        if isinstance(responses, str):
            responses = [responses]
        for q, response in zip(self.qs, responses):
            check(q, response)
        return {
            'score': score(self),
            'total': total(self),
            'passing': passing(self)
        }

    def __score__(self):
        """Compute score for quiz"""
        return sum(map(score, self.qs))

    def __total__(self):
        """Compute total for quiz"""
        return sum(map(total, self.qs))

    def __passing__(self):
        """Returns if quiz passed"""
        return score(self)/total(self)*100 >= self.threshold

    def to_json(self):
        """converts quiz to JSON"""
        raise NotImplementedError()

    def to_html(self):
        """converts quiz to HTML"""
        raise NotImplementedError()

    def generate_code(self):
        """Generates hash code that matches the given code_filter"""
        code = None
        while not code:
            _code = hash(getrandbits(128))
            if self.filter_code(_code):
                code = _code
        return code


class Question(Quizzable):
    """base Question class"""

    def __init__(self, question, answer, total=1, threshold=100, vocab=None,
        settings=None, score=lambda answer, response: int(answer == response)):

        self.question = question
        self.answer = answer
        self.score = score
        self.__score = None
        self.__total = total
        self.__settings = settings or {}
        self.vocab = vocab
        self.threshold = threshold

    def copy(self):
        return Question(self.question, self.answer, self.__total,
            self.threshold, self.vocab, self.__settings, self.score)

    def __check__(self, response):
        """Checks answer and returns JSON of result."""
        self.__score = self.score(self.answer, response)
        return {
            'score': score(self),
            'total': total(self),
            'passing': passing(self)
        }

    def __score__(self):
        if self.__score is None:
            raise UserWarning('Quizzable has not yet been checked.')
        return self.__score

    def __total__(self):
        return self.__total

    def __passing__(self):
        """Returns if question passed"""
        return score(self)/total(self)*100 >= self.threshold

    def __mul__(self, n):
        """Generate more questions of the same type and setting"""
        if not self.vocab:
            return [self.copy() for _ in range(n)]
        return [self.fromVocab(self.vocab, **self.__settings) for _ in range(n)]

    def to_json(self, suffix=''):
        """Converts question object to JSON"""
        raise NotImplementedError()

    def to_html(self):
        """converts question to HTML"""
        raise NotImplementedError()

    def __str__(self):
        """converts question to HTML"""
        return self.to_html()

class MultipleChoice(Question):
    """multiple choice question"""

    def __init__(self, question, options,
        score=lambda options, response: options[0] == response, **kwargs):
        super(MultipleChoice, self).__init__(question, options, score=score, **kwargs)

    @staticmethod
    def fromVocab(vocab, term=None, term_filter=lambda term: True, choices=5):
        """Generate multiple choice.

        :param Term term: term to test
        :param function term_filter: filter to determine what terms are used
        :return: multiple choice Question
        """
        args, used_terms = [], []
        terms = list(filter(term_filter, self.terms))
        random_term = lambda: terms[round(random() * (len(terms) - 1))]
        term_side = bool(int(random()))
        if not term:
            term = random_term()
            used_terms.append(term)
            args.append(tuple(term) if term_side else term[::-1])
        for i in range(min(choices, len(terms))):
            _term = random_term()
            while _term in used_terms:
                _term = random_term()
            used_terms.append(_term)
            args.append(_term[0 if term_side else 1])
        return MultipleChoice(*args, vocab=vocab, settings={
            'term': term,
            'term_filter': term_filter,
            'choices': choices
        })


class Vocabulary:
    """Collection of terms"""

    def __init__(self, terms):
        assert all(isinstance(t, Term) for t in terms), 'Non-Term instance found in list of terms.'
        self.terms = terms

    def __len__(self):
        return len(self.terms)

    def multipleChoice(self, **settings):
        """Generate multiple choice.

        :param dict settings: keyword argumnet settings for q generation
        """
        return MultipleChoice.fromVocab(self, **settings)

    def __repr__(self):
        return '<Vocabulary length=%d>' % len(self)

    def __str__(self):
        return '\n'.join(map(str, self.terms))

class Term:
    """Representation of a vocabulary term"""

    def __init__(self, term, definition):
        self.term = term
        self.definition = definition

    def __tuple__(self):
        return (self.term, self.definition)

    def __getitem__(self, i):
        return (self.term, self.definition)[i]

    def __repr__(self):
        return '<Term term="%s" definition="%s">' % tuple(self)

    def __str__(self):
        return '%s: %s' % tuple(self)

def files_by_tag(tag):
    """Extracts files by tag from the configuration file.

    :param str tag: tag
    :return: list of filenames
    """
    prefix = os.path.dirname(os.path.realpath(__file__))
    filename = os.path.join(prefix, 'pyquiz.cfg')
    files, _tag = [], None
    for line in open(filename, 'r').read().splitlines():
        line = line.strip()
        if line.startswith(tag+':'):
            _tag = line[:-1]
        elif not line:
            _tag = None
        elif _tag:
            files.append(line)
        else:
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
