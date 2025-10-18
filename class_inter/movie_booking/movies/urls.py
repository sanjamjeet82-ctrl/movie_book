# movies/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.movie_list, name="movie_list"),
    path("movies/<int:movie_id>/", views.movie_detail, name="movie_detail"),
    path("shows/<int:show_id>/seats/", views.seat_selection, name="seat_selection"),
    # add this path
     path("create-booking/", views.create_booking_from_selection, name="create_booking"),
     path('theaters/', views.theater_list, name="theaters"),


    path("checkout/<int:booking_id>/", views.checkout, name="checkout"),
    path('success/', views.success, name='success'),
    path('cancel/', views.cancel, name='cancel'),

    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("api/reserve-seat/", views.api_reserve_seat, name="api_reserve_seat"),
    path("api/release-seat/", views.api_release_seat, name="api_release_seat"),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
]

