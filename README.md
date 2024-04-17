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

## PROBLEM

1. if delete afterwards:
2. set defaults for form.data

Overall:

1. recreate default choices:
    1.1 parent: (current parent +) 'No Parent' + possible parents via function
    1.2 gidguds: 'No GidGuds' OR possible choices via function
    1.3 children: 'No Children' OR possible choices via function

2. create default values:
    2.1 if value = None: 'No Parent', 'No GidGuds', 'No Children'

3. create check to set None values in form to default values

4. change 'if block' after form validation:
    3.1 implement correct interpretation of new or default values
    3.2 if form.attribute.data != current_value OR default_value
-------------------------------------

Problem is, if I. send The object from the delegate with parameters. Displaying the template. the template in the correct way. 
Then I can achieve that the template Decides which form to display. 
But when I submit It does not Follow on To the deleting part. Where the redirect to delete route should happen 

It's also not working to change. the formation to redirect. 

Question 

Does the form not finish Because I display only Fields. And may have forgotten To set default values 
That would kick in when I submit the form. 

How to find out If the farm has Sufficient data to submit. 

solution 1 

Possible solution Could we make a second form? That just displays the attributes we want to alter. 
probably easiest way

Solution 2

Assure that the form has all default values That are needed to submit. 
nope, 99%

Solution 3 

Check if there's a building function. To adjust this play, parts of a flask form 

Solution 4

We make a second template. Which accept parameters for deletion 

Solution 5. 

Remove data required validators from form Try together with solution 2. 
nope

solution 6
send 5 letters in dla and make every field depend on a letter

solution 7

- build second template 
- catch referral from delete route

    from flask import request

    @app.route('/delete_category/<int:id>', methods=['GET', 'DELETE', 'POST'])
    def delete_category(id):
        # Get the URL of the referring page
        referrer = request.referrer
        if request.referrer and request.referrer.startswith('http://127.0.0.1:5000/source'):

        # Check if the referrer URL ends with the URL pattern of the delete_category route
        if referrer and referrer.endswith(f'/delete_category/{id}'):
            # The redirect stems from the delete_category route
            return True
        else:
            # The redirect does not stem from the delete_category route
            return False


## TODO

To check and manipulate the request data along with the form data, you can access request.form and modify its values as needed before populating the form. Here's how you can do it:

    Check and manipulate the request data before populating the form.
    Populate the form with the modified request data.
    Validate the form.

Here's an example:

python

from flask import request

### Check and manipulate the request data
if request.method == 'POST':
    # Get the form data from the request
    form_data = request.form

    # Check if 'parent' field is None or 'None'
    if form_data.get('parent') in (None, 'None'):
        # Manipulate the 'parent' field value
        form_data['parent'] = 'default_parent_value'

    # Populate the form with the modified request data
    form = EditCategoryForm(formdata=form_data)

    # Validate the form
    if form.validate():
        # Form is valid, process the data
        # ...
    else:
        # Form is invalid, handle errors
        # ...
else:
    # Create an empty form for GET request
    form = EditCategoryForm()

### Render the template with the form
return render_template('your_template.html', form=form)

In this example:

    We first check if the request method is POST.
    If it is, we get the form data from the request and manipulate it if necessary.
    Then, we populate the form with the modified request data.
    After that, we validate the form. If it's valid, we process the data; otherwise, we handle errors.
    If the request method is not POST (i.e., it's a GET request), we create an empty form to render the template.

### Next feature

#### GitGud overhaul

- Separation gid/gud
- If gid: Completed true
- Create gud from gid if completed
- Recurrence
- Implement timer
- Better form field for timer
- 69:69 / days:hours / Monthly:weekly / Every X of Y

### Possible features

1. CSS via bootstrap or tailwind. 
- UI redesign. 
- Light and dark mode. 

2. Input sanitation and flash handler. 

3. Creation of test library. 
- Integrate profiling. 
- Existing library Or create package. 
- Possibility to measure routes or functions. 
- Want to out a measure for Memory. Execution time Database queries 
- Optimization of eager and lazy loading 
- Optimizing request types for routes. 

4. Add amount unit and times to gidgud. 
- Let user create templates. 
- Favorite templates 
- Statistics page optical overhaul. 
- Advanced filters and data display 

5. Avatars 
- Implement avatar progression 
- One avatar or different avatars depending on category.

6. Integration of other platform studs via API 

7. User options. 
- UI customization. 
- Cringe mode - Good girl. Good boy 

8. Task breaker 

9. Correct read me and implement development log 