import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models


# ── User Manager ──────────────────────────────────────────────────────────────
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError('Email is required')
        user = self.model(email=self.normalize_email(email), **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra):
        extra.setdefault('role', 'system_admin')
        extra.setdefault('is_superuser', True)
        extra.setdefault('is_staff', True)
        return self.create_user(email, password, **extra)


# ── User ──────────────────────────────────────────────────────────────────────
class User(AbstractBaseUser, PermissionsMixin):

    class Role(models.TextChoices):
        STUDENT      = 'student',      'Student'
        CLUB_ADMIN   = 'club_admin',   'Club Admin'
        SYSTEM_ADMIN = 'system_admin', 'System Admin'

    email    = models.EmailField(unique=True)
    username = models.CharField(max_length=50, unique=True)
    role     = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    is_active = models.BooleanField(default=True)
    is_staff  = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['username']

    def is_student(self):
        return self.role == self.Role.STUDENT

    def is_club_admin(self):
        return self.role == self.Role.CLUB_ADMIN

    def is_system_admin(self):
        return self.role == self.Role.SYSTEM_ADMIN

    def save(self, *args, **kwargs):
        if self.role == self.Role.SYSTEM_ADMIN:
            self.is_staff = True
        else:
            self.is_staff = False
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username


# ── Student ───────────────────────────────────────────────────────────────────
class Student(models.Model):
    user       = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student')
    major      = models.CharField(max_length=50)
    year_group = models.IntegerField()

    def __str__(self):
        return f"{self.user.username} - Class of {self.year_group}, {self.major}"


# ── Club ──────────────────────────────────────────────────────────────────────
class Club(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name        = models.CharField(max_length=255)
    description = models.TextField()
    slug        = models.SlugField(unique=True)

    def __str__(self):
        return self.name


# ── ClubAdmin — Modified Singleton (max 3 per club) ──────────────────────────
class ClubAdmin(models.Model):
    """
    Modified Singleton Pattern:
    A club can have at most 3 ClubAdmin instances.
    Attempting to create a 4th raises a ValidationError.
    This mirrors the Singleton pattern's controlled instantiation,
    extended to allow a fixed maximum pool of 3 instead of 1.
    """
    MAX_ADMINS_PER_CLUB = 3

    user     = models.OneToOneField(User, on_delete=models.CASCADE, related_name='club_admin_profile')
    club     = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='admins')
    position = models.CharField(max_length=100)

    def clean(self):
        """Enforce the max 3 admins per club constraint."""
        if self.club_id:
            existing = ClubAdmin.objects.filter(club=self.club)
            # Exclude self when editing an existing record
            if self.pk:
                existing = existing.exclude(pk=self.pk)
            if existing.count() >= self.MAX_ADMINS_PER_CLUB:
                raise ValidationError(
                    f'"{self.club.name}" has reached its maximum of '
                    f'{self.MAX_ADMINS_PER_CLUB} club admins. '
                    f'A transfer request must be submitted to add a new admin.'
                )

    def save(self, *args, **kwargs):
        # full_clean() runs clean() and field validation before every save
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} — {self.club.name} ({self.position})"


# ── SystemAdmin — Classic Singleton (only one) ────────────────────────────────
class SystemAdmin(models.Model):
    """
    Singleton Pattern:
    Only one SystemAdmin instance can exist in the system at any time.
    Attempting to create a second one raises a ValidationError,
    mirroring the Singleton pattern's guarantee of a single global instance.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='system_admin_profile')

    def clean(self):
        """Enforce the single system admin constraint."""
        existing = SystemAdmin.objects.all()
        # Exclude self when editing the existing record
        if self.pk:
            existing = existing.exclude(pk=self.pk)
        if existing.exists():
            raise ValidationError(
                'A system admin already exists. '
                'Only one system admin is permitted at a time.'
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} — System Admin"


# ── ClubAdminTransferRequest ──────────────────────────────────────────────────
class ClubAdminTransferRequest(models.Model):
    """
    Handles transfer of a ClubAdmin slot when a club has reached
    its maximum of 3 admins. The requester specifies which existing
    admin they want to replace. The system admin approves or rejects.
    On approval the old admin is removed and the requester is added.
    On rejection the requester is notified.
    A user can only have one pending request at a time.
    """

    class Status(models.TextChoices):
        PENDING  = 'pending',  'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    club             = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='transfer_requests')
    requester        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transfer_requests')
    admin_to_replace = models.ForeignKey(ClubAdmin, on_delete=models.CASCADE, related_name='replacement_requests')
    reason           = models.TextField()
    status           = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    def clean(self):
        """A user can only have one pending request at a time."""
        if self.requester_id:
            existing = ClubAdminTransferRequest.objects.filter(
                requester=self.requester,
                status=self.Status.PENDING,
            )
            if self.pk:
                existing = existing.exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError(
                    'You already have a pending transfer request. '
                    'Please wait for it to be reviewed before submitting another.'
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def approve(self):
        """
        Approve the transfer request:
        1. Remove the existing ClubAdmin record
        2. Create a new ClubAdmin record for the requester
        3. Update requester role to club_admin
        4. Mark request as approved
        Notifications are handled in the view layer.
        """
        old_admin_user = self.admin_to_replace.user

        # Remove old admin
        self.admin_to_replace.delete()

        # Update old admin's role back to student
        old_admin_user.role = User.Role.STUDENT
        old_admin_user.save()

        # Create new admin — bypass modified singleton check
        # since we just freed up a slot by deleting the old one
        ClubAdmin.objects.create(
            user=self.requester,
            club=self.club,
            position='Club Admin',
        )

        # Update requester role
        self.requester.role = User.Role.CLUB_ADMIN
        self.requester.save()

        # Mark approved
        self.status = self.Status.APPROVED
        # Skip full_clean on status update to avoid re-triggering pending check
        super().save()

        return old_admin_user

    def reject(self):
        """Reject the transfer request."""
        self.status = self.Status.REJECTED
        super().save()

    def __str__(self):
        return (
            f"Transfer request by {self.requester.username} "
            f"for {self.club.name} "
            f"[{self.status}]"
        )
