from fastapi import APIRouter, UploadFile, File, Query
from fastapi.responses import JSONResponse
import pandas as pd
import io
from typing import List, Optional
import unicodedata

router = APIRouter()


def normalize_column(col: str) -> str:
    return (
        unicodedata.normalize("NFKD", col)  # remove weird unicode
        .encode("ascii", "ignore")
        .decode("utf-8")
        .strip()
        .lower()
    )

@router.post("/upload-csv/")
async def upload_csv(
    file: UploadFile = File(...),
    applications: Optional[List[str]] = Query(None)
):
    content = await file.read()

    # Skip first 5 rows manually
    df = pd.read_excel(io.BytesIO(content), skiprows=5)

    # Normalize column names
    df.columns = df.columns.str.strip().str.lower()
    print("Normalized Columns:", df.columns.tolist())

    required_cols = {"applications", "title", "link", "implementation complexity"}
    if not required_cols.issubset(set(df.columns)):
        return JSONResponse(
            status_code=400,
            content={"error": "Missing expected columns", "columns_detected": df.columns.tolist()}
        )

    # Optional filtering
    if applications:
        df = df[df["applications"].isin(applications)]

    # Group and map
    grouped_stories = []
    for app_name, group in df.groupby("applications"):
        stories = [
            {
                "title": row["title"],
                "description": row["link"],
                "priority": row["implementation complexity"]
            }
            for _, row in group.iterrows()
        ]
        grouped_stories.append({
            "application": app_name,
            "stories": stories
        })

    return grouped_stories
