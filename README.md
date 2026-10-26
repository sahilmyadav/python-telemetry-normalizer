# Python Telemetry Normalizer

Python utility that takes telemetry data coming in different shapes and
normalizes it into one clean, consistent format, so downstream tools always
receive the same structure.

The working code lives in the `telenaryproject/` folder. It was built around an
Industrial IoT (IIoT) use case: telemetry streams from manufacturing equipment
arrive in more than one format (JSON from modern devices and a compact binary
format from legacy equipment) and need to be parsed, detected and unified in
real time.

## Features

- Automatic detection and parsing of JSON and binary telemetry formats
- Stream normalization into a single unified structure
- In-memory time-series storage with configurable retention
- Basic analytics: metric aggregation, device health and quality scores
- Anomaly detection with alert generation for critical conditions

## Getting Started

```bash
cd telenaryproject
pip install -r requirements.txt
python telemetry_integration.py
```

Run the integration tests with:

```bash
python test_integration.py
```

## Project Structure

```
telenaryproject/
  telemetry_integration.py   Main integration pipeline
  test_integration.py        Integration tests
  requirements.txt           Python dependencies
  README.md                  Detailed project notes
```

See `telenaryproject/README.md` for the full design write-up.
