from django.urls import path
from user import views
urlpatterns = [
    path('', views.home, name='home'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.signup, name='signup'),
    path('dashboard/', views.dashboard_view, name='dashboard'),


    path('sales/', views.sales_view, name='sales'),
    path('reports/', views.reports_view, name='reports'),
    path('users/', views.user_list, name='users'),

   path('sales/new/', views.sales_view, name='new_sale'),  # Display products page
    path('sales/checkout/', views.sales, name='checkout'),  # Process checkout
    path('sales/receipt/<int:sale_id>/', views.checkout, name='checkout'),  # Show receipt
    
    path('reports/', views.reports_view, name='reports'),
    path('transactions/', views.transactions, name='transactions'),
    path('users/', views.user_list, name='users'),
    path('settings/', views.settings_view, name='settings'),
    path('inventory/', views.inventory_view, name='inventory'),
    path('profile/', views.profile_view, name='profile'),
    #product
    path('add_product/', views.add_product, name='add_product'),
    path('edit_product/<int:product_id>/', views.edit_product, name='edit_product'),
    path('restock_product/<int:product_id>/', views.restock_product, name='restock_product'),
    path('delete_product/<int:product_id>/', views.delete_product, name='delete_product'),

    #category
    path('add_category/', views.add_category, name='add_category'),
    path('category/',views.categories,name='category'),
     path('categories/edit/<int:category_id>/', views.edit_category, name='edit_category'),
    path('categories/delete/<int:category_id>/', views.delete_category, name='delete_category'),
    path('categories/<int:category_id>/products/', views.view_category_products, name='view_category_products'),

]