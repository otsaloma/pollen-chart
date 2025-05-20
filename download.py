#!/usr/bin/env python3

import boto3
import cdsapi
import dataiter as di
import datetime
import io
import numpy as np
import os
import requests
import sys
import tempfile
import xarray as xr
import zipfile

from pathlib import Path

VARIABLES = {
    "alder_pollen":   "apg_conc",
    "birch_pollen":   "bpg_conc",
    "grass_pollen":   "gpg_conc",
    "mugwort_pollen": "mpg_conc",
    "olive_pollen":   "opg_conc",
    "ragweed_pollen": "rwpg_conc",
}

def retrieve(fm, to, hours):
    # https://ads.atmosphere.copernicus.eu/how-to-api
    # https://ads.atmosphere.copernicus.eu/datasets/cams-europe-air-quality-forecasts
    client = cdsapi.Client()
    zip_handle, zip_path = tempfile.mkstemp(suffix=".zip")
    client.retrieve("cams-europe-air-quality-forecasts", {
        "variable": list(VARIABLES.keys()),
        # Is FMI's SILAM the best in Finland?
        # https://silam.fmi.fi/pollen.html
        "model": ["silam"],
        "level": ["0"],
        "date": [f"{fm.isoformat()}/{to.isoformat()}"],
        "type": ["forecast"],
        "time": ["00:00"],
        "leadtime_hour": [str(x) for x in range(hours)],
        "data_format": "netcdf_zip",
        # Helsinki YMAX, XMIN, YMIN, XMAX
        # https://boundingbox.klokantech.com/
        "area": [60.3, 24.7, 60.1, 25.2],
    }, zip_path)
    print(f"Downloaded {zip_path}")
    nc_path = Path(zip_path).with_suffix(".nc")
    with zipfile.ZipFile(zip_path, "r") as zf:
        with zf.open("SILAM_FORECAST.nc") as f:
            nc_path.write_bytes(f.read())
            print(f"Extracted {nc_path}")
    with xr.open_dataset(nc_path, decode_timedelta=False) as dataset:
        data = dataset.to_dataframe().reset_index()
        data = di.DataFrame.from_pandas(data)
        assert data and data.nrow
    data.datetime = np.datetime64(fm, "s") + data.time.astype("timedelta64[h]")
    data.date = data.datetime.astype("datetime64[D]")
    return data

def download():
    today = datetime.date.today()
    first = today - datetime.timedelta(days=13)
    yesterday = today - datetime.timedelta(days=1)
    data1 = retrieve(first, yesterday, 24)
    data2 = retrieve(today, today, 96)
    data = data1.rbind(data2)
    data.partition = np.where(data.date < today, "past",
                              np.where(data.date == today, "today",
                                       "future"))

    # 1. Aggregate over hours to find the daily peaks for each grid cell.
    # 2. Aggregate over grid cells to find the city medians for each day.
    explode = lambda f: {x: f(x) for x in VARIABLES.values()}
    data = data.group_by("date", "partition", "longitude", "latitude").aggregate(**explode(di.max))
    data = data.group_by("date", "partition").aggregate(**explode(di.median))
    data = data.rename(**{k.split("_")[0]: v for k, v in VARIABLES.items()})
    data.date = data.date.as_string()
    return data

def download_bucket():
    data = download()
    text = data.to_json()
    blob = text.encode("utf-8")
    s3 = boto3.client("s3")
    s3.upload_fileobj(
        io.BytesIO(blob),
        "otsaloma.io",
        "siitepoly/helsinki.json",
        ExtraArgs={
            "ACL": "public-read",
            "CacheControl": "public, max-age=300"})
    print(f"Wrote {data.nrow} days to s3://otsaloma.io/siitepoly/helsinki.json.")

def download_local():
    data = download()
    data.write_npz("helsinki.npz")
    data.write_json("helsinki.json")
    print(f"From: {data.date.min()}")
    print(f"  To: {data.date.max()}")
    print(f"Wrote {data.nrow} days to helsinki.npz.")
    print(f"Wrote {data.nrow} days to helsinki.json.")

def lambda_handler(event, context):
    download_bucket()
    if url := os.getenv("SUCCESS_PING_URL"):
        requests.get(url, timeout=10)

if __name__ == "__main__":
    match sys.argv[1:]:
        case ["bucket"]:
            download_bucket()
        case ["local"]:
            download_local()
        case _:
            name = Path(__file__).name
            print(f"Usage: ./{name} bucket|local")
