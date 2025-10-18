# movies/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, time
from django.conf import settings
import uuid

class Genre(models.Model):
    name = models.CharField(max_length=64, unique=True)
    def __str__(self):
        return self.name

class Language(models.Model):
    name = models.CharField(max_length=64, unique=True)
    def __str__(self):
        return self.name

class Theater(models.Model):
    name = models.CharField(max_length=128)
    city = models.CharField(max_length=64)
    def __str__(self):
        return f"{self.name} - {self.city}"

class Movie(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    duration_minutes = models.PositiveIntegerField()
    genres = models.ManyToManyField(Genre, blank=True)
    languages = models.ManyToManyField(Language, blank=True)
    trailer_youtube_id = models.CharField(max_length=32, blank=True)
    poster_url = models.URLField(blank=True)
    def __str__(self):
        return self.title

class Show(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    date = models.DateField(default=date.today)  # Automatically sets today's date
    time = models.TimeField(default=time(18, 0))  # Default time: 6:00 PM
    theater = models.ForeignKey(Theater, on_delete=models.CASCADE)
    start_time = models.DateTimeField(null=True, blank=True)
    price = models.DecimalField(max_digits=7, decimal_places=2, default=150.00)
    total_seats = models.PositiveIntegerField(default=60)
    def __str__(self):
        return f"{self.movie.title} on {self.date} at {self.time}  "

class Seat(models.Model):
    show = models.ForeignKey(Show, on_delete=models.CASCADE, related_name="seats")
    row = models.CharField(max_length=2)
    number = models.PositiveIntegerField()
    is_booked = models.BooleanField(default=False)
    reserved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    reserved_until = models.DateTimeField(null=True, blank=True)
    def __str__(self):
        return f"{self.show} - {self.row}{self.number}"

class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    show = models.ForeignKey(Show, on_delete=models.CASCADE)
    seats = models.ManyToManyField(Seat)
    total_amount = models.DecimalField(max_digits=9, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    paid = models.BooleanField(default=False)
    payment_id = models.CharField(max_length=128, blank=True)
    confirmation_uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    def __str__(self):
        return f"Booking {self.id} - {self.show.movie.title}"
