from django.conf import settings
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import default_storage
from django.db import models

from oauth2client.django_orm import FlowField, CredentialsField
from south.modelsinspector import add_introspection_rules

from stripe import InvalidRequestError

add_introspection_rules([], ["^oauth2client\.django_orm\.FlowField"])
add_introspection_rules([], ["^oauth2client\.django_orm\.CredentialsField"])


class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None):
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            username=username,
            email=BaseUserManager.normalize_email(email),
        )

        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, username, email, password):
        user = self.create_user(username, email, password)
        user.is_admin = True
        user.save()
        return user


class User(AbstractBaseUser):
    username = models.CharField(max_length=254)
    email = models.EmailField(max_length=254, unique=True, db_index=True)
    flow = FlowField()
    credential = CredentialsField()

    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    sync_task_id = models.CharField(max_length=255, unique=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'

    def get_full_name(self):
        return self.email

    def get_short_name(self):
        return self.email

    def __unicode__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        # Handle whether the user has a specific permission?"
        return True

    def has_module_perms(self, app_label):
        # Handle whether the user has permissions to view the app `app_label`?"
        return True

    @property
    def is_staff(self):
        # Handle whether the user is a member of staff?"
        return self.is_admin

    def subscribe(self, feed):
        feed.add_subscriber(self)

    def is_customer(self):
        # 6/4/2013
        # Enough early testers have said that the credit card is a
        # significant gate. Since we're not charging for now anyway,
        # let's just not ask for it.
        return True

        if settings.DEBUG is True:
            return True

        try:
            customer = self.customer
            try:
                if customer.stripe_customer.get('deleted'):
                    customer.purge()
                    return False
            # If we have an existing user in readraven, but they were
            # somehow deleted from the stripe side, we'll get an
            # exception here. Let's purge them from the readraven side,
            # which also deletes them from the stripe side. This would
            # be a rare situation, but we need to guard...
            except InvalidRequestError, e:
                if e.startswith('No such customer:'):
                    customer.purge()
                    return False

            try:
                current_plan = self.customer.current_subscription.plan
                return True
            # XXX: should be CurrentSubscription.DoesNotExist:
            except:
                return False
        except ObjectDoesNotExist:
            return False

        return False

class UserTakeoutUpload(models.Model):
    zipfile = models.FileField(upload_to='takeouts')
    user = models.ForeignKey(User, related_name='takeouts')
    upload_date = models.DateTimeField(auto_now_add=True)
