#!/usr/bin/env python3
"""
Test suite for Daikibo Industrials IIoT Telemetry Integration
"""

import unittest
import json
import struct
from datetime import datetime, timezone
from telemetry_integration import (
    JSONTelemetryParser,
    BinaryTelemetryParser,
    TelemetryProcessor,
    TelemetrySimulator,
    TimeSeriesDatabase,
    TelemetryData,
    DeviceType,
    DataFormat
)

class TestTelemetryParsers(unittest.TestCase):
    """Test telemetry parser functionality"""
    
    def setUp(self):
        self.json_parser = JSONTelemetryParser()
        self.binary_parser = BinaryTelemetryParser()
        self.simulator = TelemetrySimulator()
    
    def test_json_parser_valid_data(self):
        """Test JSON parser with valid data"""
        json_data = self.simulator.generate_json_telemetry()
        self.assertTrue(self.json_parser.validate(json_data))
        
        telemetry = self.json_parser.parse(json_data)
        self.assertIsInstance(telemetry, TelemetryData)
        self.assertEqual(telemetry.raw_format, DataFormat.JSON)
    
    def test_binary_parser_valid_data(self):
        """Test binary parser with valid data"""
        binary_data = self.simulator.generate_binary_telemetry()
        self.assertTrue(self.binary_parser.validate(binary_data))
        
        telemetry = self.binary_parser.parse(binary_data)
        self.assertIsInstance(telemetry, TelemetryData)
        self.assertEqual(telemetry.raw_format, DataFormat.BINARY)
    
    def test_parser_invalid_data(self):
        """Test parsers with invalid data"""
        invalid_json = "not a json"
        self.assertFalse(self.json_parser.validate(invalid_json))
        
        invalid_binary = b"too short"
        self.assertFalse(self.binary_parser.validate(invalid_binary))

class TestTelemetryProcessor(unittest.TestCase):
    """Test telemetry processor functionality"""
    
    def setUp(self):
        self.processor = TelemetryProcessor()
        self.simulator = TelemetrySimulator()
    
    def test_process_json_data(self):
        """Test processing JSON telemetry"""
        json_data = self.simulator.generate_json_telemetry()
        telemetry = self.processor.process(json_data)
        
        self.assertIsNotNone(telemetry)
        self.assertEqual(telemetry.raw_format, DataFormat.JSON)
        self.assertEqual(self.processor.processed_count, 1)
    
    def test_process_binary_data(self):
        """Test processing binary telemetry"""
        binary_data = self.simulator.generate_binary_telemetry()
        telemetry = self.processor.process(binary_data)
        
        self.assertIsNotNone(telemetry)
        self.assertEqual(telemetry.raw_format, DataFormat.BINARY)
    
    def test_process_invalid_data(self):
        """Test processing invalid data"""
        invalid_data = "invalid format"
        telemetry = self.processor.process(invalid_data)
        
        self.assertIsNone(telemetry)
        self.assertEqual(self.processor.error_count, 1)
    
    def test_statistics(self):
        """Test statistics calculation"""
        # Process multiple data points
        for _ in range(5):
            self.processor.process(self.simulator.generate_json_telemetry())
            self.processor.process(self.simulator.generate_binary_telemetry())
        
        stats = self.processor.get_statistics()
        self.assertEqual(stats['processed_count'], 10)
        self.assertIn('json', stats['format_distribution'])
        self.assertIn('binary', stats['format_distribution'])

class TestTimeSeriesDatabase(unittest.TestCase):
    """Test time-series database functionality"""
    
    def setUp(self):
        self.db = TimeSeriesDatabase()
        self.sample_telemetry = TelemetryData(
            timestamp=datetime.now(timezone.utc),
            device_id="TEST-001",
            device_type=DeviceType.SENSOR,
            location="test-location",
            metrics={'temperature': 25.0},
            status="active",
            quality=1.0,
            raw_format=DataFormat.JSON
        )
    
    def test_insert_and_query(self):
        """Test data insertion and querying"""
        self.db.insert(self.sample_telemetry)
        
        results = self.db.query(device_id="TEST-001")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].device_id, "TEST-001")
    
    def test_device_summary(self):
        """Test device summary generation"""
        # Insert multiple data points
        for i in range(3):
            telemetry = TelemetryData(
                timestamp=datetime.now(timezone.utc),
                device_id=f"TEST-{i:03d}",
                device_type=DeviceType.SENSOR,
                location="test-location",
                metrics={'temperature': 25.0},
                status="active",
                quality=1.0,
                raw_format=DataFormat.JSON
            )
            self.db.insert(telemetry)
        
        summary = self.db.get_device_summary()
        self.assertEqual(len(summary), 3)

if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)