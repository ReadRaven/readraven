from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

from celery.result import AsyncResult

User = get_user_model()


class Command(BaseCommand):
    def handle(self, *args, **options):
        for arg in args:
            if arg == 'users':
                for user in User.objects.all():
                    self.stdout.write(user.email)
                self.stdout.write('================')
            elif arg == 'imports':
                success = []
                fail = []
                for user in User.objects.all():
                    result = AsyncResult(user.sync_task_id)
                    if result.ready() == True:
                        success.append(user.email)
                    else:
                        fail.append(user.email)

                self.stdout.write('Successful Syncs from Reader')
                self.stdout.write('================')
                for user in success:
                    self.stdout.write(user)

                self.stdout.write('\nFailed Syncs from Reader')
                self.stdout.write('================')
                for user in fail:
                    self.stdout.write(user)

                self.stdout.write('\n================')

        self.stdout.write('Total users: %s' % User.objects.all().count())
