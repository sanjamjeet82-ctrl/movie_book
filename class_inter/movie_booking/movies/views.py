# movies/views.py
from django.shortcuts import render, get_object_or_404, redirect
from .models import Movie, Genre, Language, Show, Seat, Booking, Theater
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import send_mail
from .utils import send_booking_confirmation
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Sum, F
from movies.models import Booking
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, HttpResponse
from .email_utils import send_booking_email 
import stripe
from django.db.models import Sum, Count
import datetime
import decimal

stripe.api_key = settings.STRIPE_SECRET_KEY

def movie_list(request):
    genre = request.GET.get("genre")
    lang = request.GET.get("language")
    movies = Movie.objects.all()
    if genre:
        movies = movies.filter(genres__name__iexact=genre)
    if lang:
        movies = movies.filter(languages__name__iexact=lang)
    genres = Genre.objects.all()
    languages = Language.objects.all()
    return render(request, "movies/movie_list.html", {
        "movies": movies.distinct(),
        "genres": genres,
        "languages": languages,
    })

def movie_detail(request, movie_id):
    movie = get_object_or_404(Movie, pk=movie_id)
    shows = Show.objects.filter(movie=movie, start_time__gte=timezone.now()).order_by("start_time")
    return render(request, "movies/movie_detail.html", {
        "movie": movie,
        "shows": shows,
        "stripe_pub": settings.STRIPE_PUBLISHABLE_KEY,
    })

def create_booking(request):
    show_id = request.POST.get("show_id")
    seat_ids = request.POST.getlist("seat_ids[]")

    show = get_object_or_404(Show, id=show_id)
    seats = Seat.objects.filter(id__in=seat_ids, show=show, is_booked=False)

    if not seats.exists():
        return JsonResponse({"error": "No valid seats selected"}, status=400)

    booking = Booking.objects.create(show=show, user=request.user)
    booking.seats.set(seats)
    booking.total_amount = show.price * seats.count()
    booking.save()

    return JsonResponse({"booking_id": booking.id})



def theater_list(request):
    theaters = [
        {
            "name": "CineMax Central",
            "city": "Srinagar",
            "image_url": "https://studybreaks.com/wp-content/uploads/2017/06/41-majesticbrookfield-exteriorjpg.jpg"
        },
        {
            "name": "Galaxy Multiplex",
            "city": "Srinagar",
            "image_url": "https://www.fodors.com/wp-content/uploads/2019/06/ParisHistoricTheaters__HERO_Grand_Rex_Etoiles.jpg"
        },
        {
            "name": "Royal Cinemas",
            "city": "Srinagar",
            "image_url": "https://tse4.mm.bing.net/th/id/OIP.p5h4WeCgz_XPPr4944oWDwHaEo?cb=12&rs=1&pid=ImgDetMain&o=7&rm=3"
        }
    ]
    return render(request, "movies/theaters.html", {"theaters": theaters})

@login_required
def seat_selection(request, show_id):
    show = get_object_or_404(Show, pk=show_id)
    seats = show.seats.order_by("row", "number")
    # release expired reservations in view as safeguard
    now = timezone.now()

    # ✅ Cancel unpaid bookings older than 5 minutes
    expired_bookings = Booking.objects.filter(
        paid=False,
        created_at__lt=now - datetime.timedelta(minutes=5)
    )
    for booking in expired_bookings:
        booking.seats.update(reserved_by=None, reserved_until=None)
        booking.delete()
    expired_seats = seats.filter(
        reserved_until__lt=now,
        reserved_until__isnull=False,
        is_booked=False
    )
    for s in expired_seats:
        s.reserved_by = None
        s.reserved_until = None
        s.save()
    return render(request, "movies/seat_selection.html", {
        "show": show,
        "seats": seats,
        "reservation_seconds": settings.SEAT_RESERVATION_SECONDS,
    })



# 💳 Stripe Checkout session
@login_required
def checkout(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    # ✅ Store booking ID in session for use in success view
    request.session["latest_booking_id"] = booking.id

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': f"Booking for {booking.show.movie.title}",
                },
                'unit_amount': int(booking.total_amount * 100),
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=request.build_absolute_uri('/success/'),
        cancel_url=request.build_absolute_uri('/cancel/'),
    )

    return render(request, 'movies/checkout.html', {
        'booking': booking,
        'stripe_pub': settings.STRIPE_PUBLISHABLE_KEY,
        'session_id': session.id
    })




@login_required




def success(request):
    booking_id = request.session.get("latest_booking_id")
    if booking_id:
        booking = Booking.objects.get(id=booking_id)

        booking.paid = True
        booking.save()

        # 🔍 Debugging: print date and time to console
        print("Date:", booking.show.date)
        print("Time:", booking.show.time)

        send_booking_email(booking)

        del request.session["latest_booking_id"]
        return render(request, 'movies/success.html', {'booking': booking})
    return redirect('/')


    
@login_required
def cancel (request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id)
    # release seats on failure
    for seat in booking.seats.all():
        seat.reserved_by = None
        seat.reserved_until = None
        seat.save()
    booking.delete()
    return render(request, "movies/cancel.html", {})


@login_required
def api_reserve_seat(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)
    seat_id = request.POST.get("seat_id")
    action = request.POST.get("action")  # "reserve" or "release"
    seat = get_object_or_404(Seat, pk=seat_id)
    now = timezone.now()
    if action == "reserve":
        if seat.is_booked:
            return JsonResponse({"status": "booked"}, status=409)
        if seat.reserved_until and seat.reserved_until > now and seat.reserved_by != request.user:
            return JsonResponse({"status": "reserved"}, status=409)
        seat.reserved_by = request.user
        seat.reserved_until = now + datetime.timedelta(seconds=settings.SEAT_RESERVATION_SECONDS)
        seat.save()
        return JsonResponse({"status": "reserved", "reserved_until": seat.reserved_until.isoformat()})
    elif action == "release":
        if seat.reserved_by == request.user or True:
            seat.reserved_by = None
            seat.reserved_until = None
            seat.save()
            return JsonResponse({"status": "released"})
        return JsonResponse({"status": "forbidden"}, status=403)
    return JsonResponse({"error": "unknown action"}, status=400)

@login_required
def api_release_seat(request):
    # convenience endpoint; not used if api_reserve_seat used with release action
    return api_reserve_seat(request)

def _is_admin(user):
    return user.is_staff


@staff_member_required
def admin_dashboard(request):
    bookings = Booking.objects.filter(paid=True).select_related('show__movie', 'show__theater')

    # Core metrics
    total_revenue = bookings.aggregate(total=Sum('total_amount'))['total'] or 0
    total_bookings = bookings.count()
    total_tickets = bookings.aggregate(tickets=Sum('seats'))['tickets'] or 0
    avg_ticket_price = round(total_revenue / total_tickets, 2) if total_tickets else 0

    # Recent bookings
    recent_bookings = bookings.order_by('-created_at')[:10]

    # Most popular movies
    popular_movies = (
        bookings.values(title=F('show__movie__title'))
        .annotate(count=Sum('seats'))
        .order_by('-count')[:5]
    )

    # Busiest theaters
    busiest_theaters = (
        bookings.values(name=F('show__theater__name'), city=F('show__theater__city'))
        .annotate(count=Sum('seats'))
        .order_by('-count')[:5]
    )

    # Revenue by genre
    genre_revenue = (
        bookings.values(genre=F('show__movie__genres__name'))
        .annotate(revenue=Sum('total_amount'))
        .order_by('-revenue')
    )

    context = {
        "total_revenue": total_revenue,
        "total_bookings": total_bookings,
        "total_tickets": total_tickets,
        "avg_ticket_price": avg_ticket_price,
        "recent_bookings": recent_bookings,
        "popular_movies": list(popular_movies),
        "busiest_theaters": list(busiest_theaters),
        "genre_revenue": list(genre_revenue),
    }

    return render(request, "movies/admin_dashboard.html", context)

# utility function to create a booking after seat selection
@login_required
def create_booking_from_selection(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)
    show_id = request.POST.get("show_id")
    seat_ids = request.POST.getlist("seat_ids[]")
    show = get_object_or_404(Show, pk=show_id)
    seats = Seat.objects.filter(pk__in=seat_ids, show=show)
    # validate reservations
    now = timezone.now()
    for s in seats:
        if s.is_booked or (s.reserved_until and s.reserved_until < now) or (s.reserved_by and s.reserved_by != request.user):
            return JsonResponse({"error": "one_or_more_seats_unavailable"}, status=409)
    total = sum([show.price for s in seats])
    booking = Booking.objects.create(user=request.user, show=show, total_amount=total)
    booking.seats.set(seats)
    # mark reserved_until to keep them while going to checkout
    expiry = now + datetime.timedelta(seconds=settings.SEAT_RESERVATION_SECONDS)
    seats.update(reserved_by=request.user, reserved_until=expiry)
    return JsonResponse({"booking_id": booking.id})
