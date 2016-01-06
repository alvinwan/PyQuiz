"""
PyQuiz Utilities
simple, configurable quiz application

@author: Alvin Wan
@site: alvinwan.com
"""

from flask import jsonify
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
        self.qs = self.__questions(questions)
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
        with open(path, 'r').read() as f:
            for i, line in enumerate(filter(bool, f.readlines())):
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

    def __questions(self, questions=(), regenerate=False):
        """Returns all question if not already accessed."""
        if not questions and getattr(self, 'qs', None) and not regenerate:
            questions = self.qs
        questions = self.questions()
        for i, q in enumerate(questions):
            q._id = 'q%d' % i
        return questions

    def questions(self):
        """Returns all questions for a quiz"""
        raise NotImplementedError()

    def __check__(self, responses):
        """Checks answers and returns JSON results"""
        if isinstance(responses, str):
            responses = [responses]
        for q, response in zip(self.__questions(), responses):
            check(q, response)
        return {
            'score': score(self),
            'total': total(self),
            'passing': passing(self)
        }

    def __score__(self):
        """Compute score for quiz"""
        return sum(map(score, self.__questions()))

    def __total__(self):
        """Compute total for quiz"""
        return sum(map(total, self.__questions()))

    def __passing__(self):
        """Returns if quiz passed"""
        return score(self)/total(self)*100 >= self.threshold

    def __iter__(self):
        return iter(self.__questions())

    def generate_code(self):
        """Generates hash code that matches the given code_filter"""
        code = None
        while not code:
            _code = hash(getrandbits(128))
            if self.filter_code(_code):
                code = _code
        return code


class Question(Quizzable):
    """base Question class for a 'fill-in-the-blank'-style question"""

    def __init__(self, question, answer, total=1, threshold=100, vocab=None,
        settings=None, score=lambda answer, response: int(answer == response)):

        self.__question = question
        self.answer = answer
        self.score = score
        self.__score = None
        self.__total = total
        self.__settings = settings or {}
        self.vocab = vocab
        self.threshold = threshold

    @property
    def question(self):
        md = markdown(self.__question)
        if md.startswith('<p>'):
            md = md[3:-4]
        return md

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

    def fields(self):
        """Returns iterable of fields for user input"""
        return [Field(self._id, 'text')]


class MultipleChoice(Question):
    """multiple choice question"""

    ONE_SELECTION = 'one selection'
    MULTIPLE_SELECTIONS = 'multiple selections'

    def __init__(self, question, choices, category=ONE_SELECTION,
        score=lambda choices, response: choices[0] == response, **kwargs):
        super(MultipleChoice, self).__init__(question, choices, score=score, **kwargs)
        self.__category = category
        self.choices = choices

    def fields(self):
        _type = 'radio' if self.__category == self.ONE_SELECTION else 'checkbox'
        return [Field(self._id, _type, label=v, value=v) for v in self.choices]

    @staticmethod
    def fromVocab(vocab, term=None, term_filter=lambda term: True,
        num_choices=5, term_side=None):
        """
        Generate multiple choice.

        :param Term term: term to test
        :param function term_filter: filter to determine what terms are used
        :return: multiple choice Question
        """
        choices, used_terms = [], []
        terms = list(filter(term_filter, vocab.terms))
        random_term = lambda: terms[round(random() * (len(terms) - 1))]
        if not term_side:
            term_side = bool(int(random()))
        if not term:
            term = random_term()
            used_terms.append(term)
        question, choice = tuple(term) if term_side else term[::-1]
        choices.append(choice)
        for i in range(min(num_choices, len(terms))):
            _term = random_term()
            while _term in used_terms:
                _term = random_term()
            used_terms.append(_term)
            choices.append(_term[0 if not term_side else 1])
        return MultipleChoice(question, choices, vocab=vocab, settings={
            'term_filter': term_filter,
            'num_choices': num_choices,
            'term_side': term_side
        })


class Field:

    def __init__(self, name, type_, label=None, **props):
        self.__name = name
        self.__type = type_
        self.__props = props
        self.__label = label

    @property
    def label(self):
        md = markdown(self.__label)
        if md.startswith('<p>'):
            md = md[3:-4]
        return md

    def __str__(self):
        return '<p><input type="%s" name="%s" %s>%s</p>' % (
            self.__type, self.__name,
            ' '.join('%s="%s"' % t for t in self.__props.items()),
            self.label)


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
