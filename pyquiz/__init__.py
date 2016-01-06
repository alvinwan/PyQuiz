from flask import Flask, request, render_template
from importlib import import_module
from .util import files_by_tag, quiz, check, md2quiz, rq2responses

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
            html = md2quiz(check(q, rq2responses(request)))
        print(quiz(q))
        html = md2quiz(quiz(q))
        print('C')
        return render_template('quiz.html', html=html)
    view.__name__ = q.name
    return view

for quiz in quizzes:
    app.add_url_rule(quiz.url, quiz.name, view_generator(quiz),
        methods=['GET', 'POST'])
