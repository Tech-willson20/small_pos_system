from datetime import datetime, timedelta, date
from django.core.paginator import Paginator
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from user.models import User, Category, Product, Sales, SaleItem, Receipt, ActivityLog


# Create your views here.

def home(request):
    return render(request, 'home.html')

def signup(request):
    if request.method == "POST":
        # Capture all form fields from template
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip()
        position = request.POST.get("position", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")
        username = request.POST.get("username", "").strip()
        terms = request.POST.get("terms", "")
        
        # Debug: Print all received data
        print("=" * 50)
        print("FORM DATA RECEIVED:")
        print(f"First Name: {first_name}")
        print(f"Last Name: {last_name}")
        print(f"Email: {email}")
        print(f"Position: {position}")
        print(f"Username: {username}")
        print(f"Password: {'*' * len(password) if password else 'EMPTY'}")
        print(f"Confirm Password: {'*' * len(confirm_password) if confirm_password else 'EMPTY'}")
        print(f"Terms Accepted: {terms}")
        print("=" * 50)

        # Validation: Terms checkbox
        if not terms:
            messages.error(request, "You must agree to the Terms and Conditions.")
            return redirect("signup")

        # Validation: Password match
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("signup")

        # Validation: Password strength (minimum 8 characters)
        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return redirect("signup")

        # Validation: Email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, "An account with this email already exists.")
            return redirect("signup")
        
        # Validation: Username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "This username is already taken.")
            return redirect("signup")

        try:
            # Create account using create_user for proper AbstractUser handling
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                position=position
            )
            user.save()

            messages.success(request, "Account created successfully! Please log in.")
            return redirect("login")
            
        except Exception as e:
            print(f"Error creating account: {e}")
            messages.error(request, "An error occurred while creating your account. Please try again.")
            return redirect("signup")

    return render(request, "signup.html")
from django.contrib.auth import authenticate, login, logout

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        # Authenticate the user
        user = authenticate(request, username=username, password=password)

        if user is None:
            messages.error(request, "Invalid username or password.")
            return redirect("login")

        # Log the user in base on role
        login(request, user)

        messages.success(request, f"Welcome back, {user.first_name}!")
        if user.position == 'worker':
            return redirect("user_dashboard")
        else:
            return redirect("dashboard")

    return render(request, "login.html")



def forgot_password_view(request):
    if request.method == 'POST':
        # Handle password reset logic here
        pass
    return render(request, 'forgot_password.html')

@login_required
def dashboard_view(request):
    #account info
    user=request.user
    products_list = Product.objects.count()
    total_categories = Category.objects.count()
    low_stock_count = Product.objects.filter(stock_level='Low Stock').count()
    today_sales = Sales.objects.filter(sale_date__date=date.today())
    receipt = Receipt.objects.select_related('sale').prefetch_related('sale__items__product').order_by('-issued_at')[:3]
    receipts = Receipt.objects.select_related('sale').order_by('-issued_at')[:3]
    receipt_count = Receipt.objects.count()

    
    #give me the total sales amount for today
    today = date.today()
    today_sales = Sales.objects.filter(sale_date__date=today)
    total_sales_amount = sum(sale.total_amount for sale in today_sales)


    

    context={
        'total_products':products_list,
        'total_categories':total_categories,
        'low_stock_count': low_stock_count,
        'total_sales_amount': total_sales_amount,
        'today_sales_count': today_sales.count(),
        'user':user,
        'Receipt_count': receipt_count,
        'receipt': receipt,
        'receipts': receipts,

    }
    return render(request, 'dashboard.html',context)


@login_required
def user_dashboard(request):
    #account info
    user=request.user
    products_list = Product.objects.count()
    total_categories = Category.objects.count()
    low_stock_count = Product.objects.filter(stock_level='Low Stock').count()
    today_sales = Sales.objects.filter(sale_date__date=date.today())
    receipt = Receipt.objects.filter(sale__cashier=user).select_related('sale').prefetch_related('sale__items__product').order_by('-issued_at')[:3]
    receipts = Receipt.objects.filter(sale__cashier=user).select_related('sale').order_by('-issued_at')[:5]
    receipt_count = Receipt.objects.filter(sale__cashier=user).count()

    
    #give me the total sales amount for today by only user
    today = date.today()
    today_sales = Sales.objects.filter(sale_date__date=today, cashier=user)
    total_sales_amount = sum(sale.total_amount for sale in today_sales)
    

    context={
        'total_products':products_list,
        'total_categories':total_categories,
        'low_stock_count': low_stock_count,
        'total_sales_amount': total_sales_amount,
        'today_sales_count': today_sales.count(),
        'user':user,
        'Receipt_count': receipt_count,
        'receipt': receipt,
        'receipts': receipts,

    }
    return render(request, 'user_dashboard.html',context)

@login_required
def transactions(request):
    """View to display all transactions/sales"""
    # Get all receipts ordered by most recent first
    receipts = Receipt.objects.select_related('sale').prefetch_related(
        'sale__items__product'
    ).order_by('-issued_at')
    
    # Add pagination (15 items per page)
    paginator = Paginator(receipts, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate total sales amount for current page
    total_amount = sum(receipt.sale.total_amount for receipt in page_obj)
    
    context = {
        'page_obj': page_obj,
        'receipts': page_obj,
        'total_transactions': receipts.count(),
        'total_amount': total_amount,
    }
    
    return render(request, 'transactions.html', context)



from django.shortcuts import render
from django.db.models import Q
from .models import Sales, Product
from django.http import JsonResponse

def sales_view(request):
    """Display sales page with product search"""
    search_query = request.GET.get('search', '')
    
    # Fetch all products for the POS interface
    if search_query:
        products = Product.objects.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        ).order_by('name')
    else:
        products = Product.objects.all().order_by('name')
    
    context = {
        'products': products,
        'search_query': search_query,
    }
    return render(request, 'sales.html', context)


def search_products_api(request):
    """API endpoint for real-time product search"""
    search_query = request.GET.get('q', '')
    
    if search_query:
        products = Product.objects.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        ).values('id', 'name', 'price', 'stock')[:10]  # Limit to 10 results
    else:
        products = Product.objects.all().values('id', 'name', 'price', 'stock')[:20]
    
    return JsonResponse({
        'products': list(products)
    })
def inventory_view(request):
    """Display all products in inventory"""
    search_query = request.GET.get('search', '')
    products_list = Product.objects.all().order_by('name')
    total_categories = Category.objects.count()
    
    # Update stock levels for all products before displaying
    for product in products_list:
        if product.stock == 0:
            product.stock_level = 'Out of Stock'
        elif product.stock < product.min_stock:
            product.stock_level = 'Low Stock'
        else:
            product.stock_level = 'In Stock'
        product.save()
    
    # Calculate total value
    total_value = sum(product.price * product.stock for product in products_list)

    # Low stock products count
    low_stock_count = Product.objects.filter(stock_level='Low Stock').count()    

    # Search functionality
    if search_query:
        products_list = products_list.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )
    
    # Get category names for each product
    for product in products_list:
        product.category_name = product.category.name if product.category else 'No Category'
    
    context = {
        'products': products_list,
        'search_query': search_query,
        'total_products': Product.objects.count(),
        'total_categories': total_categories,
        'total_value': total_value,
        'low_stock_count': low_stock_count,
        
    }
    
    return render(request, 'inventory.html', context)



def restock_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        try:
            additional_stock = int(request.POST.get('additional_stock', 0))
            if additional_stock < 0:
                messages.error(request, 'Invalid stock quantity.')
                return redirect('inventory')
            
            old_stock = product.stock
            product.stock += additional_stock
            
            # Update stock level
            if product.stock == 0:
                product.stock_level = 'Out of Stock'
            elif product.stock < product.min_stock:
                product.stock_level = 'Low Stock'
            else:
                product.stock_level = 'In Stock'
            
            product.save()
            
            # Log the activity
            ActivityLog.objects.create(
                user=request.user,
                action='stock_update',
                description=f'Restocked product "{product.name}". Old Stock: {old_stock}, New Stock: {product.stock}, Added: {additional_stock}',
                related_object=f'Product ID: {product.id}'
            )
            
            messages.success(request, f'Product "{product.name}" restocked successfully!')
            return redirect('inventory')
        except ValueError:
            messages.error(request, 'Please enter a valid number for stock.')
            return redirect('inventory')
    
    context = {
        'product': product,
    }
    return render(request, 'product/restock_product.html', context)




from django.shortcuts import render
from django.db.models import Sum, Count, F
from django.db.models.functions import TruncMonth

from decimal import Decimal
from .models import Sales, SaleItem, Product, Category

def reports_view(request):
    # Get date filters from request
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    
    # Base queryset
    sales_qs = Sales.objects.all()
    
    # Apply date filters if provided
    if from_date:
        sales_qs = sales_qs.filter(sale_date__gte=from_date)
    if to_date:
        # Include the entire end date
        to_date_obj = datetime.strptime(to_date, '%Y-%m-%d')
        to_date_end = to_date_obj + timedelta(days=1)
        sales_qs = sales_qs.filter(sale_date__lt=to_date_end)
    
    # Summary Statistics
    total_sales = sales_qs.aggregate(
        total=Sum('total_amount')
    )['total'] or Decimal('0.00')
    
    total_transactions = sales_qs.count()
    
    # Top Selling Products (based on quantity sold)
    top_products = SaleItem.objects.filter(
        sale__in=sales_qs
    ).values(
        'product__name'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('unit_price'))
    ).order_by('-total_quantity')[:5]
    
    # Get top product name
    top_product_name = top_products[0]['product__name'] if top_products else 'N/A'
    
    # Category Breakdown
    category_data = SaleItem.objects.filter(
        sale__in=sales_qs
    ).values(
        'product__category__name'
    ).annotate(
        total_quantity=Sum('quantity')
    ).order_by('-total_quantity')
    
    category_labels = [item['product__category__name'] for item in category_data]
    category_values = [item['total_quantity'] for item in category_data]
    
    # Monthly Sales (last 6 months)
    six_months_ago = datetime.now() - timedelta(days=180)
    monthly_sales = Sales.objects.filter(
        sale_date__gte=six_months_ago
    ).annotate(
        month=TruncMonth('sale_date')
    ).values('month').annotate(
        total=Sum('total_amount')
    ).order_by('month')
    
    # Prepare monthly data for chart
    month_labels = []
    month_values = []
    for item in monthly_sales:
        month_labels.append(item['month'].strftime('%b'))
        month_values.append(float(item['total']))
    
    # Recent Transactions - Filter sales that have receipts
    recent_sales_with_receipts = Sales.objects.filter(
        receipt__isnull=False,
        sale_date__in=sales_qs.values_list('sale_date', flat=True) if from_date or to_date else Sales.objects.all().values_list('sale_date', flat=True)
    ).select_related('receipt').prefetch_related('items').order_by('-sale_date')[:10]

    receipt_count = Receipt.objects.count()
    
    # Prepare transaction data
    transactions_data = []
    for sale in recent_sales_with_receipts:
        transactions_data.append({
            'receipt_no': sale.receipt.receipt_number,
            'date': sale.sale_date.strftime('%Y-%m-%d'),
            'items_count': sale.items.count(),
            'total': sale.total_amount,
            'staff': 'N/A'  # Add staff field to Sales model if needed
        })
    
    context = {
        'total_sales': total_sales,
        'total_transactions': total_transactions,
        'top_product_name': top_product_name,
        'top_products': top_products,
        'category_labels': category_labels,
        'category_values': category_values,
        'month_labels': month_labels,
        'month_values': month_values,
        'transactions': transactions_data,
        'from_date': from_date or '',
        'to_date': to_date or '',
        'receipt_count': receipt_count,
    }
    
    return render(request, 'report.html', context)
def user_list(request):
    users = User.objects.all()

    return render(request, 'user_list2.html', {'users': users})
def settings_view(request):
    return render(request, 'settings.html')

import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Product, Sales, SaleItem, Receipt


def sales_view(request):
    """Display the new sale page with all products"""
    products = Product.objects.all().order_by('name')
    
    # Create a new sale object to get the ID for the form action
    sale = Sales.objects.create(total_amount=0.00)
    
    context = {
        'products': products,
        'sale': sale,
    }
    return render(request, 'sales.html', context)


def sales(request):
    """Process cart checkout and create sale record"""
    if request.method == 'POST':
        try:
            cart_data = json.loads(request.POST.get('cart_data', '[]'))
            print("Cart Data:", cart_data)
            
            if not cart_data:
                messages.error(request, 'Cart is empty!')
                return redirect('new_sale')
            
            # Calculate total amount
            total_amount = sum(float(item['price']) * int(item['quantity']) for item in cart_data)
            payment_method = request.POST.get('payment_method', 'cash')
            amount_paid = request.POST.get('amount_paid')
            receipt_method = request.POST.get('receipt_method', 'none')
            
            # Convert amount_paid to float if provided
            if amount_paid:
                try:
                    amount_paid = float(amount_paid)
                except (ValueError, TypeError):
                    amount_paid = None
            
            # Get the sale_id from the form (created when page loaded)
            sale_id = request.POST.get('sale_id')
            if sale_id:
                # Update existing sale
                sale = Sales.objects.get(sales_id=sale_id)
                sale.total_amount = total_amount
                sale.payment_method = payment_method
                sale.amount_paid = amount_paid
                sale.receipt_method = receipt_method
                sale.cashier = request.user
                sale.save()
            else:
                # Create new sale
                sale = Sales.objects.create(
                    total_amount=total_amount,
                    payment_method=payment_method,
                    amount_paid=amount_paid,
                    receipt_method=receipt_method,
                    cashier=request.user
                )
            
            # Process each item in cart
            for item in cart_data:
                product = Product.objects.get(id=item['id'])
                quantity_ordered = int(item['quantity'])
                
                if product.stock >= quantity_ordered:
                    # Deduct from stock
                    product.stock -= quantity_ordered
                    
                    # Update stock level
                    if product.stock == 0:
                        product.stock_level = 'Out of Stock'
                    elif product.stock < product.min_stock:
                        product.stock_level = 'Low Stock'
                    else:
                        product.stock_level = 'In Stock'
                    
                    product.save()
                    
                    # Create SaleItem record with unit_price field
                    SaleItem.objects.create(
                        sale=sale,
                        product=product,
                        quantity=quantity_ordered,
                        unit_price=float(item['price'])
                    )
                else:
                    # Insufficient stock - delete the sale and show error
                    sale.delete()
                    messages.error(request, f'Insufficient stock for {product.name}. Available: {product.stock}, Requested: {quantity_ordered}')
                    return redirect('new_sale')
            
            # Create receipt
            Receipt.objects.get_or_create(sale=sale)
            
            messages.success(request, f'Sale #{sale.sales_id} completed successfully!')
            return redirect('checkout', sale_id=sale.sales_id)
            
        except Product.DoesNotExist:
            messages.error(request, 'One or more products not found!')
            return redirect('new_sale')
        except Exception as e:
            messages.error(request, f'Error processing sale: {str(e)}')
            return redirect('new_sale')
    
    return redirect('new_sale')


def checkout(request, sale_id=None):
    """Display receipt for completed sale"""
    if sale_id:
        sale = get_object_or_404(Sales, sales_id=sale_id)
    else:
        # Get the most recent sale
        sale = Sales.objects.latest('sale_date') if Sales.objects.exists() else None
    
    if not sale:
        messages.error(request, 'No sale found!')
        return redirect('new_sale')
    
    # Get or create receipt
    receipt, created = Receipt.objects.get_or_create(sale=sale)
    
    # Get cashier info (you can customize this based on your auth system)
    cashier_name = 'POS Operator'
    if hasattr(request, 'user') and request.user.is_authenticated:
        try:
            user = User.objects.get(username=request.user.username)
            cashier_name = f"{user.first_name} {user.last_name}"
        except User.DoesNotExist:
            pass
    
    context = {
        'sale': sale,
        'receipt': receipt,
        'business_name': 'A $ E POS',
        'users': {'first_name': cashier_name.split()[0] if cashier_name else 'POS'},
    }
    return render(request, 'checkout.html', context)

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("login")


def profile_view(request):
    return render(request, 'user/profile.html')
def settings_view(request):
    return render(request, 'user/settings.html')



def categories(request):
    """Display all categories"""
    search_query = request.GET.get('search', '')
    
    categories_list = Category.objects.all().order_by('name')
    
    # Search functionality
    if search_query:
        categories_list = categories_list.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    # Get product count for each category
    for category in categories_list:
        category.product_count = Product.objects.filter(category=category).count()
    
    context = {
        'categories': categories_list,
        'search_query': search_query,
        'total_categories': Category.objects.count(),
    }
    
    return render(request, 'category/categories.html', context)



def add_product(request):
    """Add new product to inventory"""
    if request.method == 'POST':
        # Get form data
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        description = request.POST.get('description', '')
        price = request.POST.get('price')
        cost_price = request.POST.get('cost_price', None)
        stock = request.POST.get('stock')
        min_stock = request.POST.get('min_stock', 10)
        sku = request.POST.get('sku', '')
        
        # Validation
        if not name or not category_id or not price or not stock:
            messages.error(request, 'Please fill in all required fields.')
            categories = Category.objects.all()
            return render(request, 'add_product.html', {'categories': categories})
        
        try:
            # Check if SKU already exists
            if sku and Product.objects.filter(sku=sku).exists():
                messages.error(request, 'A product with this SKU already exists.')
                categories = Category.objects.all()
                return render(request, 'add_product.html', {'categories': categories})
            
            # Create product
            category = Category.objects.get(id=category_id)
            product = Product.objects.create(
                name=name,
                category=category,
                description=description,
                price=price,
                cost_price=cost_price if cost_price else None,
                stock=stock,
                min_stock=min_stock,
                sku=sku,
            )
            
            messages.success(request, f'Product "{product.name}" added successfully!')
            return redirect('inventory')
            
        except Category.DoesNotExist:
            messages.error(request, 'Selected category does not exist.')
        except Exception as e:
            messages.error(request, f'Error creating product: {str(e)}')

    
    categories = Category.objects.all()
    context = {
        'categories': categories,
    }
    return render(request, 'product/add_product.html', context)



def edit_product(request, product_id):
    """Edit existing product"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        # Get form data
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        description = request.POST.get('description', '')
        price = request.POST.get('price')
        cost_price = request.POST.get('cost_price', None)
        stock = request.POST.get('stock')
        min_stock = request.POST.get('min_stock', 10)
        sku = request.POST.get('sku', '')
        
        # Validation
        if not name or not category_id or not price or not stock:
            messages.error(request, 'Please fill in all required fields.')
            categories = Category.objects.all()
            return render(request, 'edit_product.html', {
                'product': product,
                'categories': categories
            })
        
        try:
            # Check if SKU already exists for other products
            if sku and Product.objects.filter(sku=sku).exclude(id=product_id).exists():
                messages.error(request, 'A product with this SKU already exists.')
                categories = Category.objects.all()
                return render(request, 'edit_product.html', {
                    'product': product,
                    'categories': categories
                })
            
            # Store old values for logging
            old_values = {
                'name': product.name,
                'category': product.category.name if product.category else '',
                'price': str(product.price),
                'stock': product.stock,
                'min_stock': product.min_stock,
                'sku': product.sku,
            }
            
            # Update product
            category = Category.objects.get(id=category_id)
            product.name = name
            product.category = category
            product.description = description
            product.price = price
            product.cost_price = cost_price if cost_price else None
            product.stock = stock
            product.min_stock = min_stock
            product.sku = sku
            product.save()
            
            # Build change log
            changes = []
            if old_values['name'] != name:
                changes.append(f"Name: {old_values['name']} → {name}")
            if old_values['category'] != category.name:
                changes.append(f"Category: {old_values['category']} → {category.name}")
            if old_values['price'] != str(price):
                changes.append(f"Price: GH₵{old_values['price']} → GH₵{price}")
            if old_values['stock'] != int(stock):
                changes.append(f"Stock: {old_values['stock']} → {stock}")
            if old_values['min_stock'] != int(min_stock):
                changes.append(f"Min Stock: {old_values['min_stock']} → {min_stock}")
            if old_values['sku'] != sku:
                changes.append(f"SKU: {old_values['sku']} → {sku}")
            
            # Log the activity
            ActivityLog.objects.create(
                user=request.user,
                action='product_update',
                description=f'Edited product "{product.name}". Changes: {", ".join(changes) if changes else "No changes"}',
                related_object=f'Product ID: {product.id}'
            )
            
            messages.success(request, f'Product "{product.name}" updated successfully!')
            return redirect('inventory')
            
        except Category.DoesNotExist:
            messages.error(request, 'Selected category does not exist.')
        except Exception as e:
            messages.error(request, f'Error updating product: {str(e)}')
    
    categories = Category.objects.all()
    context = {
        'product': product,
        'categories': categories,
    }
    return render(request, 'product/edit_product.html', context)



def delete_product(request, product_id):
    """Delete product from inventory"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Product "{product_name}" deleted successfully!')
        return redirect('inventory')
    
    return render(request, 'product/confirm_delete.html', {'product': product, 'type': 'product'})




def add_category(request):
    """Add new category"""
    if request.method == 'POST':
        # Get form data
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        
        # Validation
        if not name:
            messages.error(request, 'Category name is required.')
            return render(request, 'add_category.html')
        
        # Check if category name already exists
        if Category.objects.filter(name__iexact=name).exists():
            messages.error(request, 'A category with this name already exists.')
            return render(request, 'add_category.html')
        
        try:
            # Create category
            category = Category.objects.create(
                name=name,
                description=description
            )
            
            messages.success(request, f'Category "{category.name}" added successfully!')
            return redirect('categories')
            
        except Exception as e:
            messages.error(request, f'Error creating category: {str(e)}')
    return render(request, 'category/add_category.html')


def edit_category(request, category_id):
    """View to edit an existing category"""
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        
        # Validation
        if not name:
            messages.error(request, 'Category name is required!')
            return redirect('edit_category', category_id=category_id)
        
        # Check if another category with same name exists
        if Category.objects.filter(name__iexact=name).exclude(id=category_id).exists():
            messages.error(request, f'Category "{name}" already exists!')
            return redirect('edit_category', category_id=category_id)
        
        # Update category
        try:
            category.name = name
            category.description = description
            category.save()
            messages.success(request, f'Category "{name}" updated successfully!')
            return redirect('category')
        except Exception as e:
            messages.error(request, f'Error updating category: {str(e)}')
            return redirect('edit_category', category_id=category_id)
    
    context = {
        'category': category,
    }
    return render(request, 'category/edit_category.html', context)


def delete_category(request, category_id):
    """View to delete a category"""
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        # Check if category has products
        product_count = Product.objects.filter(category=category).count()
        
        if product_count > 0:
            messages.error(
                request, 
                f'Cannot delete category "{category.name}". It has {product_count} product(s). '
                'Please move or delete products first.'
            )
            return redirect('category')
        
        # Delete category
        try:
            category_name = category.name
            category.delete()
            messages.success(request, f'Category "{category_name}" deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting category: {str(e)}')
        
        return redirect('category')
    
    # If GET request, show confirmation page (optional)
    context = {
        'category': category,
        'product_count': Product.objects.filter(category=category).count(),
    }
    return render(request, 'category/delete_category_confirm.html', context)


def view_category_products(request, category_id):
    """View to display all products in a specific category"""
    category = get_object_or_404(Category, id=category_id)
    
    # Get all products in this category
    products = Product.objects.filter(category=category).order_by('-created_at')
    
    # Optional: Add search functionality for products
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(sku__icontains=search_query)
        )
    
    context = {
        'category': category,
        'products': products,
        'product_count': products.count(),
        'search_query': search_query,
    }
    
    return render(request, 'category/category_products.html', context)




#LOGS
def activity_log(request):
    """View to display activity logs"""
    from django.db import models
    
    # Check if user wants to view all logs
    view_all = request.GET.get('view_all', 'false') == 'true'
    
    # Fetch activity logs ordered by most recent first
    all_activity_logs = ActivityLog.objects.all().order_by('-timestamp')
    
    # Filter functionality
    action_filter = request.GET.get('action', '')
    user_filter = request.GET.get('user', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    search_query = request.GET.get('search', '')
    
    # Apply filters
    if action_filter:
        all_activity_logs = all_activity_logs.filter(action=action_filter)
    
    if user_filter:
        all_activity_logs = all_activity_logs.filter(user__id=user_filter)
    
    if date_from:
        all_activity_logs = all_activity_logs.filter(timestamp__date__gte=date_from)
    
    if date_to:
        all_activity_logs = all_activity_logs.filter(timestamp__date__lte=date_to)
    
    if search_query:
        all_activity_logs = all_activity_logs.filter(
            models.Q(description__icontains=search_query) |
            models.Q(user__username__icontains=search_query) |
            models.Q(related_object__icontains=search_query)
        )
    
    # Determine if showing all or recent 5
    if view_all:
        # Show all with pagination (20 items per page)
        paginator = Paginator(all_activity_logs, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        activity_logs = page_obj
        is_view_all = True
    else:
        # Show only recent 5
        activity_logs = all_activity_logs[:5]
        page_obj = None
        is_view_all = False
    
    # Get all users for filter dropdown
    all_users = User.objects.all().order_by('username')
    
    # Get all action types for filter dropdown
    action_choices = ActivityLog.ACTION_CHOICES
    
    # Calculate stats
    from django.utils import timezone
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    
    stats = {
        'total_activities': ActivityLog.objects.count(),
        'today_activities': ActivityLog.objects.filter(timestamp__date=today).count(),
        'this_week_activities': ActivityLog.objects.filter(timestamp__date__gte=week_ago).count(),
    }
    
    context = {
        'page_obj': page_obj if is_view_all else None,
        'activity_logs': activity_logs,
        'total_activities': all_activity_logs.count(),
        'all_users': all_users,
        'action_choices': action_choices,
        'action_filter': action_filter,
        'user_filter': user_filter,
        'date_from': date_from,
        'date_to': date_to,
        'search_query': search_query,
        'is_view_all': is_view_all,
        'stats': stats,
    }
    return render(request, 'activity_log.html', context)