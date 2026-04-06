from app import create_app
from app.storage import store
from utils.seeding import seed_demo_data


def main():
    app = create_app()
    with app.app_context():
        seed_demo_data(store, reset=True)
        print("Seeded 1000 demo users plus admin.")


if __name__ == "__main__":
    main()
