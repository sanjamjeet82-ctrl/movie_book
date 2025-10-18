# movies/admin.py
from django.contrib import admin
from .models import Genre, Language, Theater, Movie, Show, Seat, Booking
from django.db.models import Sum, Count

@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ("name",)

@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ("name",)

@admin.register(Theater)
class TheaterAdmin(admin.ModelAdmin):
    list_display = ("name", "city")

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ("title",)
    filter_horizontal = ("genres", "languages")

@admin.register(Show)
class ShowAdmin(admin.ModelAdmin):
    list_display = ("movie", "theater", "start_time", "price")

@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ("show", "row", "number", "is_booked", "reserved_by", "reserved_until")
    list_filter = ("is_booked",)



@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "show", "total_amount", "paid", "created_at")
    readonly_fields = ("confirmation_uuid",)
    def seat_list(self, obj):
        seats = obj.seats.all()
        return ", ".join([f"{s.row}{s.number}" for s in seats]) if seats else "No seats"
    seat_list.short_description = "Seats"
 