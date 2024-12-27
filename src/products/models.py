import random
import string
from accounts.models import User
from django.db import models
from django.utils import timezone

from core import settings

GOVERNMENT_CHOICES = [
    ('1', 'Cairo'),
    ('2', 'Alexandria'),
    ('3', 'Kafr El Sheikh'),
    ('4', 'Dakahlia'),
    ('5', 'Sharqia'),
    ('6', 'Gharbia'),
    ('7', 'Monufia'),
    ('8', 'Qalyubia'),
    ('9', 'Giza'),
    ('10', 'Beni Suef'),
    ('11', 'Fayoum'),
    ('12', 'Minya'),
    ('13', 'Assiut'),
    ('14', 'Sohag'),
    ('15', 'Qena'),
    ('16', 'Luxor'),
    ('17', 'Aswan'),
    ('18', 'Red Sea'),
    ('19', 'Beheira'),
    ('20', 'Ismailia'),
    ('21', 'Suez'),
    ('22', 'Port Said'),
    ('23', 'Damietta'),
    ('24', 'Matruh'),
    ('25', 'New Valley'),
    ('26', 'North Sinai'),
    ('27', 'South Sinai'),
]


PILL_STATUS_CHOICES = [
    ('i', 'initiated'),
    ('w', 'Waiting'),
    ('u', 'Under Delivery'),
    ('d', 'Delivered'),
    ('r', 'Refused'),
    ('c', 'Canceled'),
]

SIZES_CHOICES = [
    ('s', 'S'),
    ('xs', 'XS'),
    ('m', 'M'),
    ('l', 'L'),
    ('xl', 'XL'),
    ('xxl', 'XXL'),
    ('xxxl', 'XXXL'),
    ('xxxxl', 'XXXXL'),
    ('xxxxxl', 'XXXXXL'),
]

PAYMENT_CHOICES = [
    ('c', 'cash'),
    ('v', 'visa'),
]

def generate_pill_number():
    """Generate a unique 20-digit pill number."""
    while True:
        # Generate a random 20-digit string
        pill_number = ''.join(random.choices(string.digits, k=20))
        return pill_number

def create_random_coupon():
    letters = string.ascii_lowercase
    nums = ['0', '2', '3', '4', '5', '6', '7', '8', '9']
    marks = ['@', '#', '$', '%', '&', '*']
    return '-'.join(random.choice(letters) + random.choice(nums) + random.choice(marks) for _ in range(5))


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    image = models.ImageField(upload_to='categories/', null=True, blank=True)

    def __str__(self):
        return self.name

class SubCategory(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')

    def __str__(self):
        return f"{self.category.name} - {self.name}"

class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    logo = models.ImageField(upload_to='brands/', null=True, blank=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True, related_name='products')
    sub_category = models.ForeignKey(SubCategory, on_delete=models.CASCADE, null=True, blank=True, related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, null=True, blank=True, related_name='products')
    price = models.FloatField(null=True, blank=True)
    description = models.TextField(max_length=1000, null=True, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def price_after_product_discount(self):
        last_product_discount = self.discounts.last()
        if last_product_discount:
            return self.price - ((last_product_discount.discount / 100) * self.price)
        return self.price

    def price_after_category_discount(self):
        if self.category:  
            last_category_discount = self.category.discounts.last()
            if last_category_discount:
                return self.price - ((last_category_discount.discount / 100) * self.price)
        return self.price

    # apply the best discount of all discounts (price_after_product_discount OR price_after_category_discount)
    def discounted_price(self):
        return min(self.price_after_product_discount(), self.price_after_category_discount())

    def has_discount(self):
        return self.price_after_product_discount() != self.price

    def main_image(self):
        images = self.images.all()
        if images.exists():
            return random.choice(images)
        return None

    def images(self):
        return self.images.all()

    def number_of_ratings(self):
        return self.ratings.count()

    def average_rating(self):
        ratings = self.ratings.all()
        if ratings.exists():
            return round(sum(rating.star_number for rating in ratings) / ratings.count(), 1)
        return 0.0

    def total_quantity(self):
        return sum(availability.quantity for availability in self.availabilities.all())

    def available_colors(self):
        return [availability.color.name for availability in self.availabilities.all()]

    def available_sizes(self):
        return [availability.size for availability in self.availabilities.all()]

    def __str__(self):
        return self.name

class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='product_images/')

    def __str__(self):
        return f"Image for {self.product.name}"

class ProductInfo(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='info')
    num_of_sales = models.IntegerField(default=0)
    # rate = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.product.name} - Info"

class Color(models.Model):
    name = models.CharField(max_length=50, unique=True)
    degree = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class ProductAvailability(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='availabilities'
    )
    size = models.CharField(max_length=50)
    color = models.ForeignKey(
        Color,
        on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.product.name} - {self.size} - {self.color.name}"


class Rating(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='ratings'
    )
    user = models.ForeignKey(
        User,  # Assuming you have a User model
        on_delete=models.CASCADE
    )
    star_number = models.IntegerField()
    review = models.CharField(max_length=300, default="No review comment")
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.star_number} stars for {self.product.name} by {self.user.username}"


    def star_ranges(self):
        return range(int(self.star_number)), range(5 - int(self.star_number))


class Shipping(models.Model):
    government = models.CharField(choices=GOVERNMENT_CHOICES, max_length=2)
    shipping_price = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.get_government_display()} - {self.shipping_price}"

class PillItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='pill_items')
    quantity = models.PositiveIntegerField(default=1)
    size = models.CharField(max_length=10, choices=SIZES_CHOICES, null=True)
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.product.name} - {self.quantity} - {self.size} - {self.color.name if self.color else 'No Color'}"

class Pill(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='pills')
    items = models.ManyToManyField(PillItem, related_name='pills')  # Updated to relate to PillItem
    status = models.CharField(choices=PILL_STATUS_CHOICES, max_length=1, default='i')
    date_added = models.DateTimeField(auto_now_add=True)
    paid = models.BooleanField(default=False)
    coupon = models.ForeignKey('CouponDiscount', on_delete=models.SET_NULL, null=True, blank=True, related_name='pills')
    coupon_discount = models.FloatField(default=0.0)  # Store the coupon discount as a field
    pill_number = models.CharField(max_length=20, editable=False)

    def save(self, *args, **kwargs):
        if not self.pill_number:
            self.pill_number = generate_pill_number()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = 'Bills'

    def __str__(self):
        return f"Pill ID: {self.id} - Status: {self.get_status_display()} - Date: {self.date_added}"

    # 1. Price without coupons (sum of product.discounted_price() * quantity)
    def price_without_coupons(self):
        return sum(item.product.discounted_price() * item.quantity for item in self.items.all())

    # 2. Calculate coupon discount (dynamically calculate based on the coupon)
    def calculate_coupon_discount(self):
        if self.coupon:
            # Check if the coupon is valid (within start and end dates)
            now = timezone.now()
            if self.coupon.coupon_start <= now <= self.coupon.coupon_end:
                return self.coupon.discount_value
        return 0.0  # No coupon or invalid coupon

    # 3. Price after coupon discount
    def price_after_coupon_discount(self):
        return self.price_without_coupons() - self.coupon_discount

    # 4. Shipping price (based on PillAddress.government)
    def shipping_price(self):
        if hasattr(self, 'pilladdress'):
            shipping = Shipping.objects.get(government=self.pilladdress.government)
            return shipping.shipping_price
        return 0.0  # Default shipping price if PillAddress is not set

    # 5. Final price (price_after_coupon_discount + shipping_price)
    def final_price(self):
        return self.price_after_coupon_discount() + self.shipping_price()

class Discount(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True, related_name='discounts')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True, related_name='discounts')
    discount = models.FloatField()
    discount_start = models.DateTimeField()
    discount_end = models.DateTimeField()

    def __str__(self):
        return f"{self.discount}% discount"

class CouponDiscount(models.Model):
    coupon = models.CharField(max_length=100, blank=True, null=True, editable=False)
    discount_value = models.FloatField(null=True, blank=True)
    coupon_start = models.DateTimeField(null=True, blank=True)
    coupon_end = models.DateTimeField(null=True, blank=True)
    available_use_times = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        if not self.coupon:
            self.coupon = create_random_coupon()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.coupon

class PillAddress(models.Model):
    pill = models.OneToOneField(Pill, on_delete=models.CASCADE, related_name='pilladdress')
    name = models.CharField(max_length=150, null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    government = models.CharField(choices=GOVERNMENT_CHOICES, max_length=2)
    pay_method = models.CharField(choices=PAYMENT_CHOICES, max_length=2 , default="c")
    def __str__(self):
        return f"{self.name} - {self.address}"







