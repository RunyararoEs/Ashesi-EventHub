from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from users.models import Club, ClubAdmin, Student, SystemAdmin

User = get_user_model()


class UserManagerTests(TestCase):
    def test_create_user_requires_email(self):
        with self.assertRaisesMessage(ValueError, 'Email is required'):
            User.objects.create_user(email='', username='nouser', password='x')

    def test_create_user_stores_credentials(self):
        user = User.objects.create_user(
            email='student@school.edu',
            username='student1',
            password='secret123',
        )
        self.assertEqual(user.email, 'student@school.edu')
        self.assertTrue(user.check_password('secret123'))
        self.assertEqual(user.role, User.Role.STUDENT)
        self.assertFalse(user.is_staff)

    def test_create_superuser_is_staff_and_system_admin(self):
        user = User.objects.create_superuser(
            email='sys@school.edu',
            username='sysadmin',
            password='pw',
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertEqual(user.role, User.Role.SYSTEM_ADMIN)
        self.assertTrue(user.is_system_admin())


class UserRoleAndStaffTests(TestCase):
    def test_student_role_not_staff_after_save(self):
        user = User.objects.create_user(
            email='a@school.edu',
            username='a',
            password='pw',
            role=User.Role.STUDENT,
        )
        user.save()
        self.assertFalse(user.is_staff)

    def test_system_admin_is_staff_after_save(self):
        user = User.objects.create_user(
            email='b@school.edu',
            username='b',
            password='pw',
            role=User.Role.SYSTEM_ADMIN,
            is_superuser=True,
        )
        user.save()
        self.assertTrue(user.is_staff)

    def test_role_helpers(self):
        s = User.objects.create_user(
            email='s@school.edu', username='s', password='pw', role=User.Role.STUDENT
        )
        c = User.objects.create_user(
            email='c@school.edu', username='c', password='pw', role=User.Role.CLUB_ADMIN
        )
        a = User.objects.create_user(
            email='a2@school.edu',
            username='a2',
            password='pw',
            role=User.Role.SYSTEM_ADMIN,
            is_superuser=True,
        )
        self.assertTrue(s.is_student())
        self.assertTrue(c.is_club_admin())
        self.assertTrue(a.is_system_admin())


class ClubModelTests(TestCase):
    def test_club_gets_uuid_primary_key(self):
        club = Club.objects.create(
            name='Robotics',
            description='Build bots',
            slug='robotics',
        )
        self.assertIsNotNone(club.id)
        self.assertEqual(str(club), 'Robotics')


class StudentModelTests(TestCase):
    def test_student_linked_to_user(self):
        user = User.objects.create_user(
            email='stu@school.edu', username='stu', password='pw'
        )
        student = Student.objects.create(
            user=user, major='CS', year_group=2027
        )
        self.assertEqual(student.user, user)
        self.assertEqual(user.student, student)
        self.assertIn('stu', str(student))


class ClubAdminModelTests(TestCase):
    def test_club_admin_str_and_relation(self):
        club = Club.objects.create(
            name='Chess', description='♟', slug='chess-club'
        )
        user = User.objects.create_user(
            email='lead@school.edu',
            username='lead',
            password='pw',
            role=User.Role.CLUB_ADMIN,
        )
        admin = ClubAdmin.objects.create(
            user=user, club=club, position='President'
        )
        self.assertIn('Chess', str(admin))
        self.assertEqual(list(club.admins.all()), [admin])


class SystemAdminModelTests(TestCase):
    def test_system_admin_profile(self):
        user = User.objects.create_user(
            email='root@school.edu',
            username='root',
            password='pw',
            role=User.Role.SYSTEM_ADMIN,
            is_superuser=True,
        )
        profile = SystemAdmin.objects.create(user=user)
        self.assertEqual(user.system_admin_profile, profile)


class UserCascadeTests(TestCase):
    def test_deleting_user_removes_student(self):
        user = User.objects.create_user(
            email='gone@school.edu', username='gone', password='pw'
        )
        Student.objects.create(user=user, major='X', year_group=1)
        user.delete()
        self.assertEqual(Student.objects.count(), 0)
