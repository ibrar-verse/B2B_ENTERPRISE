from django.contrib import admin
from .models import RFQ,Bid

@admin.register(RFQ)
class RFQAdmin(admin.ModelAdmin):
  list_display = ('title', 'buyer_organization', 'quantity', 'status', 'closing_date', 'created_at')
  list_filter = ('status', 'buyer_organization')
  search_fields = ('title', 'description')


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ('rfq', 'vendor_organization', 'unit_price', 'total_price', 'status', 'created_at')
    list_filter = ('status', 'vendor_organization')
    readonly_fields = ('total_price',)  # Auto-computed in sa