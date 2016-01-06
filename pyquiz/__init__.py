from flask import Flask, request, render_template
from importlib import import_module
from .util import files_by_tag, check, rq2responses

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
            results = check(q, rq2responses(request))
            return render_template('quiz_corrected.html', quiz=quiz,
                results=results)
        print(quiz)
        return render_template('quiz.html', quiz=quiz)
    view.__name__ = q.name
    return view

for quiz in quizzes:
    app.add_url_rule(quiz.url, quiz.name, view_generator(quiz),
        methods=['GET', 'POST'])
