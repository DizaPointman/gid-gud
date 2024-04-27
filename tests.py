import os
os.environ['DATABASE_URL'] = 'sqlite://'

from datetime import datetime, timezone, timedelta
import unittest
from app import app, db
from app.models import Category, User, GidGud
from pytz import utc

class UserModelCase(unittest.TestCase):

    print("Test: UserModelCase")

    def setUp(self):
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()
        print("Test: UserModelCase - SetUp")

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        print("Test: UserModelCase - TearDown")

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

class CategoryModelCase(unittest.TestCase):

    print("Test: CategoryModelCase")

    def setUp(self):
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()
        print("Test: CategoryModelCase - SetUp")

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        print("Test: CategoryModelCase - TearDown")

    def test_update_level(self):

        # Create a user
        self.user = User(username='test_user', email='test@example.com')
        db.session.add(self.user)
        db.session.commit()

        # Create the default category for the user
        self.default_category = Category(name='default', user_id=self.user.id)
        db.session.add(self.default_category)
        db.session.commit()

        # Create 6 categories with default as parent
        self.categories = []
        for i in range(1, 7):
            category = Category(name=f'category_{i}', user_id=self.user.id, parent_id=self.default_category.id)
            db.session.add(category)
            self.categories.append(category)
        db.session.commit()

        # Apply update_level on each category once
        for category in self.categories:
            category.update_level()
            db.session.commit()

        # Assert default category level maintains 0
        default_category_level = Category.query.filter_by(name='default').first().level
        self.assertEqual(default_category_level, 0)

        # Assert all other categories should have level 1
        other_categories_levels = [category.level for category in self.categories if category.name != 'default']
        self.assertEqual(set(other_categories_levels), {1})

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