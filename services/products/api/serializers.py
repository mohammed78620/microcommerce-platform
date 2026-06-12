from rest_framework import serializers
from .models import Product, ProductVariant


class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ["id", "price", "colour", "size", "type"]


class ProductSerializer(serializers.ModelSerializer):
    product_variant = ProductVariantSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ["id", "name", "description", "product_variant", "created_at", "updated_at"]
