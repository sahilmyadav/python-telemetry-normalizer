# Daikibo Industrials IIoT Telemetry Integration System

## Overview
This Python-based solution integrates dual-format telemetry streams from Daikibo Industrials' manufacturing equipment, providing a unified data pipeline for their Industrial Internet of Things (IIoT) infrastructure.

## Features

### 🔄 Dual Format Support
- **JSON Format**: Standard JSON telemetry from modern IIoT devices
- **Binary Format**: Compact binary protocol for legacy equipment
- Automatic format detection and parsing
- Extensible parser architecture for additional formats

### 📊 Real-time Processing
- Stream processing with automatic normalization
- In-memory time-series database with configurable retention
- Real-time analytics and anomaly detection
- Alert generation for critical conditions

### 📈 Analytics Capabilities
- Device health monitoring
- Metric aggregation and averaging
- Format distribution analysis
- Quality score tracking
- Anomaly detection for:
  - High temperature (>40°C)
  - Excessive vibration (>8 units)
  - Low data quality (<80%)
  - Device warnings/errors

### 🎯 Key Metrics Tracked
- Temperature (°C)
- Pressure (kPa)
- Humidity (%)
- Vibration levels
- Power consumption (W)

## Installation

### Requirements
- Python 3.8 or higher
- No external dependencies required (uses standard library only)

### Setup
```bash
# Clone or download the files
python telemetry_integration.py
```

## Usage

### Basic Usage
Run the main integration service:
```bash
python telemetry_integration.py
```

This will:
1. Start a 30-second simulation of both telemetry formats
2. Process and normalize the data streams
3. Display real-time dashboard updates every 5 seconds
4. Generate alerts for anomalies
5. Provide a final summary report

### Running Tests
```bash
python test_integration.py
```

### Integration with Existing Systems

#### Processing Individual Data Points
```python
from telemetry_integration import TelemetryIntegrationService
import asyncio

# Initialize service
service = TelemetryIntegrationService()

# Process JSON telemetry
json_data = '{"deviceId": "DEV-001", "temp": 25.5, ...}'
result = asyncio.run(service.process_stream(json_data))

# Process binary telemetry
binary_data = b'\x00\x01\x02...'  # Your binary data
result = asyncio.run(service.process_stream(binary_data))
```

#### Querying Historical Data
```python
from datetime import datetime, timedelta

# Query last hour of data for specific device
end_time = datetime.now()
start_time = end_time - timedelta(hours=1)

data = service.database.query(
    device_id="DEV-001",
    start_time=start_time,
    end_time=end_time
)
```

## Architecture

### Components

1. **Parsers**: Format-specific parsers (JSON, Binary)
2. **Processor**: Central processing unit for normalization
3. **Database**: In-memory time-series storage
4. **Analytics Engine**: Real-time analysis and alerting
5. **Integration Service**: Main orchestration layer

### Data Flow
```
Raw Telemetry → Parser → Processor → Unified Format → Database
                                    ↓
                              Analytics Engine
                                    ↓
                              Alerts & Insights
```

## Output Example

```
================================================================================
DAIKIBO INDUSTRIALS - IIoT TELEMETRY INTEGRATION DASHBOARD
================================================================================
Timestamp: 2025-09-02T12:05:45.123456+00:00

Processing Statistics:
  - Total Processed: 142
  - Errors: 0
  - Error Rate: 0.00%

Format Distribution:
  - json: 71
  - binary: 71

Average Metrics:
  - temperature: 22.34
  - pressure: 101.25
  - humidity: 55.67
  - vibration: 4.82
  - power_consumption: 285.43

Active Devices: 28

Recent Alerts:
  - [2025-09-02T12:05:40.123456+00:00] HIGH_TEMP: Device DEV-042
  - [2025-09-02T12:05:38.654321+00:00] HIGH_VIBRATION: Device BIN-015
================================================================================
```

## Customization

### Adding New Formats
Extend the `TelemetryParser` class:
```python
class CustomFormatParser(TelemetryParser):
    def validate(self, raw_data):
        # Your validation logic
        pass
    
    def parse(self, raw_data):
        # Your parsing logic
        return TelemetryData(...)
```

### Modifying Alert Thresholds
Edit the `AnalyticsEngine.analyze()` method to adjust thresholds:
```python
if telemetry.metrics.get('temperature', 0) > YOUR_THRESHOLD:
    analysis['anomalies'].append('High temperature detected')
```

## Production Deployment

For production use, consider:
1. Replace in-memory database with persistent storage (InfluxDB, TimescaleDB)
2. Implement MQTT/Kafka for real-time streaming
3. Add authentication and encryption
4. Scale with multiprocessing/distributed computing
5. Implement proper logging and monitoring
6. Add data validation and sanitization
7. Configure appropriate retention policies

## Support

Author: Payalsoni00  
Date: 2025-09-02  
Client: Daikibo Industrials  
Project: IIoT Telemetry Integration

## License

This solution is proprietary to Daikibo Industrials and Deloitte.