from django.core.management.base import BaseCommand
from intellishop.models.mongodb_models import User, Coupon
from bson import ObjectId
import json

class Command(BaseCommand):
    help = 'Test favorites functionality'

    def handle(self, *args, **options):
        self.stdout.write('Testing favorites functionality...')
        
        # Test user creation with favorites
        test_user_id = User.create_user(
            username='test_favorites_user',
            password='test123',
            email='test@favorites.com',
            status=['Student'],
            age=25,
            location='Test City',
            hobbies=['electronics']
        )
        
        # Get a test coupon
        test_coupon = Coupon.find_one({})
        if not test_coupon:
            self.stdout.write(self.style.ERROR('No coupons found for testing'))
            return
        
        discount_id = test_coupon['discount_id']
        
        # Test add favorite
        result = User.add_favorite(str(test_user_id), discount_id)
        self.stdout.write(f'Add favorite result: {result}')
        
        # Test check favorite
        is_fav = User.is_favorite(str(test_user_id), discount_id)
        self.stdout.write(f'Is favorite: {is_fav}')
        
        # Test get favorites
        favorites = User.get_favorites(str(test_user_id))
        self.stdout.write(f'Favorites: {favorites}')
        
        # Test remove favorite
        result = User.remove_favorite(str(test_user_id), discount_id)
        self.stdout.write(f'Remove favorite result: {result}')
        
        # Clean up
        User.delete_one({'_id': test_user_id})
        
        self.stdout.write(self.style.SUCCESS('Favorites testing completed'))
