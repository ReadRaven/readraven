from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    def handle(self, *args, **options):
        for user in User.objects.all():
            self.stdout.write(user.email)

        self.stdout.write('================')
        self.stdout.write('Total users: %s' % User.objects.all().count())
