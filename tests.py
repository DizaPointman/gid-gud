import os

from app.managers.content_manager import ContentManager

os.environ['DATABASE_URL'] = 'sqlite://'

from datetime import datetime, timezone, timedelta
import unittest
from app.factory import create_app
from app.factory import db
from app.models import Category, User, GidGud
from pytz import utc
from functools import wraps


def get_category_by_name(user, name):
    """
    Retrieve a category by name from the user's categories.
    """
    return next((c for c in user.categories if c.name == name), None)

class BullshitGenerator():

    def __init__(self, c_man):
        self.c_man = c_man

    def gen_cat_tree(self, user=None, tree_height=None):
        categories = []

        # Creating the default category
        c0 = self.c_man.return_or_create_category(user=user)
        categories.append(c0)
        parent_category = c0

        # Generate tree for tree_height = 5
        # 'root'
        # 'root' -> 'cat1'
        # 'root' -> 'cat2' -> 'cat22'
        # 'root' -> 'cat3' -> 'cat33' -> 'cat333'
        # 'root' -> 'cat4' -> 'cat44' -> 'cat444' -> 'cat4444'
        # 'root' -> 'cat5' -> 'cat55' -> 'cat555' -> 'cat5555' -> 'cat55555'

        for j in range(1, tree_height + 1):
            for i in range(1, j + 1):
                cat_name = 'cat' + (str(j) * i)
                category = self.c_man.return_or_create_category(cat_name, user, parent_category)
                categories.append(category)
                if i != j:
                    parent_category = category
            parent_category = c0

        db.session.commit()

        return categories

    def c_man_alive(self):
        return self.c_man.test_cm()


class BaseTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app(config_class='config.TestingConfig')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Initialize ContentManager instance
        self.c_man = ContentManager()

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

        # Initialize ContentManager
        c_man = self.c_man

        # create four users
        u1 = User(username='john', email='john@example.com')
        u2 = User(username='susan', email='susan@example.com')
        u3 = User(username='mary', email='mary@example.com')
        u4 = User(username='david', email='david@example.com')
        db.session.add_all([u1, u2, u3, u4])

        # Commit because root category creation is based on existing user
        db.session.commit()

        # create four default categories for users
        c1 = c_man.return_or_create_category(user=u1)
        c2 = c_man.return_or_create_category(user=u2)
        c3 = c_man.return_or_create_category(user=u3)
        c4 = c_man.return_or_create_category(user=u4)

        # create four guds
        now = datetime.now(timezone.utc)
        g1 = GidGud(body="post from john", author=u1, category=c1,
                    timestamp=((now + timedelta(seconds=1)).isoformat()),
                    completed_at=((now + timedelta(seconds=10)).isoformat()))
        g2 = GidGud(body="post from susan", author=u2, category=c2,
                    timestamp=((now + timedelta(seconds=4)).isoformat()),
                    completed_at=((now + timedelta(seconds=40)).isoformat()))
        g3 = GidGud(body="post from mary", author=u3, category=c3,
                    timestamp=((now + timedelta(seconds=3)).isoformat()),
                    completed_at=((now + timedelta(seconds=30)).isoformat()))
        g4 = GidGud(body="post from david", author=u4, category=c4,
                    timestamp=((now + timedelta(seconds=2)).isoformat()),
                    completed_at=((now + timedelta(seconds=20)).isoformat()))

        # create one gid
        g5 = GidGud(body="uncompleted_at post from david", author=u4, category=c4,
                    timestamp=((now + timedelta(seconds=2)).isoformat()),
                    completed_at=None)
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

# TODO: implement test for gidgud completion, timedelta and recurrence


class CategoryModelCase(BaseTestCase):

    print("Test: CategoryModelCase")

    def test_return_or_create_category(self):
        # Create a user
        u = User(username='test_user', email='test@example.com')
        db.session.add(u)
        db.session.commit()

        # Initialize ContentManager
        c_man = self.c_man

        # Create or return 'root' category
        root_category = c_man.return_or_create_category(user=u)
        self.assertIsNotNone(root_category)
        self.assertEqual(root_category.name, 'root')

        # Create or return a new category
        new_category = c_man.return_or_create_category(name='new_category', user=u)
        self.assertIsNotNone(new_category)
        self.assertEqual(new_category.name, 'new_category')
        self.assertEqual(new_category.parent.name, 'root')

    def test_bullshit_generator(self):

        # Create a user
        u = User(username='test_user', email='test@example.com')
        db.session.add(u)
        db.session.commit()

        # Initialize ContentManager
        c_man = self.c_man

        # Create category tree
        bs = BullshitGenerator(c_man)
        tree_height = 5
        triangular_number = (tree_height * (tree_height + 1)) // 2
        tree = bs.gen_cat_tree(u, tree_height)

        # Check that the correct amount of categories is generated
        # + 1 for the default category
        self.assertTrue(len(tree) == triangular_number + 1)
        self.assertTrue(tree[0].name == 'root')
        self.assertTrue(tree[-1].name == f"cat{(str(tree_height) * tree_height)}")
        self.assertTrue(tree[-1].height == 1)

    def test_possible_parents_and_children(self):

        # Create a user
        u = User(username='test_user', email='test@example.com')
        db.session.add(u)
        db.session.commit()

        # Initialize ContentManager
        c_man = self.c_man

        # Create category tree
        bs = BullshitGenerator(c_man)
        bs.gen_cat_tree(u, 5)

        default_cat = get_category_by_name(u, 'root')
        # Cat1 is child of default, has no children
        cat1 = get_category_by_name(u, 'cat1')
        # Cat5 is child of default, has tree of ancestors up to cat55555
        cat5 = get_category_by_name(u, 'cat5')
        # Cat55555 is child of cat5555, has no children
        cat55555 = get_category_by_name(u, 'cat55555')

        # Default must only return root since it is added to maintain order in formfields
        self.assertTrue(c_man.get_possible_parents(default_cat) == ['root'])

        # Default should return any categories except itself as possible children
        self.assertTrue(len(c_man.get_possible_children(default_cat)) == len(u.categories) - 1)

        # Cat1
        self.assertNotIn(cat55555.name, c_man.get_possible_parents(cat1))
        self.assertNotIn('root', c_man.get_possible_children(cat1))
        self.assertNotIn(cat5.name, c_man.get_possible_children(cat1))

        # Cat5
        self.assertTrue(c_man.get_possible_parents(cat5) == ['root'])
        # All categories possible except cat5 and default_cat
        self.assertTrue(len(c_man.get_possible_children(cat5)) == len(u.categories) - 2)

        # Cat55555
        self.assertTrue(c_man.get_possible_children(cat55555) == [])
        self.assertTrue(len(c_man.get_possible_parents(cat55555)) == len(u.categories) - 1)

    def test_update_height_depth(self):

        # Create a user
        u = User(username='test_user', email='test@example.com')
        db.session.add(u)
        db.session.commit()

        # Initialize ContentManager
        c_man = self.c_man

        # Create category tree
        bs = BullshitGenerator(c_man)
        bs.gen_cat_tree(u, 5)

        default_cat = get_category_by_name(u, 'root')
        # Cat1 is child of default, has no children
        cat1 = get_category_by_name(u, 'cat1')
        # Cat2 is child of default, has child cat22
        cat2 = get_category_by_name(u, 'cat2')
        # Cat22 is child of cat2, has no child
        cat22 = get_category_by_name(u, 'cat22')
        # Cat33 is child of cat3, has tree of ancestors up to cat333
        cat33 = get_category_by_name(u, 'cat33')
        # Cat4 is child of default, has tree of ancestors up to cat4444
        cat4 = get_category_by_name(u, 'cat4')
        # Cat1 is child of default, has tree of ancestors up to cat55555
        cat5 = get_category_by_name(u, 'cat5')

        # Assert height and depth of cat1, cat2, cat5
        self.assertEqual(cat1.depth, 1)
        self.assertEqual(cat1.height, 1)
        self.assertEqual(cat2.depth, 1)
        self.assertEqual(cat2.height, 2)
        self.assertEqual(cat5.depth, 1)
        self.assertEqual(cat5.height, 5)

        # Change parent of cat1 from default to cat2
        cat1.parent = cat2
        db.session.commit()
        c_man.update_depth_and_height(cat2)

        self.assertEqual(cat1.depth, 2)
        self.assertEqual(cat1.height, 1)
        self.assertEqual(cat2.depth, 1)
        self.assertEqual(cat2.height, 2)

        # Change parent of cat1 from cat2 to cat22
        cat1.parent = cat22
        db.session.commit()
        c_man.update_depth_and_height(cat22)

        self.assertEqual(cat1.depth, 3)
        self.assertEqual(cat1.height, 1)
        self.assertEqual(cat2.depth, 1)
        self.assertEqual(cat2.height, 3)
        self.assertEqual(cat22.depth, 2)
        self.assertEqual(cat22.height, 2)

        # Change parent of cat2 to cat33
        cat2.parent = cat33
        db.session.commit()
        c_man.update_depth_and_height(cat33)

        self.assertEqual(cat33.depth, 2)
        self.assertEqual(cat33.height, 4)
        self.assertEqual(cat1.depth, 5)
        self.assertEqual(cat1.height, 1)


    def test_get_possible_parents_for_children(self):
        # Create a user
        u = User(username='test_user', email='test@example.com')
        db.session.add(u)
        db.session.commit()

        # Initialize ContentManager
        c_man = self.c_man

        # Create category tree
        bs = BullshitGenerator(c_man)
        bs.gen_cat_tree(u, 5)

        # Retrieve categories
        default_cat = get_category_by_name(u, 'root')
        cat1 = get_category_by_name(u, 'cat1')
        cat2 = get_category_by_name(u, 'cat2')
        cat22 = get_category_by_name(u, 'cat22')
        cat3 = get_category_by_name(u, 'cat3')
        cat4 = get_category_by_name(u, 'cat4')
        cat5 = get_category_by_name(u, 'cat5')
        cat55555 = get_category_by_name(u, 'cat55555')

        # Test possible parents for children of root (should raise ValueError)
        with self.assertRaises(ValueError):
            c_man.get_possible_parents_for_children(default_cat)

        # Test possible parents for children of cat1 (should return empty since it has no children)
        possible_parents_cat1 = c_man.get_possible_parents_for_children(cat1)
        self.assertEqual(possible_parents_cat1, [])

        # Test possible parents for children of cat5 (should return a flat list of unique possible parents)
        possible_parents_cat5 = c_man.get_possible_parents_for_children(cat5)
        print(f"possible_parents_cat5: {possible_parents_cat5}")
        expected_parents = {'root', 'cat1', 'cat2', 'cat3', 'cat4', 'cat5'}
        self.assertIsInstance(possible_parents_cat5, list)
        self.assertTrue(expected_parents.issubset(possible_parents_cat5))

        # Test possible parents for children of cat55555 (should return empty since it has no children)
        possible_parents_cat55555 = c_man.get_possible_parents_for_children(cat55555)
        self.assertEqual(possible_parents_cat55555, [])

        # Test possible parents for children of cat2 (should return a flat list of unique possible parents)
        possible_parents_cat2 = c_man.get_possible_parents_for_children(cat2)
        self.assertIsInstance(possible_parents_cat2, list)
        self.assertTrue(all(isinstance(name, str) for name in possible_parents_cat2))
        # Ensure that cat 22 and cat55555 are not in the possible parents list
        self.assertTrue(len(possible_parents_cat2) == len(u.categories) - 2)



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