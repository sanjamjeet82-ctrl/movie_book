from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, datetime, time
from movies.models import Genre, Language, Theater, Movie, Show, Seat

class Command(BaseCommand):
    help = "Seed all core data: genres, languages, theaters, movies, future shows, and seats"

    def handle(self, *args, **options):
        # Genres
        genres = ["Action", "Comedy", "Drama", "Thriller", "Sci-Fi"]
        genre_objs = {name: Genre.objects.get_or_create(name=name)[0] for name in genres}

        # Languages
        languages = ["Hindi", "English", "Urdu"]
        lang_objs = {name: Language.objects.get_or_create(name=name)[0] for name in languages}

        # Theaters
        theaters = [
            {"name": "CineMax Central", "city": "Srinagar"},
            {"name": "Galaxy Multiplex", "city": "Srinagar"},
            {"name": "Royal Cinemas", "city": "Srinagar"},
        ]
        theater_objs = [Theater.objects.get_or_create(name=t["name"], city=t["city"])[0] for t in theaters]

        # Movies
        sample_movies = [
            {
                "title": "PLay Dirty",
                "description": "A high-octane action thriller about a courier who uncovers a city-wide conspiracy.",
                "duration_minutes": 125,
                "genres": ["Action", "Thriller"],
                "languages": ["English"],
                "trailer_youtube_id": "6paP2-ry-QY",
                "poster_url": "https://img.rgstatic.com/content/movie/42747501-f661-4d24-a4b3-833c165b1767/poster-342.webp",
            },
            {
                "title": "28 Years Later",
                "description": "Survivors of the rage virus discover horrors that have mutated not only the infected but other survivors.",
                "duration_minutes": 155,
                "genres": ["Sci-Fi"],
                "languages": ["Hindi", "English"],
                "trailer_youtube_id": "mcvLKldPM08",
                "poster_url": "https://img.rgstatic.com/content/movie/64313b57-bbd6-47cb-878a-383fd4be3e3a/poster-342.webp",
            },
            {
                "title": "Inspector Zende",
                "description": "Inspector Zende pursues a serial killer who escaped prison and returned to Mumbai.",
                "duration_minutes": 142,
                "genres": ["Drama"],
                "languages": ["Hindi"],
                "trailer_youtube_id": "SqIE6lj2IGo",
                "poster_url": "https://img.rgstatic.com/content/movie/1e0f27bd-19b6-4314-9f56-ed7a560819c3/poster-342.webp",
            },
            {
                "title": "Coolie",
                "description": "A man's relentless quest for vengeance since youth, driven by righting past wrongs.",
                "duration_minutes": 138,
                "genres": ["Action"],
                "languages": ["English", "Hindi"],
                "trailer_youtube_id": "PuzNA314WCI",
                "poster_url": "https://img.rgstatic.com/content/movie/40a8e71a-814b-487b-b951-e8ef38580114/poster-342.webp",
            },
            {
                "title": "Superman",
                "description": "Superman must reconcile his alien Kryptonian heritage with his human upbringing.",
                "duration_minutes": 102,
                "genres": ["Action"],
                "languages": ["English", "Hindi"],
                "trailer_youtube_id": "Ox8ZLF6cGM0",
                "poster_url": "https://img.rgstatic.com/content/movie/44d7c988-dcbf-48c6-9aa5-7ff022e75d10/poster-342.webp",
            },
        ]

        movie_objs = []
        for m in sample_movies:
            movie, _ = Movie.objects.get_or_create(
                title=m["title"],
                defaults={
                    "description": m["description"],
                    "duration_minutes": m["duration_minutes"],
                    "trailer_youtube_id": m["trailer_youtube_id"],
                    "poster_url": m["poster_url"],
                }
            )
            movie.genres.set([genre_objs[g] for g in m["genres"]])
            movie.languages.set([lang_objs[l] for l in m["languages"]])
            movie.save()
            movie_objs.append(movie)

        # Create shows for next 7 days at 6:30 PM
        shows_created = []
        today = timezone.now().date()
        for movie in movie_objs:
            for theater in theater_objs:
                for day_offset in range(7):
                    show_date = today + timedelta(days=day_offset)
                    show_time = time(hour=18, minute=30)
                    show_datetime = timezone.make_aware(datetime.combine(show_date, show_time))

                    exists = Show.objects.filter(movie=movie, theater=theater, start_time=show_datetime).exists()
                    if not exists:
                        show = Show.objects.create(
                            movie=movie,
                            theater=theater,
                            start_time=show_datetime,
                            price=250,
                            total_seats=60
                        )
                        shows_created.append(show)

        # Create seats for each show (rows A–F, numbers 1–10)
        rows = ["A", "B", "C", "D", "E", "F"]
        seat_count = 0
        for show in shows_created:
            if show.seats.count() == 0:
                for r in rows:
                    for num in range(1, 11):
                        Seat.objects.create(show=show, row=r, number=num)
                        seat_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Seed complete: {len(genres)} genres, {len(languages)} languages, "
            f"{len(theater_objs)} theaters, {len(movie_objs)} movies, "
            f"{len(shows_created)} new shows, {seat_count} seats created."
        ))