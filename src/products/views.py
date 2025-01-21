from django.utils import timezone
from rest_framework import generics, status
from rest_framework import filters as rest_filters  # Rename this import
from django_filters.rest_framework import DjangoFilterBackend
from collections import defaultdict
from products.permissions import IsOwner
from .models import Category, Color, CouponDiscount, PillAddress, ProductAvailability, ProductImage, Rating, Shipping, SubCategory, Brand, Product,Pill
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import *
from .filters import CategoryFilter, CouponDiscountFilter, PillFilter, ProductFilter
from .models import prepare_whatsapp_message


#^ < ==========================customer endpoints========================== >

class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = CategoryFilter 
    

class SubCategoryListView(generics.ListAPIView):
    queryset = SubCategory.objects.all()
    serializer_class = SubCategorySerializer
    filter_backends = [DjangoFilterBackend] 
    filterset_fields = ['category']

class BrandListView(generics.ListAPIView):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    pagination_class = None

class ProductListView(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, rest_filters.SearchFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'category__name', 'brand__name', 'description']


class Last10ProductsListView(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, rest_filters.SearchFilter]
    filterset_class = ProductFilter


class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    lookup_field = 'id'
    
class PillCreateView(generics.CreateAPIView):
    queryset = Pill.objects.all()
    serializer_class = PillCreateSerializer
    permission_classes = [IsAuthenticated]  # Ensure the user is authenticated

    def perform_create(self, serializer):
        # If 'user' is not in the request data, set it to the request.user
        if 'user' not in serializer.validated_data:
            serializer.validated_data['user'] = self.request.user
        serializer.save()

class PillCouponApplyView(generics.UpdateAPIView):
    queryset = Pill.objects.all()
    serializer_class = PillCouponApplySerializer
    lookup_field = 'id'

    def perform_update(self, serializer):
        # Get the coupon instance from the validated data
        coupon = serializer.validated_data.get('coupon')

        # Get the pill instance
        pill = self.get_object()

        # Check if the pill already has a coupon
        if pill.coupon:
            return Response({"error": "This pill already has a coupon applied."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the coupon is valid (within start and end dates)
        if not self.is_coupon_valid(coupon):
            return Response({"error": "Coupon is not valid or expired."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the coupon is available based on available_use_times
        if not self.is_coupon_available(coupon):
            return Response({"error": "Coupon is not available."}, status=status.HTTP_400_BAD_REQUEST)

        # Apply the coupon to the pill
        pill = serializer.save(coupon=coupon)

        # Calculate the coupon discount as a percentage
        coupon_discount_amount = (coupon.discount_value / 100) * pill.price_without_coupons()

        # Update the pill's coupon discount field
        pill.coupon_discount = coupon_discount_amount
        pill.save()

        # Decrement the available_use_times of the coupon
        coupon.available_use_times -= 1
        coupon.save()

        # Return the updated pill data
        return Response(self.get_pill_data(pill), status=status.HTTP_200_OK)

    def is_coupon_valid(self, coupon):
        """
        Check if the coupon is valid based on its start and end dates.
        """
        now = timezone.now()
        return coupon.coupon_start <= now <= coupon.coupon_end

    def is_coupon_available(self, coupon):
        """
        Check if the coupon is available based on available_use_times.
        """
        return coupon.available_use_times > 0

    def get_pill_data(self, pill):
        """
        Return the updated pill data with price calculations.
        """
        return {
            "id": pill.id,
            "coupon": pill.coupon.coupon if pill.coupon else None,
            "price_without_coupons": pill.price_without_coupons(),
            "coupon_discount": pill.coupon_discount,
            "price_after_coupon_discount": pill.price_after_coupon_discount(),
            "final_price": pill.final_price(),
        }

class PillAddressCreateUpdateView(generics.CreateAPIView, generics.UpdateAPIView):
    queryset = PillAddress.objects.all()
    serializer_class = PillAddressCreateSerializer

    def get_object(self):
        """
        Get the PillAddress instance associated with the pill_id.
        """
        pill_id = self.kwargs.get('pill_id')
        try:
            pill = Pill.objects.get(id=pill_id)
            return PillAddress.objects.get(pill=pill)
        except Pill.DoesNotExist:
            return None
        except PillAddress.DoesNotExist:
            return None

    def perform_create(self, serializer):
        pill_id = self.kwargs.get('pill_id')
        try:
            pill = Pill.objects.get(id=pill_id)
            # Save the PillAddress with the associated Pill
            serializer.save(pill=pill)

            # Update the Pill's status to 'w' (waiting)
            pill.status = 'w'
            pill.save()

        except Pill.DoesNotExist:
            return Response({"error": "Pill does not exist."}, status=status.HTTP_404_NOT_FOUND)

    def perform_update(self, serializer):
        pill_id = self.kwargs.get('pill_id')
        try:
            pill = Pill.objects.get(id=pill_id)
            # Update the PillAddress
            serializer.save(pill=pill)

            # Optionally, you can update the Pill's status to 'w' (waiting) if needed
            pill.status = 'w'
            pill.save()

        except Pill.DoesNotExist:
            return Response({"error": "Pill does not exist."}, status=status.HTTP_404_NOT_FOUND)

class PillDetailView(generics.RetrieveAPIView):
    queryset = Pill.objects.all()
    serializer_class = PillDetailSerializer
    lookup_field = 'id'
    
class CustomerRatingListCreateView(generics.ListCreateAPIView):
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Allow users to see only their own ratings
        return Rating.objects.filter(user=self.request.user)

class CustomerRatingDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    
class UserPillsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get the authenticated user
        user = request.user
        # Retrieve all pills for the user
        pills = Pill.objects.filter(user=user)
        # Serialize the data
        serializer = PillDetailSerializer(pills, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class getColors(generics.ListAPIView):
    queryset = Color.objects.all()
    serializer_class = ColorSerializer


class PayRequestListCreateView(generics.ListCreateAPIView):
    queryset = PayRequest.objects.all()
    serializer_class = PayRequestSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  # To handle file uploads
    filter_backends = [DjangoFilterBackend, rest_filters.SearchFilter]
    filterset_fields = ['is_applied', 'pill__pill_number', 'pill__user__name', 'pill__pilladdress__email', 'pill__pilladdress__phone', 'pill__pilladdress__government']
    search_fields = ['pill__pill_number', 'pill__user__name', 'pill__pilladdress__email', 'pill__pilladdress__phone', 'pill__pilladdress__government']

    def perform_create(self, serializer):
        # Ensure the user is the owner of the pill
        pill_id = self.request.data.get('pill')
        try:
            pill = Pill.objects.get(id=pill_id, user=self.request.user)
            # Check if the pill is already paid
            if pill.paid:
                raise serializers.ValidationError("This pill is already paid.")
            serializer.save(pill=pill)
        except Pill.DoesNotExist:
            raise serializers.ValidationError("Pill does not exist or you do not have permission to create a payment request for this pill.")

#^ < ==========================Dashboard endpoints========================== >

class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = CategoryFilter 
    permission_classes = [IsAdminUser] 

class CategoryRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminUser] 

class SubCategoryListCreateView(generics.ListCreateAPIView):
    queryset = SubCategory.objects.all()
    serializer_class = SubCategorySerializer
    filter_backends = [DjangoFilterBackend] 
    filterset_fields = ['category']
    permission_classes = [IsAdminUser] 

class SubCategoryRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SubCategory.objects.all()
    serializer_class = SubCategorySerializer
    permission_classes = [IsAdminUser] 

class BrandListCreateView(generics.ListCreateAPIView):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [IsAdminUser] 

class BrandRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [IsAdminUser] 

class ColorListCreateView(generics.ListCreateAPIView):
    queryset = Color.objects.all()
    serializer_class = ColorSerializer
    permission_classes = [IsAdminUser] 

class ColorRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Color.objects.all()
    serializer_class = ColorSerializer
    permission_classes = [IsAdminUser] 
    lookup_field = 'id'

class ProductListCreateView(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, rest_filters.SearchFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'category__name', 'brand__name', 'description']
    permission_classes = [IsAdminUser] 
class ProductListBreifedView(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductBreifedSerializer
    filter_backends = [DjangoFilterBackend, rest_filters.SearchFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'category__name', 'brand__name', 'description']
    permission_classes = [IsAdminUser] 

class ProductRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminUser] 


class ProductImageListCreateView(generics.ListCreateAPIView):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer
    filterset_fields = ['product']
    permission_classes = [IsAdminUser] 


class ProductImageBulkCreateView(generics.CreateAPIView):
    permission_classes = [IsAdminUser]

    def post(self, request, *args, **kwargs):
        serializer = ProductImageBulkUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product = serializer.validated_data['product']
        images = serializer.validated_data['images']

        # Save each image
        product_images = [
            ProductImage(product=product, image=image)
            for image in images
        ]
        ProductImage.objects.bulk_create(product_images)

        return Response(
            {"message": "Images uploaded successfully."},
            status=status.HTTP_201_CREATED,
        )



class ProductImageDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer
    permission_classes = [IsAdminUser] 

class PillListCreateView(generics.ListCreateAPIView):
    queryset = Pill.objects.all()
    serializer_class = PillCreateSerializer
    filter_backends = [DjangoFilterBackend, rest_filters.SearchFilter]
    filterset_class = PillFilter  
    search_fields = ['pilladdress__phone', 'pilladdress__government', 'pilladdress__name', 'user__name', 'user__username']
    permission_classes = [IsAdminUser]

    def get_serializer_class(self):
        # Use PillCreateSerializer for POST (create) requests
        if self.request.method == 'POST':
            return PillCreateSerializer
        # Use PillDetailSerializer for GET (list) requests
        return PillDetailSerializer

class PillRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Pill.objects.all()
    serializer_class = PillDetailSerializer
    permission_classes = [IsAdminUser] 

class CouponListCreateView(generics.ListCreateAPIView):
    queryset = CouponDiscount.objects.all()
    serializer_class = CouponDiscountSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = CouponDiscountFilter
    permission_classes = [IsAdminUser] 

class CouponRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CouponDiscount.objects.all()
    serializer_class = CouponDiscountSerializer
    permission_classes = [IsAdminUser] 

class ShippingListCreateView(generics.ListCreateAPIView):
    queryset = Shipping.objects.all()
    serializer_class = ShippingSerializer
    filterset_fields = ['government']
    permission_classes = [IsAdminUser] 

class ShippingRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Shipping.objects.all()
    serializer_class = ShippingSerializer
    permission_classes = [IsAdminUser] 

class RatingListCreateView(generics.ListCreateAPIView):
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer
    filterset_fields = ['product']
    permission_classes = [IsAdminUser] 

class RatingDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer
    permission_classes = [IsAdminUser] 

class ProductAvailabilityListCreateView(generics.ListCreateAPIView):
    queryset = ProductAvailability.objects.all()
    serializer_class = ProductAvailabilitySerializer
    permission_classes = [IsAdminUser] 
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product', 'color', 'size']

class ProductAvailabilityDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ProductAvailability.objects.all()
    serializer_class = ProductAvailabilitySerializer
    permission_classes = [IsAdminUser] 

class ProductAvailabilitiesView(generics.ListAPIView):
    def get(self, request, product_id):
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        # Group availabilities by size and color, and sum the quantities
        grouped_availabilities = defaultdict(int)
        for availability in product.availabilities.all():
            color_id = availability.color.id if availability.color else None
            color_name = availability.color.name if availability.color else None
            key = (availability.size, color_id, color_name)
            grouped_availabilities[key] += availability.quantity

        # Convert the grouped data into the desired format
        result = [
            {
                "size": size,
                "color": {
                    "id": color_id,
                    "name": color_name
                },
                "quantity": quantity
            }
            for (size, color_id, color_name), quantity in grouped_availabilities.items()
        ]

        # Serialize the result
        serializer = ProductAvailabilityBreifedSerializer(result, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class AdminPayRequestCreateView(generics.CreateAPIView):
    queryset = PayRequest.objects.all()
    serializer_class = PayRequestSerializer
    permission_classes = [IsAdminUser]  
    parser_classes = [MultiPartParser, FormParser] 

    def perform_create(self, serializer):
        # Ensure the pill exists
        pill_id = self.request.data.get('pill')
        try:
            pill = Pill.objects.get(id=pill_id)
            # Check if the pill is already paid
            if pill.paid:
                raise serializers.ValidationError("This pill is already paid.")
            # Create the PayRequest with is_applied=True
            serializer.save(pill=pill, is_applied=True)
        except Pill.DoesNotExist:
            raise serializers.ValidationError("Pill does not exist.")
    
class ApplyPayRequestView(generics.UpdateAPIView):
    queryset = PayRequest.objects.all()
    serializer_class = PayRequestSerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'id'

    def update(self, request, *args, **kwargs):
        # Get the PayRequest instance
        pay_request = self.get_object()

        # Check if the PayRequest is already applied
        if pay_request.is_applied:
            return Response({"error": "This payment request has already been applied."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the associated Pill is already paid
        pill = pay_request.pill
        if pill.paid:
            return Response({"error": "This pill is already paid."}, status=status.HTTP_400_BAD_REQUEST)

        # Update the PayRequest to mark it as applied
        pay_request.is_applied = True
        pay_request.save()

        # Update the associated Pill to mark it as paid
        pill.paid = True
        pill.status = 'p'
        pill.save()
        if pill.pilladdress:
            prepare_whatsapp_message(pill.pilladdress.phone, pill)

        # Return the updated PayRequest
        serializer = self.get_serializer(pay_request)
        return Response(serializer.data, status=status.HTTP_200_OK)





