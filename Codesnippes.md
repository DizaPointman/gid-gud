# Routes

    @app.route('/delete_and_reassign_category/<id>', methods=['GET', 'DELETE', 'POST'])
    @login_required
    def delete_and_reassign_category(id):
        current_category = db.session.scalar(sa.select(Category).where(id == Category.id))
        cat_name = current_category.name
        form = AssignNewCategoryOnDelete()
        form.new_category.choices = [category.name for category in current_user.categories if category != current_category]
        if form.validate_on_submit():
            attached_gidguds = check_if_category_has_gidguds_and_return_list(current_category)
            for gidgud in attached_gidguds:
                app.logger.info(f"ID: {gidgud.id}, BODY:{gidgud}, Category ID: {gidgud.category.id} Category GidGuds: {gidgud.category.gidguds}")
            new_category = db.session.scalar(sa.select(Category).where(Category.name == form.new_category.data))
            app.logger.info(f"Current Cat ID: {current_category.id}, Current Cat Name: {current_category}, GidGuds: {current_category.gidguds}")
            app.logger.info(f"New Cat ID: {new_category.id}, New Cat Name: {new_category}, GidGuds: {new_category.gidguds}")
            for gidgud in attached_gidguds:
                gidgud.category = new_category
                app.logger.info(f"GidGud ID: {gidgud.id}, Category: {gidgud.category}, GidGuds: {gidgud.category.gidguds}")
                #update_gidgud_category(gidgud, new_category)
            db.session.commit()
            db.session.delete(current_category)
            db.session.commit()
            flash(f'Category: {cat_name} deleted!')
            return redirect(url_for('user_categories', username=current_user.username))
        return render_template('delete_and_reassign_category.html', title='Assign new Category', form=form, id=id)



    @app.route('/edit_category/<id>', methods=['GET', 'DELETE', 'POST'])
    @login_required
    def edit_category(id):
        current_category = db.session.scalar(sa.select(Category).where(id == Category.id))
        form = EditCategoryForm()
        form.new_category.choices = [category.name for category in current_user.categories if category != current_category]
        if form.validate_on_submit():

            if form.name.data != current_category.name:
                if form.name.data in current_user.categories:
                    flash('Category already exists. Please choose another name.')
                else:
                    if form.new_category.data == current_category.name and current_category.name != form.name.data:
                        current_category.name = form.name.data
                        db.session.commit()
                        flash(f'Category {current_category.name} was renamed to {form.name.data}.')
                        return redirect(url_for('user_categories', username=current_user.username))
                    elif form.new_category.data == current_category.name and current_category.name == form.name.data:
                        flash('No changes were made.')
                        return redirect(url_for('user_categories', username=current_user.username))
                    elif form.new_category.data != current_category.name and current_category.name != form.name.data:
                        current_category.name = form.name.data
                        db.session.commit()
                        new_category = db.session.scalar(sa.select(Category).where(Category.name == form.new_category.data))
                        for gidgud in new_category.gidguds:
                            update_gidgud_category(gidgud, new_category)
                            db.session.commit()
                        flash(f'Category {current_category.name} was renamed to {form.name.data}.')
                        flash(f'Attached GidGuds were assigned from Category {current_category.name} to Category {new_category.name}')
                        return redirect(url_for('user_categories', username=current_user.username))
                    elif form.new_category.data != current_category.name and current_category.name == form.name.data:
                        new_category = db.session.scalar(sa.select(Category).where(Category.name == form.new_category.data))
                        for gidgud in new_category.gidguds:
                            update_gidgud_category(gidgud, new_category)
                            db.session.commit()
                        flash(f'Attached GidGuds were assigned from Category {current_category.name} to Category {new_category.name}')
                        return redirect(url_for('user_categories', username=current_user.username))
        elif request.method == 'GET':
            form.name.data = current_category.name
            form.new_category.choices = [category.name for category in current_user.categories if category != current_category]
        return render_template('edit_category.html', title='Edit Category', form=form)

# Logging

## SQL to log file

    import logging
    from logging.handlers import RotatingFileHandler
    from flask import Flask
    from flask_sqlalchemy import SQLAlchemy

    # Initialize Flask application
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'your_database_uri'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('sqlalchemy.engine')
    file_handler = RotatingFileHandler('sql.log', maxBytes=1024 * 1024, backupCount=10)
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    # Initialize SQLAlchemy extension
    db = SQLAlchemy(app)

    # Import routes and other modules
    from . import routes  # Import your routes module

## Log to terminal

    from flask import Flask
    from flask_sqlalchemy import SQLAlchemy
    import logging

    # Initialize Flask application
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'your_database_uri'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Set up logging
    logging.basicConfig()
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    logging.getLogger('sqlalchemy.engine').addHandler(logging.StreamHandler())

    # Initialize SQLAlchemy extension
    db = SQLAlchemy(app)

    # Import routes and other modules
    from . import routes  # Import your routes module

