# from django.contrib import admin
# from .models import Product, Variation, ReviewRating, ProductGallery
# import admin_thumbnails


# @admin_thumbnails.thumbnail('image')
# class ProductGalleryInline(admin.TabularInline):
#     model = ProductGallery
#     extra = 1

# class ProductAdmin(admin.ModelAdmin):
#     list_display = ('product_name', 'price', 'stock', 'category', 'modified_date', 'is_available')
#     prepopulated_fields = {'slug': ('product_name',)}
#     inlines = [ProductGalleryInline]

# class VariationAdmin(admin.ModelAdmin):
#     list_display = ('product', 'variation_category', 'variation_value', 'is_active')
#     list_editable = ('is_active',)
#     list_filter = ('product', 'variation_category', 'variation_value')

# admin.site.register(Product, ProductAdmin)
# admin.site.register(Variation, VariationAdmin)
# admin.site.register(ReviewRating)
# admin.site.register(ProductGallery)

from django.contrib import admin
from .models import Product, Variation, ReviewRating, ProductGallery
import admin_thumbnails


@admin_thumbnails.thumbnail('image')
class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'product_name',
        'price',
        'offer_price',
        'stock',
        'category',
        'modified_date',
        'is_available'
    )
    search_fields = ('^product_name', '=id',"=price","=stock")
    list_filter = ('category', 'is_available')
    list_per_page = 25
    prepopulated_fields = {'slug': ('product_name',)}
    inlines = [ProductGalleryInline]


@admin.register(Variation)
class VariationAdmin(admin.ModelAdmin):
    list_display = ('product', 'variation_category', 'variation_value', 'is_active')
    list_editable = ('is_active',)
    list_filter = ('product', 'variation_category', 'variation_value')


@admin.register(ReviewRating)
class ReviewRatingAdmin(admin.ModelAdmin):
    pass


@admin.register(ProductGallery)
class ProductGalleryAdmin(admin.ModelAdmin):
    pass
