from django.core.management.base import BaseCommand
from intellishop.models.mongodb_models import User
from bson import ObjectId

class Command(BaseCommand):
    help = 'Migrate existing users to include favorites field'

    def handle(self, *args, **options):
        self.stdout.write('Starting favorites field migration...')
        
        # Get all users without favorites field
        users = User.find({'favorites': {'$exists': False}})
        
        migrated_count = 0
        for user in users:
            try:
                # Add empty favorites array to existing users
                User.update_one(
                    {'_id': user['_id']},
                    {'$set': {'favorites': []}}
                )
                migrated_count += 1
                self.stdout.write(f'Migrated user: {user.get("username", "Unknown")}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Failed to migrate user {user.get("username", "Unknown")}: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(f'Migration completed. {migrated_count} users migrated.'))
