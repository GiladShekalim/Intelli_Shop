# URL patterns that map URLs to view functions within the IntelliShop app
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),  # Root route to index
    path('home/', views.index_home, name='index_home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('mfa_verification/', views.mfa_verification, name='mfa_verification'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('base/', views.template, name='template'),
    path('coupon_for_aliexpress/', views.aliexpress_coupons, name='aliexpress_coupons'),
    path('club/<str:club_name>/', views.coupon_detail, name='coupon_detail'),
    path('filter_search/', views.filter_search, name='filter_search'),
    path('profile/', views.profile_view, name='profile'),
    path('logout/', views.logout_view, name='logout'),
    path('coupon/<str:code>/', views.coupon_code_view, name='coupon_code'),
    path('favorites/', views.favorites_view, name='favorites'),
    path('show_all_discounts/', views.show_all_discounts, name='show_all_discounts'),
    path('filtered_discounts/', views.filtered_discounts, name='filtered_discounts'),
    path('search_discounts/', views.search_discounts_by_text, name='search_discounts_by_text'),
    path('ai_filter_helper/', views.ai_filter_helper, name='ai_filter_helper'),
    path('add_favorite/', views.add_favorite_view, name='add_favorite'),
    path('remove_favorite/', views.remove_favorite_view, name='remove_favorite'),
    path('check_favorite/<str:discount_id>/', views.check_favorite_view, name='check_favorite'),
    path('api/club_names/', views.get_club_names, name='get_club_names'),
    path('debug_favorites/', views.debug_favorites, name='debug_favorites'),
    path('debug_page/', views.debug_favorites_page, name='debug_favorites_page'),
] 

