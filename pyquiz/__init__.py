from flask import Flask, request, render_template
from jinja2 import Environment
from .util import files_by_tag, check, rq2responses, rq2quiz, path2quiz
from markdown import markdown

app = Flask(__name__)

@app.route('/')
def index():
    return '<p>Quiz app launched. Available quizzes:</p><ul>%s</ul>' % '\n'.join(['<li><a href="%s">%s</a></li>' % (quiz.url, quiz.name) for quiz in quizzes])

quizzes = [path2quiz(path) for path in files_by_tag('app')]

def view_generator(source, name):
    def view():
        if request.method == 'POST':
            quiz = rq2quiz(request)
            results = check(quiz, rq2responses(request))
            return render_template('quiz_corrected.html', quiz=quiz,
                results=results)
        quiz = path2quiz(source)
        if quiz.shuffle_on_view:
            quiz.shuffle()  # TODO convert to hook decorator
        return render_template('quiz.html', quiz=quiz)
    view.__name__ = name
    return view

for quiz in quizzes:
    app.add_url_rule(quiz.url, quiz.name,
        view_generator(quiz.source, quiz.name), methods=['GET', 'POST'])

@app.template_filter('markdown')
def md(s):
    return markdown(s)
