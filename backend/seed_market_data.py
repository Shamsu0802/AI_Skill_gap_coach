
import csv
from datetime import datetime
from pathlib import Path

from app.database import SessionLocal
from app.models import MarketSkillObservation


BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "job_market_sample_dataset.csv"
DATA_SOURCE = "Synthetic sample data - not real job postings"


def seed_market_data():
    if not CSV_PATH.exists():
        print(f"CSV file not found: {CSV_PATH}")
        return

    db = SessionLocal()

    try:
        # Avoid importing the same CSV observations more than once.
        existing = (
            db.query(MarketSkillObservation)
            .filter(MarketSkillObservation.source == DATA_SOURCE)
            .first()
        )

        if existing:
            print("Sample CSV dataset is already loaded.")
            return

        observations = []

        with CSV_PATH.open("r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            required_columns = {
                "target_role",
                "skill",
                "posting_count",
                "total_postings",
                "demand_percentage",
                "source",
                "observed_at",
            }

            if not required_columns.issubset(reader.fieldnames or []):
                raise ValueError(
                    "CSV is missing one or more required columns."
                )

            for row in reader:
                observed_at = datetime.fromisoformat(row["observed_at"])

                observations.append(
                    MarketSkillObservation(
                        target_role=row["target_role"],
                        skill=row["skill"],
                        posting_count=int(row["posting_count"]),
                        total_postings=int(row["total_postings"]),
                        demand_percentage=float(row["demand_percentage"]),
                        source=DATA_SOURCE,
                        observed_at=observed_at,
                    )
                )

        db.add_all(observations)
        db.commit()

        print(
            f"Successfully imported {len(observations)} observations "
            "from the sample CSV."
        )

    except Exception as error:
        db.rollback()
        print(f"Import failed: {error}")

    finally:
        db.close()


if __name__ == "__main__":
    seed_market_data()
