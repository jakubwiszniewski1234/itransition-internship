import os
import time
import statistics
import psycopg2

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
        port=int(os.getenv("DB_PORT", 5432)),
        sslmode=os.getenv("DB_SSLMODE", "prefer")
    )

def execute_single_run(cursor, conn, seed, locale, batch_index, batch_size):
    cursor.execute("SELECT * FROM generate_users_batch(%s, %s, %s, %s);", (seed, locale, batch_index, batch_size))
    cursor.fetchall()
    conn.commit()

def measure_single_run(cursor, conn, seed, locale, batch_index, batch_size):
    start_time = time.perf_counter()
    execute_single_run(cursor, conn, seed, locale, batch_index, batch_size)
    return time.perf_counter() - start_time

def calculate_stats(times, batch_size):
    return {
        "avg": statistics.mean(times),
        "min": min(times), "max": max(times),
        "stdev": statistics.stdev(times) if len(times) > 1 else 0.0,
        "efficiency": batch_size / statistics.mean(times)
    }

def print_summary(stats, iterations, batch_size):
    print(f"\niterations: {iterations}")
    print(f"size: {batch_size}")
    print(f"avg time: {stats['avg']:.4f}s")
    print(f"std: {stats['stdev']:.4f}s")
    print(f"fastest: {stats['min']:.4f}s")
    print(f"slowest: {stats['max']:.4f}s")
    print(f"avg efficiency: {stats['efficiency']:.2f} users/s")

def benchmark_user_generation(
    iterations: int = 10,
    batch_size: int = 1000,
    seed: int = 42,
    locale: str = "en_US"
) -> float:
    conn = get_db_connection()
    times = []

    try:
        with conn.cursor() as cursor:
            for i in range(iterations):
                duration = measure_single_run(cursor, conn, seed, locale, i, batch_size)
                times.append(duration)
                print(f"{i + 1}/{iterations}: {duration:.4f}s")
    finally:
        conn.close()

    stats = calculate_stats(times, batch_size)
    print_summary(stats, iterations, batch_size)
    return stats["avg"]

if __name__ == "__main__":
    benchmark_user_generation(iterations=10, batch_size=5000)