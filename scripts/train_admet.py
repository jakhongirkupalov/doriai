"""2-qadam: ADMET modellarini o'qitish va baholash.

Misollar:
  python scripts/train_admet.py                         # hammasi (~5–15 daqiqa)
  python scripts/train_admet.py --tasks solubility bbbp clintox   # tezkor
"""
import argparse
import time
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

from doriai.models.admet import TASKS, save_metrics, train_task


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", nargs="*", default=list(TASKS), choices=list(TASKS))
    args = ap.parse_args()

    all_metrics = {}
    for name in args.tasks:
        t0 = time.time()
        spec = TASKS[name]
        print(f"▶ {name:28s} ({spec.kind}) o'qitilmoqda...", flush=True)
        m = train_task(spec)
        all_metrics[name] = m
        main_metric = f"ROC-AUC={m.get('roc_auc', float('nan')):.3f}" if spec.kind == "classification" \
            else f"RMSE={m['rmse']:.3f}  R²={m['r2']:.3f}"
        print(f"  ✓ {main_metric}  (n={m['n_total']}, {time.time() - t0:.0f}s)")
    save_metrics(all_metrics)
    print("\nBarcha modellar models/admet/ papkasida saqlandi.")


if __name__ == "__main__":
    main()
