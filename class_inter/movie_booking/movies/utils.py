# utils.py
from django.core.mail import send_mail

def send_booking_confirmation(user_email, booking):
    subject = "Your Movie Booking Confirmation"
    message = f"""
Hi {booking.user.username},

Your booking for {booking.show.movie.title} on {booking.show.date} at {booking.show.time} is confirmed.

Seats: {', '.join(seat.label for seat in booking.seats.all())}
Total Amount: ${booking.total_amount}

Enjoy the show!
"""
    send_mail(subject, message, 'your_email@gmail.com', [user_email])
