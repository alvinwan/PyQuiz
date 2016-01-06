from flask import Flask, request, render_template
from .util import files_by_tag, check, rq2responses, rq2quiz, path2quiz

app = Flask(__name__)

@app.route('/')
def index():
    return '<p>Quiz app launched. Available quizzes:</p><ul>%s</ul>' % '\n'.join(['<li><a href="%s">%s</a></li>' % (quiz.url, quiz.name) for quiz in quizzes])

quizzes = [path2quiz(path) for path in files_by_tag('app')]

def view_generator(quiz):
    def view():
        if request.method == 'POST':
            old_quiz = rq2quiz(request)
            results = check(old_quiz, rq2responses(request))
            return render_template('quiz_corrected.html', quiz=old_quiz,
                results=results)
        return render_template('quiz.html', quiz=quiz)
    view.__name__ = quiz.name
    return view

for quiz in quizzes:
    app.add_url_rule(quiz.url, quiz.name, view_generator(quiz),
        methods=['GET', 'POST'])
