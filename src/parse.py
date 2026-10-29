import json
from pathlib import Path
import pandas as pd

RAW = Path("data/raw")
OUT = Path("data/clean/trials.csv")


def parse_study(study):
    proto = study.get("protocolSection", {})
    ident = proto.get("identificationModule", {})
    status = proto.get("statusModule", {})
    design = proto.get("designModule", {})
    cond = proto.get("conditionsModule", {})
    sponsor = proto.get("sponsorCollaboratorsModule", {})

    return {
        "nct_id": ident.get("nctId"),
        "title": ident.get("briefTitle"),
        "status": status.get("overallStatus"),
        "start_date": status.get("startDateStruct", {}).get("date"),
        "phase": "; ".join(design.get("phases", [])),
        "conditions": "; ".join(cond.get("conditions", [])),
        "sponsor": sponsor.get("leadSponsor", {}).get("name"),
        "enrollment": design.get("enrollmentInfo", {}).get("count"),
    }


def main():
    rows = []
    for path in RAW.glob("*.json"):
        drug = path.stem
        with open(path, encoding="utf-8") as f:
            studies = json.load(f)
        for study in studies:
            row = parse_study(study)
            row["drug"] = drug
            rows.append(row)

    df = pd.DataFrame(rows)
    df["start_year"] = pd.to_datetime(df["start_date"], errors="coerce").dt.year
    df = df.drop_duplicates(subset=["nct_id", "drug"])
    print(df.shape)
    print(df["drug"].value_counts())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False, encoding="utf-8-sig")
    print("Saved:", OUT.resolve(), len(df))

if __name__ == "__main__":
    main()