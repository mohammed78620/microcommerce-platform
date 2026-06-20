from rest_framework import serializers
from .models import Product, ProductVariant, Category, Tag


class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ["id", "price", "colour", "size", "type", "category"]


class ProductSerializer(serializers.ModelSerializer):
    product_variant = ProductVariantSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ["id", "name", "description", "product_variant", "created_at", "updated_at"]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"
