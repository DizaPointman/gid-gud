from models import Category, db

def create_default_root_category(user):
        # Check if 'default' root category exists
        default_category = Category.query.filter_by(name='default', user_id=user.id).first()

        # If 'default' root category doesn't exist, create it
        if not default_category:
            default_category = Category(name='default', user=user)
            db.session.add(default_category)
            db.session.commit()

        return default_category