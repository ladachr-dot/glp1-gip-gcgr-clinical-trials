import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "clean" / "trials.csv"
FIG = ROOT / "figures"

CATS = {
    "diabetes": ["diabet"],
    "obesity": ["obes", "overweight", "weight"],
    "liver": ["nash", "mash", "steatohep", "liver", "hepat"],
    "cardio": ["cardio", "heart", "hypertens"],
    "kidney": ["kidney", "renal", "nephro"],
    "healthy": ["healthy"],
}


def load():
    d = pd.read_csv(DATA)
    d["start_year"] = pd.to_numeric(d["start_date"].str[:4], errors="coerce")
    d = d[d["status"] != "WITHDRAWN"]
    d = d[d["start_year"].between(2010, 2026)].copy()
    d["start_year"] = d["start_year"].astype(int)
    return d


def classify_indications(d):
    low = d["conditions"].str.lower()
    for k, words in CATS.items():
        d[k] = low.str.contains("|".join(words), na=False)
    d["other"] = ~d[list(CATS)].any(axis=1)
    return d


def max_phase(s):
    nums = re.findall(r"PHASE(\d)", s) if isinstance(s, str) else []
    return f"Phase {max(nums)}" if nums else "Not specified"


def save(name):
    FIG.mkdir(exist_ok=True)
    plt.tight_layout()
    plt.savefig(FIG / name, dpi=150)
    plt.close()


def main():
    d = classify_indications(load())
    d["max_phase"] = d["phase"].apply(max_phase)
    order = d["drug"].value_counts().index.tolist()
    cols = list(CATS) + ["other"]

    print("Studies after cleaning:", len(d))
    print("Share started 2021+:", round((d["start_year"] >= 2021).mean(), 4))
    print(d["drug"].value_counts(normalize=True).round(4))

    by_year = d.groupby(["start_year", "drug"]).size().unstack(fill_value=0)[order]
    by_year.plot(kind="bar", stacked=True, figsize=(10, 5))
    plt.title("Trial starts by year and drug")
    plt.xlabel("Start year")
    plt.ylabel("Studies")
    save("01_trials_by_year.png")

    ind_year = d.groupby("start_year")[cols].sum()
    ind_year.plot(figsize=(10, 5), marker="o")
    plt.title("Studies by indication and start year")
    plt.xlabel("Start year")
    plt.ylabel("Studies")
    save("02_indications_by_year.png")

    prof = d.groupby("drug")[cols].mean().loc[order].round(2)
    print(prof)
    fig, ax = plt.subplots(figsize=(9, 5))
    im = ax.imshow(prof.values, cmap="Blues", aspect="auto")
    ax.set_xticks(range(len(cols)), cols)
    ax.set_yticks(range(len(order)), order)
    for i in range(prof.shape[0]):
        for j in range(prof.shape[1]):
            ax.text(j, i, f"{prof.values[i, j]:.2f}", ha="center", va="center")
    fig.colorbar(im)
    ax.set_title("Indication profile by drug (share of studies)")
    save("03_indication_profile.png")

    ph = pd.crosstab(d["drug"], d["max_phase"], normalize="index").loc[order]
    ph.plot(kind="barh", stacked=True, figsize=(10, 5))
    plt.title("Highest phase by drug (share of studies)")
    plt.xlabel("Share")
    save("04_phases_by_drug.png")

    top = d["sponsor"].value_counts().head(10).sort_values()
    top.plot(kind="barh", figsize=(9, 5))
    plt.title("Top 10 lead sponsors")
    plt.xlabel("Studies")
    save("05_top_sponsors.png")

    lead = d.groupby("drug")["sponsor"].agg(
        lead=lambda s: s.value_counts().index[0],
        lead_n=lambda s: s.value_counts().iloc[0],
        n="size",
    )
    lead["lead_share"] = (lead["lead_n"] / lead["n"]).round(2)
    print(lead)


if __name__ == "__main__":
    main()
