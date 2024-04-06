# Dropdowns
https://hackanons.com/2021/09/flask-dropdown-menu-everything-you-need-to-know.html

# Beauty/Style
https://blog.miguelgrinberg.com/post/beautiful-interactive-tables-for-your-flask-templates

SQLite JSON

https://docs.sqlalchemy.org/en/13/dialects/sqlite.html#sqlalchemy.dialects.sqlite.JSON
https://docs.sqlalchemy.org/en/13/core/type_basics.html#sqlalchemy.types.JSON.JSONElementType
https://stackoverflow.com/questions/75379948/what-is-correct-mapped-annotation-for-json-in-sqlalchemy-2-x-version

https://amercader.net/blog/beware-of-json-fields-in-sqlalchemy/

# FlaskForm / WTForm

Default for SelectField

https://stackoverflow.com/questions/12099741/how-do-you-set-a-default-value-for-a-wtforms-selectfield/12100214#12100214
https://wtforms.readthedocs.io/en/2.3.x/fields/

# Bughunt

# Git

## Rewind and Reset

https://www.30secondsofcode.org/git/s/rewind-to-commit/

## Amend

git commit --amend --no-edit

## Git Flow

Semantic Versioning is used

INFO: there's also a special versioning for python!!!!

https://jeffkreeftmeijer.com/git-flow/

### Changelog

https://mokkapps.de/blog/how-to-automatically-generate-a-helpful-changelog-from-your-git-commit-messages
https://dev.to/devsatasurion/automate-changelogs-to-ease-your-release-282

### Cheatsheet

https://danielkummer.github.io/git-flow-cheatsheet/
https://www.baeldung.com/cs/semantic-versioning

Correct commit msg

https://www.conventionalcommits.org/en/v1.0.0/
https://github.com/angular/angular/blob/22b96b9/CONTRIBUTING.md#-commit-message-guidelines

Git Tag

https://git-scm.com/book/en/v2/Git-Basics-Tagging

### Features

1. git flow feature start [feature name]
2. git flow feature finish [feature name]

### Versioned releases

1. git flow release start 0.1.0
2. git flow release finish '0.1.0'

### Hotfixing production code

1. git flow hotfix start [assets]
2. git flow hotfix finish 'assets'

# Working Strategy

## 1.0

do this for ONE functionality

1. FlaskForm with minimum
2. html template
3. route
4. utils function/s

REPEAT or alter existing for EACH additional feature

## Helpful

    # TODO: Implement error handling here
    # FIXME: This function is not optimized
    # BUG: This block needs refactoring

# Easter Eggs

TabNine Pro 90 days free trial

# What ToDo

send params in dictionary via route to template for conditioning of template

make template behave differently according to values in dict

add child function etc

create meaningful utils functions

CHECK_ and HANDLE_ for use cases to clean up routes and dont repeat code

split routes according to request type: get, delete, post, etc