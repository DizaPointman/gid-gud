import os
os.environ['DATABASE_URL'] = 'sqlite://'

from datetime import datetime, timezone, timedelta
import unittest
from app import app, db
from app.models import Category, User, GidGud
from pytz import utc
from functools import wraps


def get_category_by_name(user, name):
    """
    Retrieve a category by name from the user's categories.
    """
    return next((c for c in user.categories if c.name == name), None)

class BullshitGenerator():

    #FIXME: add complete tree as comment for visualization

    def gen_cat_tree(self, user=None, tree_height=None):

        categories = []

        # Creating the default category
        c0 = Category(name='default', user=user, parent=None)
        c0.depth = 0
        c0.height = tree_height
        categories.append(c0)
        parent_category = c0

        # Generate chain of categories following a triangular number sequence, where the number of items in each row increases by one for each successive row
        # Example:
        # tree_depth=1 will generate 1 category: <cat1> with default as parent category
        # tree_depth=2 will generate 2 categories: <cat2> with default as parent, <cat22> with <cat2> as parent
        # and categories for tree_depth 1
        # tree_depth=3 will generate 3 categories: <cat3> with default as parent, <cat33> with <cat3> as parent, <cat333> with <cat33> as parent
        # and categories for tree_depth 1 and 2

        for j in range(1, tree_height + 1):
            for i in range(1, j + 1):
                cat_name = 'cat' + (str(j) * i)
                category = Category(name=cat_name, user=user, parent=parent_category)
                category.depth = len(str(j) * i)
                category.height = 1 + j - i
                categories.append(category)
                if i != j:
                    parent_category = category
            parent_category = c0

        db.session.add_all(categories)
        db.session.commit()

        return categories


class BaseTestCase(unittest.TestCase):

    def setUp(self):
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

class UserModelCase(BaseTestCase):

    print("Test: UserModelCase")

    def test_password_hashing(self):
        u = User(username='susan', email='susan@example.com')
        u.set_password('cat')
        self.assertFalse(u.check_password('dog'))
        self.assertTrue(u.check_password('cat'))

    def test_avatar(self):
        u = User(username='john', email='john@example.com')
        self.assertEqual(u.avatar(128), ('https://www.gravatar.com/avatar/'
                                         'd4c74594d841139328695756648b6bd6'
                                         '?d=identicon&s=128'))

    def test_follow(self):
        u1 = User(username='john', email='john@example.com')
        u2 = User(username='susan', email='susan@example.com')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        following = db.session.scalars(u1.following.select()).all()
        followers = db.session.scalars(u2.followers.select()).all()
        self.assertEqual(following, [])
        self.assertEqual(followers, [])

        u1.follow(u2)
        db.session.commit()
        self.assertTrue(u1.is_following(u2))
        self.assertEqual(u1.following_count(), 1)
        self.assertEqual(u2.followers_count(), 1)
        u1_following = db.session.scalars(u1.following.select()).all()
        u2_followers = db.session.scalars(u2.followers.select()).all()
        self.assertEqual(u1_following[0].username, 'susan')
        self.assertEqual(u2_followers[0].username, 'john')

        u1.unfollow(u2)
        db.session.commit()
        self.assertFalse(u1.is_following(u2))
        self.assertEqual(u1.following_count(), 0)
        self.assertEqual(u2.followers_count(), 0)

    def test_follow_gidguds(self):
        # create four users
        u1 = User(username='john', email='john@example.com')
        u2 = User(username='susan', email='susan@example.com')
        u3 = User(username='mary', email='mary@example.com')
        u4 = User(username='david', email='david@example.com')
        db.session.add_all([u1, u2, u3, u4])

        # create four default categories for users
        c1 = Category(name='default', user=u1)
        c2 = Category(name='default', user=u2)
        c3 = Category(name='default', user=u3)
        c4 = Category(name='default', user=u4)
        db.session.add_all([c1, c2, c3, c4])

        # create four guds
        now = datetime.now(timezone.utc)
        g1 = GidGud(body="post from john", author=u1, category=c1,
                    timestamp=((now + timedelta(seconds=1)).isoformat()),
                    completed=((now + timedelta(seconds=10)).isoformat()))
        g2 = GidGud(body="post from susan", author=u2, category=c2,
                    timestamp=((now + timedelta(seconds=4)).isoformat()),
                    completed=((now + timedelta(seconds=40)).isoformat()))
        g3 = GidGud(body="post from mary", author=u3, category=c3,
                    timestamp=((now + timedelta(seconds=3)).isoformat()),
                    completed=((now + timedelta(seconds=30)).isoformat()))
        g4 = GidGud(body="post from david", author=u4, category=c4,
                    timestamp=((now + timedelta(seconds=2)).isoformat()),
                    completed=((now + timedelta(seconds=20)).isoformat()))

        # create one gid
        g5 = GidGud(body="uncompleted post from david", author=u4, category=c4,
                    timestamp=((now + timedelta(seconds=2)).isoformat()),
                    completed=None)
        db.session.add_all([g1, g2, g3, g4, g5])
        db.session.commit()

        # setup the followers
        u1.follow(u2)  # john follows susan
        u1.follow(u4)  # john follows david
        u2.follow(u3)  # susan follows mary
        u3.follow(u4)  # mary follows david
        db.session.commit()

        # check the following guds of each user
        f1 = db.session.scalars(u1.following_guds()).all()
        f2 = db.session.scalars(u2.following_guds()).all()
        f3 = db.session.scalars(u3.following_guds()).all()
        f4 = db.session.scalars(u4.following_guds()).all()
        self.assertEqual(f1, [g2, g4, g1])
        self.assertEqual(f2, [g2, g3])
        self.assertEqual(f3, [g3, g4])
        self.assertEqual(f4, [g4])

        # check that gid g5 is not in following guds
        self.assertNotIn(g5, f4)

class CategoryModelCase(BaseTestCase):

    print("Test: CategoryModelCase")

    def test_bullshit_generator(self):

        # Create a user
        u = User(username='test_user', email='test@example.com')
        db.session.add(u)
        db.session.commit()

        # Create category tree
        bs = BullshitGenerator()
        tree_height = 5
        triangular_number = (tree_height * (tree_height + 1)) // 2
        tree = bs.gen_cat_tree(u, tree_height)

        # Check that the correct amount of categories is generated
        # + 1 for the default category
        self.assertTrue(len(tree) == triangular_number + 1)
        self.assertTrue(tree[0].name == 'default')
        self.assertTrue(tree[-1].name == f"cat{(str(tree_height) * tree_height)}")
        self.assertTrue(tree[-1].height == 1)

    def test_possible_parents_and_children(self):

        # Create a user
        u = User(username='test_user', email='test@example.com')
        db.session.add(u)
        db.session.commit()

        # Create category tree
        bs = BullshitGenerator()
        bs.gen_cat_tree(u, 5)

        default_cat = get_category_by_name(u, 'default')
        # Cat1 is child of default, has no children
        cat1 = get_category_by_name(u, 'cat1')
        # Cat5 is child of default, has tree of ancestors up to cat55555
        cat5 = get_category_by_name(u, 'cat5')
        # Cat55555 is child of cat5555, has no children
        cat55555 = get_category_by_name(u, 'cat55555')

        # Default must not return any possible parent since it is root category
        self.assertTrue(default_cat.get_possible_parents() == [])

        # Default should return any categories except itself as possible children
        self.assertTrue(len(default_cat.get_possible_children()))

        # Cat1
        self.assertNotIn(cat55555, cat1.get_possible_parents())
        self.assertNotIn(default_cat, cat1.get_possible_children())
        self.assertNotIn(cat5, cat1.get_possible_children())

        # Cat5
        self.assertTrue(cat5.get_possible_parents() == [default_cat])
        # All categories possible except cat5 and default_cat
        self.assertTrue(len(cat5.get_possible_children()) == len(u.categories) - 2)

        # Cat55555
        self.assertTrue(cat55555.get_possible_children() == [])
        self.assertTrue(len(cat55555.get_possible_parents()) == len(u.categories) - 1)

    def test_update_height_depth(self):

        # Create a user
        u = User(username='test_user', email='test@example.com')
        db.session.add(u)
        db.session.commit()

        # Create category tree
        bs = BullshitGenerator()
        bs.gen_cat_tree(u, 5)

        default_cat = get_category_by_name(u, 'default')
        # Cat1 is child of default, has no children
        cat1 = get_category_by_name(u, 'cat1')
        # Cat2 is child of default, has child cat22
        cat2 = get_category_by_name(u, 'cat2')
        # Cat22 is child of cat2, has no child
        cat22 = get_category_by_name(u, 'cat22')
        # Cat4 is child of default, has tree of ancestors up to cat4444
        cat4 = get_category_by_name(u, 'cat4')
        # Cat1 is child of default, has tree of ancestors up to cat55555
        cat5 = get_category_by_name(u, 'cat5')

        # Assert height and depth of cat1 and cat2
        self.assertEqual(cat1.depth, 1)
        self.assertEqual(cat1.height, 1)
        self.assertEqual(cat2.depth, 1)
        self.assertEqual(cat2.height, 2)

        # Change parent of cat1 from default to cat2
        cat1.parent = cat2
        cat1.update_height_depth(cat2)

        self.assertEqual(cat1.depth, 2)
        self.assertEqual(cat1.height, 1)
        self.assertEqual(cat2.depth, 1)
        self.assertEqual(cat2.height, 2)

        # Change parent of cat1 from cat2 to cat22
        cat1.parent = cat22
        cat1.update_height_depth(cat22)

        self.assertEqual(cat1.depth, 3)
        self.assertEqual(cat1.height, 1)
        self.assertEqual(cat2.depth, 1)
        self.assertEqual(cat2.height, 3)
        self.assertEqual(cat22.depth, 2)
        self.assertEqual(cat22.height, 2)



if __name__ == '__main__':
    #unittest.main(verbosity=2)

    # Create test suite
    suite = unittest.TestSuite()

    # Add the test cases to the suite
    suite.addTest(unittest.makeSuite(UserModelCase))
    suite.addTest(unittest.makeSuite(CategoryModelCase))

    # Execute the test suite
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

    """
        for c in tree:
            print("\n")
            print(f"name: {c.name}, height: {c.height}, depth: {c.depth}, parent: {c.parent}, children: {c.children}")
            print(f"possible children:")
            print([(f"<{i.name}, {i.height}, {i.depth}>, ") for i in c.get_possible_children()])
            print(f"possible parents:")
            print([(f"<{i.name}, {i.height}, {i.depth}>, ") for i in c.get_possible_parents()])
        """