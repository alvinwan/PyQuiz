# PyQuiz
Quiz application with configurable completion codes

Quizzes can be created in two ways:
- code an OOP representation of a quiz, using the Quiz class along with
  `Question` and/or vocabulary `Term` instances
- write a quiz using markdown syntax

Quizzes can be published:
- as static HTML files
- as an application, where questions and answers can be randomly ordered
- with randomly-generated or pattern-matching codes of completion

## Usage

Launch using `make run`. See below for configurations and getting started.

## OOP Quiz Creation

`Question` instances allow you to code questions as you normally would. `Term`
instances allow you to to specify a set of terms, then generate several
different types of test questions.

All quizzes must subclass `pyquiz.Quiz` and include a `questions` method that
returns an iterable of quizzable objects.

> Quizzable objects implement the `__quiz__` method, which returns a
markdown version of the quiz, and the `__check__` method, which accepts a list
of answers and then returns results as markdown.

**Standard Questions**

A quiz with standard questions would resemble the following. Note that the
first answer choice provided is assumed to be the correct answer.

```
class YourQuiz(Quiz):

  url = '/yourquiz'

  def questions(self):
    """Returns an iterable of test questions."""
    return [Question(
      'Calculate the slope of y = 2x+3',
      2, 3, 4, 5, 7)]  # assume 2 is the right answer
```

**Vocabulary**

Quizzes with vocabulary should specify a `terms` method and then invoke
built-in or custom question types.

```
class YourQuiz(Quiz):

  url = '/yourquiz'

  def terms(self):
    """Returns an iterable of vocabulary terms"""
    return [Term('PyQuiz', 'quiz application with configurable completion codes')]

  def questions(self):
    """Returns an iterable of test questions."""
    v = self.vocabulary
    return [v.multiple_choice()]
```

`Question` instances take an additional `check` function as a keyword
argument. This function will override the default method of checking answers
and must return a boolean, True for correct and False otherwise.

## Markdown Quiz Creation

Start all questions with `Q:`. The next markdown-valid list in the file will be
considered the set of all answer choices for that question. The first answer
choice will be considered the answer.

The following is a valid, sample markdown file.

```
Q: How many points at minimum are required to unique identify a polynomial of degree d?

* d+1
* 5
* d-1
* 2
* none of the above
```

## Publishing

When publishing, make sure to specify all target quizzes in the configuration
file `pyquiz.cfg`, under the respective category. List all *paths* to your quiz
files.

**HTML**

To generate HTML statics, specify quizzes under `html:` in `pyquiz.cfg`.

```
html:
  yourquiz.py
  path/to/anotherquiz.py
  test.md
```

Then, run `make html` to generate statics under `pyquiz/html/`.

**App**

To specify which apps will go live, specify quizzes under `app:` in
`pyquiz.cfg`.

```
app:
  yourquiz.py
  path/to/anotherquiz.py
  test.md
```

Your application, once launched, will automatically send these quizzes live.

## Installation

Clone this repository, using `git clone https://github.com/alvinwan/PyQuiz.git`.

Check that Python3 is installed using `make check`. Then, run the installation using `make install`.

In case the installation script fails, you may execute the contents of the bash script line by line:

1. Setup a new virtual environment: `python3 -m virtualenv env`.
1. Start the virtual environment: `source env/bin/activate`.
1. Install all requirements `pip install -r requirements.txt`.

> To activate the virtual environment for the future, use `source activate.sh`.
