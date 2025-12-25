from django.db import models
from django.contrib.auth.models import AbstractUser

import user

# Use Django's AbstractUser so authentication and user fields behave correctly
class User(AbstractUser):
    POSITION_CHOICES = [
        ('admin', 'Admin'),
        ('owner', 'Owner'),
        ('worker', 'Worker'),
    ]

    # Keep email unique for this project
    email = models.EmailField(unique=True)

    # Additional field for role/position
    position = models.CharField(
        max_length=50,
        choices=POSITION_CHOICES,
        blank=True,
    )

    # Override last_login to allow NULL (not required)
    last_login = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    class Meta:
        db_table = 'account'  # reuse previous table name to ease migration

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'category'
        verbose_name_plural = 'Categories'
    
    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock = models.IntegerField(default=0)
    min_stock = models.IntegerField(default=10)
    sku = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    stock_level = models.CharField(max_length=50, blank=True, choices=[
        ('In Stock', 'In Stock'),   
        ('Low Stock', 'Low Stock'),
        ('Out of Stock', 'Out of Stock'),  
    ], default='In Stock')

    class Meta:
        db_table = 'product'

    def __str__(self):
        return self.name


class Sales(models.Model):
    sales_id = models.AutoField(primary_key=True)
    
    PAYMENT_CHOICES = [
        ('cash', 'Cash'),
        ('mtn', 'MTN Mobile Money'),
        ('airtel', 'AirtelTigo Money'),
        ('vodafone', 'Vodafone Cash'),
        ('card', 'Card'),
    ]

    RECEIPT_CHOICES = [
        ('none', 'No Receipt'),
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp'),
        ('email', 'Email'),
        ('print', 'Print PDF'),
    ]
    
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cash')
    receipt_method = models.CharField(max_length=20, choices=RECEIPT_CHOICES, default='none')
    sale_date = models.DateTimeField(auto_now_add=True)
    cashier = models.ForeignKey(User, on_delete=models.PROTECT, blank=True, null=True, default=None)
   

    class Meta:
        db_table = 'sales'
        verbose_name_plural = 'Sales'

    @property
    def subtotal(self):
        return self.total_amount

    @property
    def tax(self):
        return 0.00

    @property
    def discount(self):
        return 0.00

    @property
    def total(self):
        return self.total_amount

    @property
    def change(self):
        if self.amount_paid:
            return max(0, float(self.amount_paid) - float(self.total_amount))
        return 0.00
    
    @property
    def cashier_name(self):
        return self.cashier.get_full_name() if self.cashier and self.cashier.get_full_name() else (self.cashier.username if self.cashier else "Unknown")

    
    

    def __str__(self):
        return f"Sale #{self.sales_id} - GH₵{self.total_amount}"
class SaleItem(models.Model):
    sale = models.ForeignKey(Sales, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'sale_item'

    @property
    def total_price(self):
        return self.quantity * self.unit_price
    
    @property
    def product_name(self):
        return self.product.name

    def __str__(self):
        return f"{self.quantity} × {self.product.name}"


class Receipt(models.Model):
    sale = models.OneToOneField(Sales, on_delete=models.CASCADE)
    receipt_number = models.CharField(max_length=50, unique=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    
    


    class Meta:
        db_table = 'receipt'


    
    def __str__(self):
        return f"Receipt {self.receipt_number} for Sale {self.sale.sales_id}"
    
    def save(self, *args, **kwargs):
        if not self.receipt_number:
            self.receipt_number = f"REC-{self.sale.sales_id:06d}"
        super().save(*args, **kwargs)