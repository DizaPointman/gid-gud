from app.models import Category


def run_maintenance_after_login(session, user_id):
    user_categories = session.query(Category).filter_by(user_id=user_id).all()
    for category in user_categories:
        try:
            category.validate_path()
        except ValueError as e:
            print(f"Error in category {category.id}: {e}")
            if category.parent:
                category.path = f"{category.parent.path}.{category.id}"
            else:
                category.path = str(category.id)
            session.commit()

def maintain_tree_structure(session):
    categories = session.query(Category).all()
    for category in categories:
        try:
            category.validate_path()
        except ValueError:
            _fix_category_path(session, category)
    
    session.commit()

def _fix_category_path(session, category: Category):
    parent_ids = []
    current = category

    while current.parent:
        current = current.parent
        if current.id in parent_ids:
            # Handle cycle by breaking it
            category.parent = None
            break
        parent_ids.append(current.id)

    if category.parent:
        category.path = f"{'.'.join(map(str, reversed(parent_ids)))}.{category.id}"
    else:
        category.path = str(category.id)

    _update_descendant_paths(session, category)

def _update_descendant_paths(session, category: Category):
    descendants = session.query(Category).filter(Category.path.like(f"{category.path}.%")).all()
    for descendant in descendants:
        parent_path = '.'.join(descendant.path.split('.')[:-1])
        descendant.path = f"{parent_path}.{descendant.id}"