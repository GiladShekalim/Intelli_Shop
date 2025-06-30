from django.core.management.base import BaseCommand
from intellishop.utils.mongodb_utils import get_collection_handle
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Clear all coupons from the coupons collection'

    def handle(self, *args, **options):
        self.stdout.write('Clearing coupons collection...')
        
        collection = get_collection_handle('coupons')
        if collection is not None:
            try:
                result = collection.delete_many({})
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully cleared {result.deleted_count} coupons from collection')
                )
                logger.info(f"Cleared {result.deleted_count} coupons from collection")
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error clearing coupons collection: {str(e)}')
                )
                logger.error(f"Error clearing coupons collection: {str(e)}")
        else:
            self.stdout.write(
                self.style.ERROR('Could not access coupons collection')
            )
            logger.error("Could not access coupons collection") 