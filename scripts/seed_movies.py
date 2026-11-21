"""
Seed (pre-fill) the database with sample movies.

Run it from the project root (virtual env active):
    python -m scripts.seed_movies

The first 8 movies are the exact same ones the Android app had hard-coded in
`FakeMovieApiService`, so the app looks the same once it talks to this API.

Safe to run many times: a movie that already exists (same title + year) is skipped.

Notice that this script uses MovieService - the SAME business logic the API
uses. That's a big benefit of keeping HTTP out of the service layer.
"""

from app.core.database import SessionLocal
from app.core.exceptions import ConflictError
from app.schemas import MovieCreate
from app.services import MovieService

# Each dict uses the same keys as the MovieCreate schema.
SAMPLE_MOVIES = [
    # ---- The 8 movies from the Android FakeMovieApiService -------------------
    {
        "title": "Aurora Protocol",
        "overview": "A rescue pilot discovers a hidden signal that could stop a city-wide blackout.",
        "poster_url": "https://picsum.photos/seed/aurora-protocol/500/750",
        "backdrop_url": "https://picsum.photos/seed/aurora-backdrop/1200/675",
        "rating": 8.2,
        "release_year": 2026,
        "genres": ["Sci-Fi", "Thriller"],
    },
    {
        "title": "The Last Lantern",
        "overview": "Two siblings cross a flooded coast to return a mysterious lantern to its keeper.",
        "poster_url": "https://picsum.photos/seed/last-lantern/500/750",
        "backdrop_url": "https://picsum.photos/seed/lantern-backdrop/1200/675",
        "rating": 7.8,
        "release_year": 2025,
        "genres": ["Adventure", "Drama"],
    },
    {
        "title": "Midnight Kitchen",
        "overview": "A burned-out chef turns a closed diner into a secret midnight supper club.",
        "poster_url": "https://picsum.photos/seed/midnight-kitchen/500/750",
        "backdrop_url": "https://picsum.photos/seed/kitchen-backdrop/1200/675",
        "rating": 7.4,
        "release_year": 2024,
        "genres": ["Comedy", "Drama"],
    },
    {
        "title": "North Star Run",
        "overview": "A courier racing across polar terrain becomes the only hope for a stranded research team.",
        "poster_url": "https://picsum.photos/seed/north-star-run/500/750",
        "backdrop_url": "https://picsum.photos/seed/north-star-backdrop/1200/675",
        "rating": 8.0,
        "release_year": 2026,
        "genres": ["Action", "Adventure"],
    },
    {
        "title": "Paper Moons",
        "overview": "An illustrator finds that every moon she draws changes the dreams of her neighborhood.",
        "poster_url": "https://picsum.photos/seed/paper-moons/500/750",
        "backdrop_url": "https://picsum.photos/seed/moons-backdrop/1200/675",
        "rating": 7.6,
        "release_year": 2023,
        "genres": ["Fantasy", "Romance"],
    },
    {
        "title": "Static Hearts",
        "overview": "A radio host and a skeptical engineer chase a strange broadcast across the desert.",
        "poster_url": "https://picsum.photos/seed/static-hearts/500/750",
        "backdrop_url": "https://picsum.photos/seed/static-backdrop/1200/675",
        "rating": 7.1,
        "release_year": 2025,
        "genres": ["Mystery", "Romance"],
    },
    {
        "title": "Harbor of Glass",
        "overview": "A detective returns home when a quiet harbor town begins reflecting impossible memories.",
        "poster_url": "https://picsum.photos/seed/harbor-glass/500/750",
        "backdrop_url": "https://picsum.photos/seed/harbor-backdrop/1200/675",
        "rating": 8.4,
        "release_year": 2026,
        "genres": ["Mystery", "Drama"],
    },
    {
        "title": "Orbit Cafe",
        "overview": "On a tiny orbital diner, regular customers prepare for Earth's first interstellar festival.",
        "poster_url": "https://picsum.photos/seed/orbit-cafe/500/750",
        "backdrop_url": "https://picsum.photos/seed/orbit-backdrop/1200/675",
        "rating": 7.9,
        "release_year": 2024,
        "genres": ["Sci-Fi", "Comedy"],
    },
    # ---- Extra movies so pagination and search have more data ---------------
    {
        "title": "Copper Valley",
        "overview": "A retired miner reopens a forgotten tunnel to save the town that forgot him.",
        "poster_url": "https://picsum.photos/seed/copper-valley/500/750",
        "backdrop_url": "https://picsum.photos/seed/copper-backdrop/1200/675",
        "rating": 7.3,
        "release_year": 2022,
        "genres": ["Drama", "Western"],
    },
    {
        "title": "Signal Garden",
        "overview": "Botanists on a remote island notice their plants are answering radio messages.",
        "poster_url": "https://picsum.photos/seed/signal-garden/500/750",
        "backdrop_url": "https://picsum.photos/seed/garden-backdrop/1200/675",
        "rating": 7.7,
        "release_year": 2025,
        "genres": ["Sci-Fi", "Mystery"],
    },
    {
        "title": "Thunder Lane",
        "overview": "A street racer gets one last chance to clear her brother's name in a midnight rally.",
        "poster_url": "https://picsum.photos/seed/thunder-lane/500/750",
        "backdrop_url": "https://picsum.photos/seed/thunder-backdrop/1200/675",
        "rating": 6.8,
        "release_year": 2024,
        "genres": ["Action", "Thriller"],
    },
    {
        "title": "The Quiet Archive",
        "overview": "A librarian discovers a room of books describing events that have not happened yet.",
        "poster_url": "https://picsum.photos/seed/quiet-archive/500/750",
        "backdrop_url": "https://picsum.photos/seed/archive-backdrop/1200/675",
        "rating": 8.6,
        "release_year": 2023,
        "genres": ["Fantasy", "Mystery"],
    },
    {
        "title": "Little Giants",
        "overview": "A struggling youth football team recruits a coach who has never seen a game.",
        "poster_url": "https://picsum.photos/seed/little-giants-team/500/750",
        "backdrop_url": "https://picsum.photos/seed/giants-backdrop/1200/675",
        "rating": 6.9,
        "release_year": 2021,
        "genres": ["Comedy", "Family"],
    },
    {
        "title": "Saltwater Letters",
        "overview": "Letters washed ashore connect a fisherman and a stranger living an ocean away.",
        "poster_url": "https://picsum.photos/seed/saltwater-letters/500/750",
        "backdrop_url": "https://picsum.photos/seed/saltwater-backdrop/1200/675",
        "rating": 7.5,
        "release_year": 2022,
        "genres": ["Romance", "Drama"],
    },
    {
        "title": "Dust and Circuits",
        "overview": "In a desert scrapyard, a lonely robot builds a companion from spare parts.",
        "poster_url": "https://picsum.photos/seed/dust-circuits/500/750",
        "backdrop_url": "https://picsum.photos/seed/dust-backdrop/1200/675",
        "rating": 8.1,
        "release_year": 2024,
        "genres": ["Sci-Fi", "Family", "Animation"],
    },
    {
        "title": "Ninth Floor",
        "overview": "Office workers trapped overnight realize the building has added a floor that wasn't there.",
        "poster_url": "https://picsum.photos/seed/ninth-floor/500/750",
        "backdrop_url": "https://picsum.photos/seed/ninth-backdrop/1200/675",
        "rating": 6.6,
        "release_year": 2025,
        "genres": ["Horror", "Thriller"],
    },
]


def seed_movies() -> None:
    created_count = 0
    skipped_count = 0

    # `with` closes the session automatically at the end (a "context manager").
    with SessionLocal() as db:
        service = MovieService(db)

        for movie_data in SAMPLE_MOVIES:
            # Validate the dict with the same schema the API uses.
            movie_in = MovieCreate(**movie_data)
            try:
                movie = service.create_movie(movie_in)
                print(f"  + created  #{movie.id:<3} {movie.title}")
                created_count = created_count + 1
            except ConflictError:
                print(f"  = skipped       {movie_in.title} (already exists)")
                skipped_count = skipped_count + 1

    print(f"\nDone. Created {created_count}, skipped {skipped_count}.")


# This block only runs when the file is executed directly
# (python -m scripts.seed_movies), not when it is imported by another file.
if __name__ == "__main__":
    seed_movies()
