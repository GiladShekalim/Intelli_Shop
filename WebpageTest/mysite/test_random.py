from intellishop.models.mongodb_models import User, Coupon
from bson import ObjectId
import random

# Get user
user = User.find_one({})
print(f"User: {user.get('username')}")
print(f"Status: {user.get('status')}")
print(f"Hobbies: {user.get('hobbies')}")

# Build filters
filters = {
    'statuses': user.get('status', []),
    'interests': user.get('hobbies', [])
}

# Get filtered coupons
all_filtered = list(Coupon.get_filtered_coupons(filters))
print(f"All filtered coupons: {len(all_filtered)}")

# Test randomization
if len(all_filtered) > 5:
    random_coupons = random.sample(all_filtered, 5)
    print("Randomly selected 5 coupons")
else:
    random_coupons = all_filtered
    print("Using all available coupons")

print(f"Final count: {len(random_coupons)}")

# Show sample
for i, coupon in enumerate(random_coupons[:3]):
    print(f"{i+1}. {coupon.get('title', 'No title')}") 