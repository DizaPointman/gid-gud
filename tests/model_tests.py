# tests/model_tests.py

from datetime import datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta
from app.models import Category, CompletionTable, GidGud, User
from tests.base_test_case import BaseTestCase
from app.factory import db
from pytz import utc


class BullshitGeneratorModelCase(BaseTestCase):

    print("Test: BullshitGeneratorModelCase")

    # TODO: tests for category management functions
    # TODO: tests for category management routes

    def test_bullshit_generator(self):

        bs = self.bs
        alive = bs.test_bs()
        self.assertEqual(alive, "Bullshit generator is alive")

    def test_bullshit_categories(self):

        # Create a user
        u = User(username='test_user', email='test@example.com')
        db.session.add(u)
        db.session.commit()

        # Create category tree
        bs = self.bs
        tree_height = 5
        triangular_number = (tree_height * (tree_height + 1)) // 2
        tree = bs.gen_cat_tree(u, tree_height)

        # Check that the correct amount of categories is generated
        # + 1 for the default category
        self.assertTrue(len(tree) == triangular_number + 1)
        self.assertTrue(tree[0].name == 'root')
        self.assertTrue(tree[-1].name == f"cat{(str(tree_height) * tree_height)}")

class UserModelCase(BaseTestCase):

    # TODO: tests for user management functions
    # TODO: tests for user management routes

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

    def test_follow_guds(self):
        # TODO: rework this

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
        c1 = c_man.cat_get_or_create_root(user=u1)
        c2 = c_man.cat_get_or_create_root(user=u2)
        c3 = c_man.cat_get_or_create_root(user=u3)
        c4 = c_man.cat_get_or_create_root(user=u4)

        # create four gidguds
        # TODO: change follow to completion entries in user model, adapt test
        now = datetime.now(timezone.utc)
        g1 = GidGud(body="post from john", author=u1, category=c1,
                    created_at=((now + timedelta(seconds=1)).isoformat()))
        g2 = GidGud(body="post from susan", author=u2, category=c2,
                    created_at=((now + timedelta(seconds=4)).isoformat()))
        g3 = GidGud(body="post from mary", author=u3, category=c3,
                    created_at=((now + timedelta(seconds=3)).isoformat()))
        g4 = GidGud(body="post from david", author=u4, category=c4,
                    created_at=((now + timedelta(seconds=2)).isoformat()))

        db.session.add_all([g1, g2, g3, g4])
        db.session.commit()

        # create four guds from gidguds
        g11 = CompletionTable(
            gidgud_id=g1.id,
            user_id=g1.user_id,
            body=g1.body,
            category_name=g1.category.name,
            category_id=g1.category_id,
            completed_at=((datetime.fromisoformat(g1.created_at) + timedelta(seconds=10)).isoformat())
        )

        g22 = CompletionTable(
            gidgud_id=g2.id,
            user_id=g2.user_id,
            body=g2.body,
            category_name=g2.category.name,
            category_id=g2.category_id,
            completed_at=((datetime.fromisoformat(g2.created_at) + timedelta(seconds=10)).isoformat())
        )

        g33 = CompletionTable(
            gidgud_id=g3.id,
            user_id=g3.user_id,
            body=g3.body,
            category_name=g3.category.name,
            category_id=g3.category_id,
            completed_at=((datetime.fromisoformat(g3.created_at) + timedelta(seconds=10)).isoformat())
        )

        g44 = CompletionTable(
            gidgud_id=g4.id,
            user_id=g4.user_id,
            body=g4.body,
            category_name=g4.category.name,
            category_id=g4.category_id,
            completed_at=((datetime.fromisoformat(g4.created_at) + timedelta(seconds=10)).isoformat())
        )

        db.session.add_all([g11, g22, g33, g44])
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
        self.assertEqual(f1, [g22, g44, g11])
        self.assertEqual(f2, [g22, g33])
        self.assertEqual(f3, [g33, g44])
        self.assertEqual(f4, [g44])

        # check that gid g5 is not in following guds
        self.assertNotIn(g4, f4)

class CategoryModelCase(BaseTestCase):

    print("Test: CategoryModelCase")

    def test_category_creation(self):
        # Create a user
        user = User(username='test_user', email='test@example.com')
        db.session.add(user)
        db.session.commit()

        # Create a category
        category = Category(name='Test Category', user_id=user.id)
        db.session.add(category)
        db.session.commit()

        # Fetch the category from the database
        fetched_category = Category.query.get(category.id)
        self.assertEqual(fetched_category.name, 'Test Category')
        self.assertEqual(fetched_category.user_id, user.id)

    def test_set_path_root_category(self):
        user = User(username='test_user', email='test@example.com')
        db.session.add(user)
        db.session.commit()

        root_category = Category(name='root', user_id=user.id)
        db.session.add(root_category)
        db.session.commit()

        # Set path for root category
        root_category.set_path()
        self.assertEqual(root_category.path, str(root_category.id))

    def test_set_path_child_category(self):
        user = User(username='test_user', email='test@example.com')
        db.session.add(user)
        db.session.commit()

        root_category = Category(name='root', user_id=user.id)
        root_category.save()

        child_category = Category(name='Child Category', user_id=user.id, parent_id=root_category.id)
        db.session.add(child_category)
        db.session.commit()

        child_category.set_path()
        self.assertEqual(child_category.path, f'{root_category.id}.{child_category.id}')

    def test_validate_path(self):
        user = User(username='test_user', email='test@example.com')
        db.session.add(user)
        db.session.commit()

        root_category = Category(name='root', user_id=user.id)
        root_category.save()

        child_category = Category(name='Child Category', user_id=user.id, parent_id=root_category.id)
        child_category.save()

        # Validate path
        try:
            child_category.validate_path()
        except ValueError:
            self.fail("validate_path raised ValueError unexpectedly!")

    def test_validate_invalid_path(self):
        user = User(username='test_user', email='test@example.com')
        db.session.add(user)
        db.session.commit()

        invalid_category = Category(name='Invalid Category', user_id=user.id)
        invalid_category.path = 'invalid_path'
        db.session.add(invalid_category)
        db.session.commit()

        with self.assertRaises(ValueError):
            invalid_category.validate_path()

    def test_get_parent(self):
        user = User(username='test_user', email='test@example.com')
        db.session.add(user)
        db.session.commit()

        root_category = Category(name='root', user_id=user.id)
        root_category.save()

        child_category = Category(name='Child Category', user_id=user.id, parent_id=root_category.id)
        child_category.save()

        self.assertEqual(child_category.get_parent(), root_category)

    def test_get_children(self):
        user = User(username='test_user', email='test@example.com')
        db.session.add(user)
        db.session.commit()

        root_category = Category(name='root', user_id=user.id)
        root_category.save()

        child1 = Category(name='Child Category 1', user_id=user.id, parent_id=root_category.id)
        child1.save()
        child2 = Category(name='Child Category 2', user_id=user.id, parent_id=root_category.id)
        child2.save()

        children = root_category.get_children()
        self.assertIn(child1, children)
        self.assertIn(child2, children)

    def test_has_children(self):
        user = User(username='test_user', email='test@example.com')
        db.session.add(user)
        db.session.commit()

        root_category = Category(name='root', user_id=user.id)
        root_category.save()

        self.assertFalse(root_category.has_children)

        child_category = Category(name='Child Category', user_id=user.id, parent_id=root_category.id)
        child_category.save()

        self.assertTrue(root_category.has_children)

    def test_get_descendants(self):
        user = User(username='test_user', email='test@example.com')
        db.session.add(user)
        db.session.commit()

        root_category = Category(name='root', user_id=user.id)
        root_category.save()
        print(f"root path: {root_category.path}")

        child1 = Category(name='Child Category 1', user_id=user.id, parent_id=root_category.id)
        child1.save()
        child2 = Category(name='Child Category 2', user_id=user.id, parent_id=root_category.id)
        child2.save()
        grandchild = Category(name='Grandchild Category', user_id=user.id, parent_id=child1.id)
        grandchild.save()

        descendants = root_category.get_descendants()
        self.assertIn(child1, descendants)
        self.assertIn(child2, descendants)
        self.assertIn(grandchild, descendants)

    def test_get_max_descendants_depth(self):
        user = User(username='test_user', email='test@example.com')
        db.session.add(user)
        db.session.commit()

        root_category = Category(name='root', user_id=user.id)
        root_category.save()

        child1 = Category(name='Child Category 1', user_id=user.id, parent_id=root_category.id)
        child1.save()
        grandchild = Category(name='Grandchild Category', user_id=user.id, parent_id=child1.id)
        grandchild.save()

        self.assertEqual(root_category.get_max_descendants_depth(), 3)
        self.assertEqual(child1.get_max_descendants_depth(), 3)

    def test_get_subtree_depth(self):
        user = User(username='test_user', email='test@example.com')
        db.session.add(user)
        db.session.commit()

        root_category = Category(name='root', user_id=user.id)
        root_category.save()

        child1 = Category(name='Child Category 1', user_id=user.id, parent_id=root_category.id)
        child1.save()
        grandchild = Category(name='Grandchild Category', user_id=user.id, parent_id=child1.id)
        grandchild.save()

        self.assertEqual(root_category.get_subtree_depth(), 3)
        self.assertEqual(child1.get_subtree_depth(), 2)

    def test_is_descendant_of(self):
        user = User(username='test_user', email='test@example.com')
        db.session.add(user)
        db.session.commit()

        root_category = Category(name='root', user_id=user.id)
        root_category.save()

        child1 = Category(name='Child Category 1', user_id=user.id, parent_id=root_category.id)
        child1.save()
        grandchild = Category(name='Grandchild Category', user_id=user.id, parent_id=child1.id)
        grandchild.save()

        self.assertTrue(grandchild.is_descendant_of(root_category))
        self.assertTrue(grandchild.is_descendant_of(child1))
        self.assertFalse(child1.is_descendant_of(grandchild))

class GidGudModelCase(BaseTestCase):

    def setUp(self):
        super().setUp()
        # Create a user
        self.user = User(username='test_user', email='test@example.com')
        db.session.add(self.user)
        db.session.commit()

        # Create a category
        self.category = Category(name='Test Category', user=self.user)
        db.session.add(self.category)
        db.session.commit()

    def test_update_rec_next_no_recurrence(self):
        gidgud = GidGud(
            body='Test GidGud',
            user_id=self.user.id,
            category_id=self.category.id,
            rec=False
        )
        db.session.add(gidgud)
        db.session.commit()

        timestamp = datetime(2024, 1, 1)
        next_date = gidgud.update_rec_next(timestamp)

        self.assertIsNone(next_date)

    def test_update_rec_next_with_recurrence(self):
        gidgud = GidGud(
            body='Test GidGud',
            user_id=self.user.id,
            category_id=self.category.id,
            rec=True,
            rec_val=2,
            rec_unit='days'
        )
        db.session.add(gidgud)
        db.session.commit()

        timestamp = datetime(2024, 1, 1)
        next_date = gidgud.update_rec_next(timestamp)

        expected_date = timestamp + timedelta(days=2)
        self.assertEqual(next_date, expected_date)

    def test_update_rec_next_with_months(self):
        gidgud = GidGud(
            body='Test GidGud',
            user_id=self.user.id,
            category_id=self.category.id,
            rec=True,
            rec_val=2,
            rec_unit='months'
        )
        db.session.add(gidgud)
        db.session.commit()

        timestamp = datetime(2024, 1, 1)
        next_date = gidgud.update_rec_next(timestamp)

        expected_date = timestamp + relativedelta(months=2)
        self.assertEqual(next_date, expected_date)

    def test_update_rec_next_with_years(self):
        gidgud = GidGud(
            body='Test GidGud',
            user_id=self.user.id,
            category_id=self.category.id,
            rec=True,
            rec_val=1,
            rec_unit='years'
        )
        db.session.add(gidgud)
        db.session.commit()

        timestamp = datetime(2024, 1, 1)
        next_date = gidgud.update_rec_next(timestamp)

        expected_date = timestamp + relativedelta(years=1)
        self.assertEqual(next_date, expected_date)

    def test_add_completion_entry(self):
        gidgud = GidGud(
            body='Test GidGud',
            user_id=self.user.id,
            category_id=self.category.id
        )
        db.session.add(gidgud)
        db.session.commit()

        timestamp = datetime(2024, 1, 1)
        completion = gidgud.add_completion_entry(timestamp)

        self.assertIsInstance(completion, CompletionTable)
        self.assertEqual(completion.gidgud_id, gidgud.id)
        self.assertEqual(completion.user_id, gidgud.user_id)
        self.assertEqual(completion.body, gidgud.body)
        self.assertEqual(completion.category_id, gidgud.category_id)
        self.assertEqual(completion.completed_at, timestamp.isoformat())