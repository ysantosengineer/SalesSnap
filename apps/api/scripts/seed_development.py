from app.db.seed import seed_development_data
from app.db.session import SessionLocal


def main() -> None:
    with SessionLocal() as session:
        seed_development_data(session)


if __name__ == "__main__":
    main()
