# Dropdowns
https://hackanons.com/2021/09/flask-dropdown-menu-everything-you-need-to-know.html

# Beauty/Style
https://blog.miguelgrinberg.com/post/beautiful-interactive-tables-for-your-flask-templates

SQLite JSON

https://docs.sqlalchemy.org/en/13/dialects/sqlite.html#sqlalchemy.dialects.sqlite.JSON
https://docs.sqlalchemy.org/en/13/core/type_basics.html#sqlalchemy.types.JSON.JSONElementType
https://stackoverflow.com/questions/75379948/what-is-correct-mapped-annotation-for-json-in-sqlalchemy-2-x-version

# Categories

Change to JSON in user model and reference in Gid/Gud

# Bughunt

category_name = 'existing_category'

# Check if the category exists and is a list
if category_name in categories_dict and isinstance(categories_dict[category_name], list):
    # If the category exists and is a list, append the value
    categories_dict[category_name].append('new_value')
else:
    # If the category doesn't exist or is not a list, create it as a list and add the value
    categories_dict[category_name] = ['new_value']