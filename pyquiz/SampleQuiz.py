from .util import Quiz, Term

class SampleQuiz(Quiz):

    url = '/sample'

    def terms(self):
        return [
            Term('Github', '![Github](https://assets-cdn.github.com/images/modules/open_graph/github-mark.png)'),
            Term('Bitbucket', '![Bitbucket](https://pbs.twimg.com/profile_images/615675308243488768/_d8TRzzL.png)'),
            Term('Git', '![Git](https://www.scm-manager.com/wp-content/uploads/2013/04/git-logo.png)'),
            Term('Gitorious', '![Gitorious](https://gitorious.org/logo_only.png)'),
            Term('Gitlab', '![Gitlab](https://pbs.twimg.com/profile_images/616747751661961216/H_6Bders.png)'),
            Term('Mercurial', '![Mercurial](https://upload.wikimedia.org/wikipedia/commons/thumb/9/9a/New_Mercurial_logo.svg/2000px-New_Mercurial_logo.svg.png)')]

    def questions(self):
        return self.vocab.multipleChoice(term_side=False)*5
