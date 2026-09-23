from pathlib import Path

def test_seed_data_exists():
    root = Path(__file__).resolve().parents[2]
    seed_dir = root / "simulator" / "seed_data"
    for name in ["operators.csv", "machines.csv", "tasks.csv", "task_time_logs.csv"]:
        assert (seed_dir / name).exists()
