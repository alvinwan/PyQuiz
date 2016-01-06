"""
PyQuiz Utilities
simple, configurable quiz application

@author: Alvin Wan
@site: alvinwan.com
"""

from json import loads, dumps
from random import random, getrandbits, shuffle
from importlib import import_module
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

    title = 'Quiz'
    initial_message = 'Click check at the end to check your work. You have \
    unlimited tries. Once you have passed, you will be given a custom code to \
    prove completion.'
    failed_message = 'You received {percent}%, but passing is {threshold}%. <a \
    href="#" onclick="location.reload()">Try again?</a>'
    passed_message = 'Congratulations! You have passed with {percent}%. Here is\
    your code of completion: {code}'
    code_filter = lambda self, code: code % 35 == 2
    shuffle_on_view = True

    def __init__(self, source, questions=(), threshold=90, name=None):
        """
        Default constructor

        :param tuple questions: tuple of Questions
        """

        self.source = source
        self.vocab = Vocabulary(self.terms())
        self.qs = self.__questions(questions)
        self.name = name or self.__class__.__name__
        self.threshold = threshold
        self.__checked = False

    def copy(self):
        """returns new copy of quiz"""
        return Quiz(self.qs, self.threshold, self.name, self.code_filter)

    @property
    def message(self):
        if not self.__checked:
            return self.initial_message

        percent = (score(self) * 100) // total(self)
        return self.failed_message.format(percent=percent,
            threshold=self.threshold) if not passing(self) else self.passed_message.format(percent=percent, code=self.generate_code())

    @staticmethod
    def from_json(json):
        """
        Create quiz object from json

        :param json: JSON
        :return: Quiz
        """
        data = loads(json)
        return Quiz.from_dict({
            'questions':[globals()[q['class']].from_dict(q)
                for q in data['questions']],
            'source': data['source']
        })

    @staticmethod
    def from_dict(data):
        """
        Create quiz object from dictionary

        :param dict data: data
        :return: Quiz
        """
        return Quiz(**data)

    @staticmethod
    def from_markdown(path):
        """
        Loads information from a markdown file.

        :param str path: path to .md file
        :return: new Quiz object
        """
        questions, question = [], {}
        with open(path, 'r').read() as f:
            for i, line in enumerate(filter(bool, f)):
                if line.startswith('Q:'):
                    if question:
                        questions.append(question)
                        question = {}
                    question['q'] = line[2:]
                elif line[0] in ('-', '*'):
                    question['choices'].setdefault([]).append(line[1:].strip())
                else:
                    # TODO: change to logger warning
                    raise SyntaxError('Line %d in %s not a supported format.' % \
                        (i, path))
        return Quiz(path, [Question(d['q'], d['choices'][0], d['choices'])
            for d in questions])

    def shuffle(self):
        """shuffle questions and choices"""
        for q in self.qs:
            q.shuffle()
        shuffle(self.qs)
        self.id_questions()

    def terms(self):
        """Returns all vocabulary terms for a quiz"""
        return []

    def __questions(self, questions=(), regenerate=False):
        """Returns all question if not already accessed."""
        if questions:
            self.qs = questions
        elif not getattr(self, 'qs', None) or regenerate:
            self.qs = self.questions()
        self.id_questions()
        return self.qs

    def id_questions(self):
        """ids all questions"""
        for i, q in enumerate(self.qs):
            q._id = Question.ID_FORMAT % i

    def questions(self):
        """Returns all questions for a quiz"""
        raise NotImplementedError()

    def __check__(self, responses):
        """Checks answers and returns JSON results"""
        self.__checked = True
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
        return float(sum(map(score, self.__questions())))

    def __total__(self):
        """Compute total for quiz"""
        return float(sum(map(total, self.__questions())))

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
            if self.code_filter(_code):
                code = _code
        return code

    def to_dict(self):
        return {
            'source': self.source,
            'questions': [q.to_dict() for q in self.qs],
        }

    def to_json(self):
        """dumps quiz"""
        return dumps(self.to_dict())


class Question(Quizzable):
    """base Question class for a 'fill-in-the-blank'-style question"""

    ID_FORMAT = 'q%d'

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
        self.__fields = None

    @property
    def question(self):
        md = markdown(self.__question)
        if md.startswith('<p>'):
            md = md[3:-4]
        return md

    def copy(self):
        return Question(self.question, self.answer, self.__total,
            self.threshold, self.vocab, self.__settings, self.score)

    def shuffle(self):
        pass

    @staticmethod
    def from_json(json):
        """
        Create quiz object from json

        :param json: JSON
        :return: Quiz
        """
        return Question.from_dict(loads(json))

    @staticmethod
    def from_dict(data):
        """
        Create quiz object from dictionary

        :param dict data: data
        :return: Quiz
        """
        return Question(data['question'], data['answer'])

    def __check__(self, response):
        """Checks answer and returns JSON of result."""
        self.__score = self.score(self.answer, response)
        for field in self.fields():
            check(field, self.answer, response)
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
        if not self.__fields:
            self.__fields = [Field(self._id, 'text')]
        return self.__fields

    def to_dict(self):
        """dumps question"""
        return {
            'question': self.__question,
            'answer': self.answer,
            'class': 'Question'
        }

    def to_json(self):
        return dumps(self.to_dict())


class MultipleChoice(Question):
    """multiple choice question"""

    ONE_SELECTION = 'one selection'
    MULTIPLE_SELECTIONS = 'multiple selections'

    def __init__(self, question, answer, choices, category=ONE_SELECTION,
        total=1, threshold=100, vocab=None, settings=None,
        score=lambda answer, response: int(answer == response), **kwargs):
        super(MultipleChoice, self).__init__(question, choices, score=score, **kwargs)

        self.__question = question
        self.answer = answer
        self.score = score
        self.__score = None
        self.__total = total
        self.__settings = settings or {}
        self.vocab = vocab
        self.threshold = threshold

        self.__category = category
        self.choices = choices
        self.__fields = []

    def fields(self):
        if not self.__fields:
            _type = 'radio' if self.__category == self.ONE_SELECTION else 'checkbox'
            self.__fields = [Field(self._id, _type, label=v, value=v) for v in self.choices]
        return self.__fields

    def shuffle(self):
        shuffle(self.__fields)
        shuffle(self.choices)

    @staticmethod
    def from_json(json):
        """
        Create question object from json

        :param json: JSON
        :return: Quiz
        """
        return MultipleChoice.from_dict(loads(json))

    @staticmethod
    def from_dict(data):
        """
        Create question object from dictionary

        :param dict data: data
        :return: Quiz
        """
        return MultipleChoice(data['question'], data['answer'], data['choices'])

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
        question, answer = tuple(term) if term_side else term[::-1]
        choices.append(answer)
        for i in range(min(num_choices, len(terms))):
            _term = random_term()
            while _term in used_terms:
                _term = random_term()
            used_terms.append(_term)
            choices.append(_term[0 if not term_side else 1])
        return MultipleChoice(question, answer, choices, vocab=vocab, settings={
            'term_filter': term_filter,
            'num_choices': num_choices,
            'term_side': term_side
        })

    def to_dict(self):
        return {
            'question': self.__question,
            'answer': self.answer,
            'choices': self.choices,
            'class': 'MultipleChoice'
        }


class Field:

    def __init__(self, name, type_, label=None, **props):
        self.__name = name
        self.__type = type_
        self.__props = props
        self.__label = label
        self.__checked = False

    @property
    def label(self):
        md = markdown(self.__label)
        if md.startswith('<p>'):
            md = md[3:-4]
        return md

    def __check__(self, answer, response):
        self.__checked = True
        self.__response = response
        self.__answer = answer

    def display(self):
        if self.__type in ('radio', 'checkbox'):
            if self.__response == self.__label == self.__answer:
                message = 'Correct answer: '
            elif self.__response == self.__label != self.__answer:
                message = 'You chose: '
            elif self.__response != self.__label == self.__answer :
                message = 'Correct choice: '
            else:
                message = ''
            return '<p>%s%s</p>' % (message, self.__label)
        else:
            self.__props.update({
                'value': response,
                'readonly': 'readonly'
            })
            return self.input()

    def input(self):
        return '<p><input type="%s" name="%s" %s>%s</p>' % (
            self.__type, self.__name,
            ' '.join('%s="%s"' % t for t in self.__props.items()),
            self.label)

    def __str__(self):
        return self.display() if self.__checked else self.input()


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


def rq2quiz(request):
    """
    Extracts quiz from a request

    :param request: Flask Request object
    :return: Quiz object
    """
    q = Quiz.from_json(request.form['meta'])
    return path2quiz(q.source, q.qs)

def rq2responses(request):
    """
    Converts a request to a list of responses.

    :param request: Flask Request object
    :return: list of response strings
    """
    i, responses = 0, []
    for i in range(int(request.form['num_questions'])):
        name = Question.ID_FORMAT % i
        if request.form.get(name, None):
            responses.append(request.form[name])
        else:
            responses.append(None)
        i += 1
    return responses

def path2quiz(path, *args, **kwargs):
    if path.endswith('.md'):
        return Quiz.from_markdown(path)
    else:
        path_ = path.replace('.py', '')
        classname = path_.split('/')[-1]
        module = import_module(path_.replace('/', '.'))
        Quiz = getattr(module, classname)
        return Quiz(path, *args, **kwargs)
