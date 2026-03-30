from django.core.management.base import BaseCommand
from myapp.models import Category # noqa


class Command(BaseCommand):
    help = "Seed default expense categories"

    def handle(self, *args, **kwargs):
        categories = [
            "Health",
            "Leisure",
            "Home",
            "Cafe",
            "Education",
            "Gifts",
            "Groceries",
            "Family",
            "Workout",
            "Transportation",
            "Other",
        ]

        created_count = 0

        for name in categories:
            obj, created = Category.objects.get_or_create(name=name)
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created: {name}"))
            else:
                self.stdout.write(f"Already exists: {name}")

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. {created_count} new categories added."
        ))