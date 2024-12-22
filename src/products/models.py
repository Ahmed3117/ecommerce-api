import random
import string
from accounts.models import User
from django.db import models

GOVERNMENT_CHOICES = [
    ('1', 'Cairo'),
    ('2', 'Alex'),
    ('3', 'Kafrelshaikh'),
]

PILL_STATUS_CHOICES = [
    ('d', 'Delivered'),
    ('u', 'Under Delivery'),
    ('w', 'Waiting'),
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

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

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
        last_product_discount = self.discount_set.last()
        if last_product_discount:
            return self.price - ((last_product_discount.discount / 100) * self.price)
        return self.price

    def price_after_category_discount(self):
        last_category_discount = self.category.discount_set.last()
        if last_category_discount:
            return self.price - ((last_category_discount.discount / 100) * self.price)
        return self.price

    def has_discount(self):
        return self.price_after_product_discount() != self.price

    def main_image(self):
        images = self.productimage_set.all()
        if images.exists():
            return random.choice(images)
        return None

    def images(self):
        return self.productimage_set.all()

    def number_of_ratings(self):
        return self.rating_set.count()

    def average_rating(self):
        ratings = self.rating_set.all()
        if ratings.exists():
            return round(sum(rating.star_number for rating in ratings) / ratings.count(), 1)
        return 0.0

    def total_quantity(self):
        return sum(availability.quantity for availability in self.productavailability_set.all())

    def available_colors(self):
        return [availability.color.name for availability in self.productavailability_set.all()]

    def available_sizes(self):
        return [availability.size for availability in self.productavailability_set.all()]

    def __str__(self):
        return self.name

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.FileField(upload_to='products/')

    def __str__(self):
        return self.image.name

class ProductInfo(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='info')
    num_of_sales = models.IntegerField(default=0)
    rate = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.product.name} - Info"

class Color(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class ProductAvailability(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='availabilities')
    size = models.CharField(choices=SIZES_CHOICES, max_length=50, default='s')
    color = models.ForeignKey(Color, on_delete=models.CASCADE, related_name='availabilities')
    quantity = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.product.name} - {self.size} - {self.color.name} - {self.quantity}"

class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='ratings')
    star_number = models.FloatField(default=5.0)
    review = models.CharField(max_length=300, default="No review comment")
    date_added = models.DateField(auto_now_add=True)

    def star_ranges(self):
        return range(int(self.star_number)), range(5 - int(self.star_number))

    def __str__(self):
        return f"{self.product.name} - {self.user.username}"

class Shipping(models.Model):
    government = models.CharField(choices=GOVERNMENT_CHOICES, max_length=2)
    shipping_price = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.get_government_display()} - {self.shipping_price}"

class Pill(models.Model):
    items = models.ManyToManyField(Product, related_name='pills')
    pill_discount = models.FloatField(default=0.0)
    pill_coupon_discount = models.FloatField(default=0.0)
    status = models.CharField(choices=PILL_STATUS_CHOICES, max_length=1, default='w')
    date_added = models.DateTimeField(auto_now_add=True)
    paid = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'Bills'

    def __str__(self):
        return f"{self.pilladdress.name} - {self.get_status_display()} - {self.date_added}"

    def get_pill_price(self):
        pill_price = sum(item.price for item in self.items.all())
        pill_price_after_discount = pill_price - (self.pill_discount / 100) * pill_price
        shipping_price = Shipping.objects.get(government=self.pilladdress.government).shipping_price
        pill_price_after_discount_and_shipping = pill_price_after_discount + shipping_price
        pill_price_after_discount_and_shipping_and_coupon = pill_price_after_discount - (self.pill_coupon_discount / 100) * pill_price + shipping_price

        return (
            pill_price,
            pill_price_after_discount,
            pill_price_after_discount_and_shipping,
            pill_price_after_discount_and_shipping_and_coupon,
            shipping_price
        )

    def pill_price(self):
        return self.get_pill_price()[0]

    def pill_price_after_discount(self):
        return self.get_pill_price()[1]

    def pill_price_after_discount_and_shipping(self):
        return self.get_pill_price()[2]

    def pill_price_after_discount_and_shipping_and_coupon(self):
        return self.get_pill_price()[3]

    def shipping_price(self):
        return self.get_pill_price()[4]

class Discount(models.Model):
    discount = models.FloatField(null=True, blank=True)
    discount_start = models.DateTimeField()
    discount_end = models.DateTimeField()
    comment = models.CharField(max_length=150, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True, related_name='discounts')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True, related_name='discounts')

    class Meta:
        verbose_name_plural = 'Offers'

    def __str__(self):
        return f"{self.category.name if self.category else self.product.name} - {self.discount}%"

class CouponDiscount(models.Model):
    coupon = models.CharField(max_length=100, blank=True, null=True, editable=False)
    discount_value = models.FloatField(null=True, blank=True)
    coupon_start = models.DateTimeField(null=True, blank=True)
    coupon_end = models.DateTimeField(null=True, blank=True)

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

    def __str__(self):
        return f"{self.name} - {self.address}"

def create_random_coupon():
    letters = string.ascii_lowercase
    nums = ['0', '2', '3', '4', '5', '6', '7', '8', '9']
    marks = ['@', '#', '$', '%', '&', '*']
    return '-'.join(random.choice(letters) + random.choice(nums) + random.choice(marks) for _ in range(5))

