from flask import Flask, request
from importlib import import_module
from util import files_by_tag, quiz, check, markdown_to_quiz

app = Flask(__name__)

quizzes = []
for path in files_by_tag('app'):
    if path.endswith('.md'):
        quizzes.append(Quiz.from_markdown(path))
    else:
        path = path.replace('.py', '')
        classname = path.split('/')[-1]
        module = import_module(path.replace('/', '.'))
        Quiz = getattr(module, classname)
        quizzes.append(Quiz())

def view_generator(q):
    def view():
        if request.method == 'POST':
            return md2quiz(check(q, rq2responses(request)))
        return md2quiz(quiz(q))

for quiz in quizzes:
    app.add_url_rule(quiz.url, quiz.name, view_generator(quiz),
        methods=['GET', 'POST'])
