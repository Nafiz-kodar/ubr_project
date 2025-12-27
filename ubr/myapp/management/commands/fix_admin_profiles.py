from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from myapp.models import Profile


class Command(BaseCommand):
    help = 'Ensure staff/superuser users have Profile.user_type set to Admin'

    def handle(self, *args, **options):
        users = User.objects.filter(is_staff=True)
        for u in users:
            profile, created = Profile.objects.get_or_create(user=u)
            if profile.user_type != 'Admin':
                profile.user_type = 'Admin'
                profile.save()
                self.stdout.write(self.style.SUCCESS(f"Set Admin for {u.username}"))
        self.stdout.write(self.style.SUCCESS('Finished updating admin profiles.'))
