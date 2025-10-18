from django.core.mail import send_mail
from django.template.loader import render_to_string

def send_booking_email(booking):
    subject = f"Your ticket for {booking.show.movie.title}"
    recipient = booking.user.email

    context = {
        'user': booking.user,
        'movie': booking.show.movie.title,
        'date': booking.show.date,
        'time': booking.show.time,
        'seats': booking.seats.all() if hasattr(booking, 'seats') else [],
    }

    message = render_to_string('emails/booking_confirmation.txt', context)
    html_message = render_to_string('emails/booking_confirmation.html', context)

    send_mail(
        subject,
        message,
        None,
        [recipient],
        html_message=html_message,
    )
