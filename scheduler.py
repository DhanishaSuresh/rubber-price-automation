import os
import sys
import psycopg2
import subprocess
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


SCRAPER_PATH = os.path.join(BASE_DIR, "scrape.py")

subprocess.run([sys.executable, SCRAPER_PATH])

load_dotenv()


def scheduler():
    print("Scheduler started")

    while True:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            port=os.getenv("DB_PORT")
        )


        conn.autocommit = True
        cur = conn.cursor()

        cur.execute("""
            SELECT id, site_name, frequency, next_run
            FROM scraper_master
            WHERE status=TRUE
        """)

        now = datetime.now()

        for sid, site, freq, nxt in cur.fetchall():
            print(f"[CHECK] {site} | now={now} | next_run={nxt}")

            if not nxt or now >= nxt:
                print(f"[RUN] {site} scraping started")

                # FIX: use correct scraper path
                subprocess.run([sys.executable, SCRAPER_PATH, site])

                next_time = now + timedelta(hours=freq)
                cur.execute(
                    "UPDATE scraper_master SET next_run=%s WHERE id=%s",
                    (next_time, sid)
                )
                conn.commit()

                print(f"[DONE] {site} | next_run={next_time}")
            else:
                print(f"[SKIP] {site} | runs at {nxt}")

        cur.close()
        conn.close()

        time.sleep(30)


if __name__ == "__main__":
    scheduler()
