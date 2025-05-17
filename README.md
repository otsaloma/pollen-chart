Pollen Chart
============

A visualization of the pollen situation in Helsinki in two parts: (1) A
lambda function that downloads data from [CAMS][] using [CDSAPI][] to an
S3 bucket and (2) a static client-side web app that renders that data
into a custom visualization.

[CAMS]: https://ads.atmosphere.copernicus.eu/datasets/cams-europe-air-quality-forecasts
[CDSAPI]: https://ads.atmosphere.copernicus.eu/how-to-api

## Getting Started

Follow CDSAPI setup instructions:

https://ads.atmosphere.copernicus.eu/how-to-api

Create a `.env` file with the following content.

```bash
CDSAPI_KEY=...
CDSAPI_URL=...
```

Create a virtual environment with `make venv`. Run `./download.py local`
to fetch pollen data. Use `make run` to launch the web app locally.
