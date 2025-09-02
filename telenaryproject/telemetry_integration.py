#!/usr/bin/env python3
"""
Daikibo Industrials IIoT Telemetry Integration System
Author: Payalsoni00
Date: 2025-09-02
Description: Integrates dual-format telemetry streams from manufacturing equipment
"""

import json
import struct
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from enum import Enum
import random
import time
from collections import deque
import threading
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('DaikiboTelemetry')

# ============================================================================
# Data Models
# ============================================================================

class DeviceType(Enum):
    """Types of IIoT devices in Daikibo's infrastructure"""
    SENSOR = "sensor"
    ACTUATOR = "actuator"
    CONTROLLER = "controller"
    GATEWAY = "gateway"

class DataFormat(Enum):
    """Supported telemetry data formats"""
    JSON = "json"
    BINARY = "binary"
    CSV = "csv"
    XML = "xml"

@dataclass
class TelemetryData:
    """Unified telemetry data model"""
    timestamp: datetime
    device_id: str
    device_type: DeviceType
    location: str
    metrics: Dict[str, float]
    status: str
    quality: float  # Data quality score (0-1)
    raw_format: DataFormat
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        result['device_type'] = self.device_type.value
        result['raw_format'] = self.raw_format.value
        return result

# ============================================================================
# Format Parsers
# ============================================================================

class TelemetryParser(ABC):
    """Abstract base class for telemetry parsers"""
    
    @abstractmethod
    def parse(self, raw_data: Union[bytes, str]) -> TelemetryData:
        """Parse raw data into unified TelemetryData format"""
        pass
    
    @abstractmethod
    def validate(self, raw_data: Union[bytes, str]) -> bool:
        """Validate if data can be parsed by this parser"""
        pass

class JSONTelemetryParser(TelemetryParser):
    """Parser for JSON format telemetry (Format 1)"""
    
    def validate(self, raw_data: Union[bytes, str]) -> bool:
        try:
            if isinstance(raw_data, bytes):
                raw_data = raw_data.decode('utf-8')
            json.loads(raw_data)
            return True
        except (json.JSONDecodeError, UnicodeDecodeError):
            return False
    
    def parse(self, raw_data: Union[bytes, str]) -> TelemetryData:
        """Parse JSON telemetry data"""
        if isinstance(raw_data, bytes):
            raw_data = raw_data.decode('utf-8')
        
        data = json.loads(raw_data)
        
        # Map JSON fields to unified format
        return TelemetryData(
            timestamp=datetime.fromisoformat(data.get('ts', datetime.now(timezone.utc).isoformat())),
            device_id=data.get('deviceId', 'unknown'),
            device_type=DeviceType(data.get('type', 'sensor')),
            location=data.get('location', 'unknown'),
            metrics={
                'temperature': data.get('temp', 0.0),
                'pressure': data.get('pressure', 0.0),
                'humidity': data.get('humidity', 0.0),
                'vibration': data.get('vibration', 0.0),
                'power_consumption': data.get('power', 0.0)
            },
            status=data.get('status', 'active'),
            quality=data.get('quality', 1.0),
            raw_format=DataFormat.JSON
        )

class BinaryTelemetryParser(TelemetryParser):
    """Parser for binary format telemetry (Format 2)"""
    
    # Binary format structure:
    # - 4 bytes: timestamp (unix timestamp) - unsigned int
    # - 16 bytes: device_id (null-terminated string)
    # - 1 byte: device_type - unsigned char
    # - 4 bytes: temperature - float
    # - 4 bytes: pressure - float
    # - 4 bytes: humidity - float
    # - 4 bytes: vibration - float
    # - 4 bytes: power - float
    # - 1 byte: status - unsigned char
    # Total: 46 bytes
    
    # IMPORTANT: 16s counts as ONE item in struct.pack, not 16!
    BINARY_FORMAT = '!I16sBfffffB'  # Using network byte order (big-endian) for consistency
    EXPECTED_SIZE = struct.calcsize(BINARY_FORMAT)
    
    def validate(self, raw_data: Union[bytes, str]) -> bool:
        if isinstance(raw_data, str):
            return False
        return len(raw_data) == self.EXPECTED_SIZE
    
    def parse(self, raw_data: bytes) -> TelemetryData:
        """Parse binary telemetry data"""
        unpacked = struct.unpack(self.BINARY_FORMAT, raw_data)
        
        timestamp_unix = unpacked[0]
        device_id = unpacked[1].decode('utf-8').rstrip('\x00')
        device_type = unpacked[2]
        temp = unpacked[3]
        pressure = unpacked[4]
        humidity = unpacked[5]
        vibration = unpacked[6]
        power = unpacked[7]
        status = unpacked[8]
        
        # Map device type
        device_type_map = {0: DeviceType.SENSOR, 1: DeviceType.ACTUATOR, 
                          2: DeviceType.CONTROLLER, 3: DeviceType.GATEWAY}
        
        # Map status
        status_map = {0: 'inactive', 1: 'active', 2: 'warning', 3: 'error'}
        
        return TelemetryData(
            timestamp=datetime.fromtimestamp(timestamp_unix, tz=timezone.utc),
            device_id=device_id,
            device_type=device_type_map.get(device_type, DeviceType.SENSOR),
            location=f"plant-{device_id[:3]}",  # Derive location from device ID
            metrics={
                'temperature': temp,
                'pressure': pressure,
                'humidity': humidity,
                'vibration': vibration,
                'power_consumption': power
            },
            status=status_map.get(status, 'unknown'),
            quality=0.95 if status <= 1 else 0.7,
            raw_format=DataFormat.BINARY
        )

# ============================================================================
# Data Simulators
# ============================================================================

class TelemetrySimulator:
    """Simulates telemetry data streams for testing"""
    
    def __init__(self):
        self.device_counter = 0
        self.locations = ['tokyo-plant-1', 'osaka-plant-2', 'nagoya-plant-3']
    
    def generate_json_telemetry(self) -> str:
        """Generate sample JSON telemetry data"""
        device_id = f"DEV-{self.device_counter:04d}"
        self.device_counter = (self.device_counter + 1) % 100
        
        data = {
            'ts': datetime.now(timezone.utc).isoformat(),
            'deviceId': device_id,
            'type': random.choice(['sensor', 'actuator', 'controller']),
            'location': random.choice(self.locations),
            'temp': 20 + random.uniform(-5, 25),
            'pressure': 100 + random.uniform(-10, 10),
            'humidity': 50 + random.uniform(-20, 30),
            'vibration': random.uniform(0, 10),
            'power': random.uniform(100, 500),
            'status': random.choice(['active', 'active', 'active', 'warning']),
            'quality': random.uniform(0.85, 1.0)
        }
        return json.dumps(data)
    
    def generate_binary_telemetry(self) -> bytes:
        """Generate sample binary telemetry data"""
        device_id = f"BIN-{self.device_counter:04d}".encode('utf-8')
        device_id = device_id.ljust(16, b'\x00')  # Pad to 16 bytes
        self.device_counter = (self.device_counter + 1) % 100
        
        timestamp = int(time.time())
        device_type = random.randint(0, 3)
        temp = 20 + random.uniform(-5, 25)
        pressure = 100 + random.uniform(-10, 10)
        humidity = 50 + random.uniform(-20, 30)
        vibration = random.uniform(0, 10)
        power = random.uniform(100, 500)
        status = random.choices([1, 1, 1, 2], weights=[70, 20, 5, 5])[0]
        
        # Pack data - NOTE: 16s counts as ONE item, so we have 9 total items
        packed_data = struct.pack(
            BinaryTelemetryParser.BINARY_FORMAT,
            timestamp,     # 1. I - unsigned int
            device_id,     # 2. 16s - 16 byte string (counts as ONE item)
            device_type,   # 3. B - unsigned char
            temp,          # 4. f - float
            pressure,      # 5. f - float
            humidity,      # 6. f - float
            vibration,     # 7. f - float
            power,         # 8. f - float
            status         # 9. B - unsigned char
        )
        
        return packed_data

# ============================================================================
# Data Processing Pipeline
# ============================================================================

class TelemetryProcessor:
    """Processes and normalizes telemetry data"""
    
    def __init__(self):
        self.parsers = [JSONTelemetryParser(), BinaryTelemetryParser()]
        self.processed_count = 0
        self.error_count = 0
        self.metrics_buffer = deque(maxlen=1000)  # Buffer for analytics
    
    def process(self, raw_data: Union[bytes, str]) -> Optional[TelemetryData]:
        """Process raw telemetry data and return normalized format"""
        for parser in self.parsers:
            if parser.validate(raw_data):
                try:
                    telemetry = parser.parse(raw_data)
                    self.processed_count += 1
                    self.metrics_buffer.append(telemetry)
                    return telemetry
                except Exception as e:
                    logger.error(f"Error parsing data: {e}")
                    self.error_count += 1
                    return None
        
        logger.warning(f"No parser found for data format")
        self.error_count += 1
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics"""
        if not self.metrics_buffer:
            return {
                'processed_count': self.processed_count,
                'error_count': self.error_count,
                'error_rate': 0,
                'avg_metrics': {},
                'format_distribution': {}
            }
        
        # Calculate average metrics
        avg_metrics = {}
        metric_names = list(self.metrics_buffer[0].metrics.keys())
        
        for metric in metric_names:
            values = [t.metrics.get(metric, 0) for t in self.metrics_buffer]
            avg_metrics[metric] = sum(values) / len(values)
        
        return {
            'processed_count': self.processed_count,
            'error_count': self.error_count,
            'error_rate': self.error_count / max(1, self.processed_count + self.error_count),
            'avg_metrics': avg_metrics,
            'format_distribution': self._get_format_distribution()
        }
    
    def _get_format_distribution(self) -> Dict[str, int]:
        """Get distribution of data formats"""
        distribution = {}
        for telemetry in self.metrics_buffer:
            format_name = telemetry.raw_format.value
            distribution[format_name] = distribution.get(format_name, 0) + 1
        return distribution

# ============================================================================
# Data Storage
# ============================================================================

class TimeSeriesDatabase:
    """Simple in-memory time-series database for telemetry data"""
    
    def __init__(self, retention_hours: int = 24):
        self.data: List[TelemetryData] = []
        self.retention_hours = retention_hours
        self.lock = threading.Lock()
    
    def insert(self, telemetry: TelemetryData):
        """Insert telemetry data"""
        with self.lock:
            self.data.append(telemetry)
            self._cleanup_old_data()
    
    def _cleanup_old_data(self):
        """Remove data older than retention period"""
        cutoff = datetime.now(timezone.utc).timestamp() - (self.retention_hours * 3600)
        self.data = [d for d in self.data if d.timestamp.timestamp() > cutoff]
    
    def query(self, 
              device_id: Optional[str] = None,
              start_time: Optional[datetime] = None,
              end_time: Optional[datetime] = None,
              limit: int = 100) -> List[TelemetryData]:
        """Query telemetry data"""
        with self.lock:
            result = self.data.copy()
            
            if device_id:
                result = [d for d in result if d.device_id == device_id]
            
            if start_time:
                result = [d for d in result if d.timestamp >= start_time]
            
            if end_time:
                result = [d for d in result if d.timestamp <= end_time]
            
            return result[-limit:]
    
    def get_device_summary(self) -> Dict[str, Any]:
        """Get summary statistics by device"""
        with self.lock:
            device_stats = {}
            for telemetry in self.data:
                if telemetry.device_id not in device_stats:
                    device_stats[telemetry.device_id] = {
                        'count': 0,
                        'last_seen': telemetry.timestamp,
                        'status': telemetry.status,
                        'location': telemetry.location
                    }
                stats = device_stats[telemetry.device_id]
                stats['count'] += 1
                if telemetry.timestamp > stats['last_seen']:
                    stats['last_seen'] = telemetry.timestamp
                    stats['status'] = telemetry.status
            
            return device_stats

# ============================================================================
# Real-time Analytics
# ============================================================================

class AnalyticsEngine:
    """Real-time analytics for telemetry data"""
    
    def __init__(self, database: TimeSeriesDatabase):
        self.database = database
        self.alerts = deque(maxlen=100)
    
    def analyze(self, telemetry: TelemetryData) -> Dict[str, Any]:
        """Perform real-time analysis on telemetry data"""
        analysis = {
            'timestamp': telemetry.timestamp.isoformat(),
            'device_id': telemetry.device_id,
            'anomalies': [],
            'alerts': []
        }
        
        # Check for anomalies
        if telemetry.metrics.get('temperature', 0) > 40:
            analysis['anomalies'].append('High temperature detected')
            self._create_alert('HIGH_TEMP', telemetry)
        
        if telemetry.metrics.get('vibration', 0) > 8:
            analysis['anomalies'].append('Excessive vibration detected')
            self._create_alert('HIGH_VIBRATION', telemetry)
        
        if telemetry.quality < 0.8:
            analysis['anomalies'].append('Low data quality')
            self._create_alert('LOW_QUALITY', telemetry)
        
        if telemetry.status in ['warning', 'error']:
            analysis['alerts'].append(f'Device status: {telemetry.status}')
            self._create_alert('DEVICE_STATUS', telemetry)
        
        return analysis
    
    def _create_alert(self, alert_type: str, telemetry: TelemetryData):
        """Create an alert"""
        alert = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'type': alert_type,
            'device_id': telemetry.device_id,
            'location': telemetry.location,
            'details': telemetry.to_dict()
        }
        self.alerts.append(alert)
        logger.warning(f"Alert created: {alert_type} for device {telemetry.device_id}")
    
    def get_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        return list(self.alerts)[-limit:]

# ============================================================================
# Integration Service
# ============================================================================

class TelemetryIntegrationService:
    """Main service for integrating dual-format telemetry streams"""
    
    def __init__(self):
        self.processor = TelemetryProcessor()
        self.database = TimeSeriesDatabase()
        self.analytics = AnalyticsEngine(self.database)
        self.simulator = TelemetrySimulator()
        self.running = False
        self.threads = []
    
    async def process_stream(self, raw_data: Union[bytes, str]) -> Dict[str, Any]:
        """Process a single telemetry data point"""
        # Parse and normalize data
        telemetry = self.processor.process(raw_data)
        
        if telemetry:
            # Store in database
            self.database.insert(telemetry)
            
            # Perform analytics
            analysis = self.analytics.analyze(telemetry)
            
            return {
                'success': True,
                'data': telemetry.to_dict(),
                'analysis': analysis
            }
        else:
            return {
                'success': False,
                'error': 'Failed to parse telemetry data'
            }
    
    def start_simulation(self, duration_seconds: int = 60):
        """Start simulated data streams"""
        self.running = True
        
        # Start JSON stream simulator
        json_thread = threading.Thread(
            target=self._simulate_json_stream,
            args=(duration_seconds,)
        )
        json_thread.start()
        self.threads.append(json_thread)
        
        # Start binary stream simulator
        binary_thread = threading.Thread(
            target=self._simulate_binary_stream,
            args=(duration_seconds,)
        )
        binary_thread.start()
        self.threads.append(binary_thread)
        
        logger.info(f"Started simulation for {duration_seconds} seconds")
    
    def _simulate_json_stream(self, duration: int):
        """Simulate JSON telemetry stream"""
        end_time = time.time() + duration
        while self.running and time.time() < end_time:
            try:
                raw_data = self.simulator.generate_json_telemetry()
                asyncio.run(self.process_stream(raw_data))
                time.sleep(random.uniform(0.5, 2.0))
            except Exception as e:
                logger.error(f"Error in JSON stream simulation: {e}")
    
    def _simulate_binary_stream(self, duration: int):
        """Simulate binary telemetry stream"""
        end_time = time.time() + duration
        while self.running and time.time() < end_time:
            try:
                raw_data = self.simulator.generate_binary_telemetry()
                asyncio.run(self.process_stream(raw_data))
                time.sleep(random.uniform(0.5, 2.0))
            except Exception as e:
                logger.error(f"Error in binary stream simulation: {e}")
    
    def stop(self):
        """Stop the service"""
        self.running = False
        for thread in self.threads:
            thread.join()
        logger.info("Service stopped")
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for dashboard display"""
        return {
            'statistics': self.processor.get_statistics(),
            'recent_alerts': self.analytics.get_alerts(),
            'device_summary': self.database.get_device_summary(),
            'total_devices': len(self.database.get_device_summary()),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

# ============================================================================
# Main Application
# ============================================================================

def print_dashboard(service: TelemetryIntegrationService):
    """Print dashboard information"""
    dashboard = service.get_dashboard_data()
    
    print("\n" + "="*80)
    print("DAIKIBO INDUSTRIALS - IIoT TELEMETRY INTEGRATION DASHBOARD")
    print("="*80)
    print(f"Timestamp: {dashboard['timestamp']}")
    print(f"\nProcessing Statistics:")
    stats = dashboard['statistics']
    print(f"  - Total Processed: {stats['processed_count']}")
    print(f"  - Errors: {stats['error_count']}")
    print(f"  - Error Rate: {stats['error_rate']:.2%}")
    
    if stats.get('format_distribution'):
        print(f"\nFormat Distribution:")
        for fmt, count in stats['format_distribution'].items():
            print(f"  - {fmt}: {count}")
    
    if stats.get('avg_metrics'):
        print(f"\nAverage Metrics:")
        for metric, value in stats['avg_metrics'].items():
            print(f"  - {metric}: {value:.2f}")
    
    print(f"\nActive Devices: {dashboard['total_devices']}")
    
    if dashboard['recent_alerts']:
        print(f"\nRecent Alerts:")
        for alert in dashboard['recent_alerts'][:5]:
            print(f"  - [{alert['timestamp']}] {alert['type']}: Device {alert['device_id']}")
    
    print("="*80)

async def main():
    """Main application entry point"""
    print("Starting Daikibo Industrials IIoT Telemetry Integration System")
    print(f"Author: Payalsoni00")
    print(f"Date: 2025-09-02")
    print("-"*60)
    
    # Initialize service
    service = TelemetryIntegrationService()
    
    # Start simulation
    simulation_duration = 30  # Run for 30 seconds
    service.start_simulation(simulation_duration)
    
    # Monitor progress
    start_time = time.time()
    while time.time() - start_time < simulation_duration:
        await asyncio.sleep(5)
        print_dashboard(service)
    
    # Stop service
    service.stop()
    
    # Final report
    print("\n" + "="*80)
    print("FINAL REPORT")
    print_dashboard(service)
    
    # Export sample data
    sample_data = service.database.query(limit=10)
    if sample_data:
        print("\nSample Processed Data (Last 10 entries):")
        for i, telemetry in enumerate(sample_data[-3:], 1):
            print(f"\n{i}. Device: {telemetry.device_id}")
            print(f"   Location: {telemetry.location}")
            print(f"   Status: {telemetry.status}")
            print(f"   Format: {telemetry.raw_format.value}")
            print(f"   Temperature: {telemetry.metrics.get('temperature', 0):.2f}°C")
            print(f"   Pressure: {telemetry.metrics.get('pressure', 0):.2f} kPa")
    
    print("\nIntegration complete! Both telemetry formats successfully unified.")
    print("System ready for Daikibo Industrials' IIoT infrastructure.")
    return service

if __name__ == "__main__":
    # Run the application
    try:
        service = asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Error running application: {e}")
        import traceback
        traceback.print_exc()