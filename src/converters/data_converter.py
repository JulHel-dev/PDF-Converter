"""
Data Format Converter

Handles data format conversions.
Supported: JSON ↔ YAML ↔ XML ↔ CSV
"""
import os
import json
import csv
from typing import Optional, Dict, Any
from src.converters.base_converter import BaseConverter


class DataConverter(BaseConverter):
    """
    Handles data format conversions.
    
    Supported: JSON ↔ YAML ↔ XML ↔ CSV
    """
    
    def __init__(self):
        super().__init__()
        self.supported_input_formats = ['json', 'yaml', 'yml', 'xml', 'csv']
        self.supported_output_formats = ['json', 'yaml', 'yml', 'xml', 'csv', 'txt']
    
    def convert(self, input_path: str, output_path: str, output_format: str) -> bool:
        """Convert data format to target format."""
        timer_id = self.monitor.start_timer('data_conversion')
        
        try:
            # Step 1: Validate
            self.monitor.log_event('conversion_start', {
                'input': input_path,
                'output_format': output_format,
                'output_path': output_path
            }, severity='INFO', step='Step 1/4: Validating input')
            
            if not self.validate_input(input_path):
                return False
            
            if not self.validate_output(output_path):
                return False
            
            # Step 2: Load and parse data
            self.monitor.log_event('data_load', {
                'input': input_path
            }, severity='INFO', step='Step 2/4: Loading data')
            
            from src.utils.format_detector import detect_format
            input_format = detect_format(input_path)
            
            data = self._load_data(input_path, input_format)
            
            if data is None:
                return False
            
            # Step 3: Convert to target format
            self.monitor.log_event('format_conversion', {
                'output_format': output_format
            }, severity='INFO', step='Step 3/4: Converting to target format')
            
            result = self._write_output(data, output_path, output_format)
            
            # Step 4: Complete
            self.monitor.log_event('conversion_complete', {
                'input': input_path,
                'output': output_path,
                'success': result
            }, severity='INFO', step='Step 4/4: Conversion complete')
            
            return result
            
        except Exception as e:
            self.monitor.log_event('conversion_failed', {
                'input': input_path,
                'output_format': output_format,
                'error': str(e),
                'error_type': type(e).__name__
            }, severity='ERROR')
            return False
        finally:
            self.monitor.end_timer(timer_id)
    
    def _load_data(self, file_path: str, format: str) -> Optional[Any]:
        """Load data from file based on format."""
        try:
            if format == 'json':
                return self._load_json(file_path)
            elif format in ['yaml', 'yml']:
                return self._load_yaml(file_path)
            elif format == 'xml':
                return self._load_xml(file_path)
            elif format == 'csv':
                return self._load_csv(file_path)
            else:
                self.monitor.log_event('unsupported_input_format', {
                    'format': format
                }, severity='ERROR')
                return None
                
        except Exception as e:
            self.monitor.log_event('data_load_failed', {
                'file': file_path,
                'format': format,
                'error': str(e)
            }, severity='ERROR')
            return None
    
    def _load_json(self, file_path: str) -> Optional[Any]:
        """Load JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _load_yaml(self, file_path: str) -> Optional[Any]:
        """Load YAML file."""
        try:
            import yaml
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
                
        except ImportError:
            self.monitor.log_event('dependency_missing', {
                'library': 'PyYAML',
                'install_command': 'pip install PyYAML'
            }, severity='ERROR')
            return None
    
    def _load_xml(self, file_path: str) -> Optional[Any]:
        """Load XML file and convert to dict."""
        try:
            import xml.etree.ElementTree as ET
            
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            def element_to_dict(element):
                """Recursively convert XML element to dict."""
                result = {}
                
                # Add attributes
                if element.attrib:
                    result['@attributes'] = element.attrib
                
                # Add text content
                if element.text and element.text.strip():
                    result['@text'] = element.text.strip()
                
                # Add children
                for child in element:
                    child_data = element_to_dict(child)
                    
                    if child.tag in result:
                        # Multiple elements with same tag - make it a list
                        if not isinstance(result[child.tag], list):
                            result[child.tag] = [result[child.tag]]
                        result[child.tag].append(child_data)
                    else:
                        result[child.tag] = child_data
                
                return result
            
            return {root.tag: element_to_dict(root)}
            
        except Exception as e:
            self.monitor.log_event('xml_parse_failed', {
                'file': file_path,
                'error': str(e)
            }, severity='ERROR')
            return None
    
    def _load_csv(self, file_path: str) -> Optional[Any]:
        """Load CSV file as list of dictionaries."""
        data = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(dict(row))
        
        return data
    
    def _write_output(self, data: Any, output_path: str, format: str) -> bool:
        """Write data to target format."""
        format = format.lower()
        
        try:
            if format == 'json':
                return self._write_json(data, output_path)
            elif format in ['yaml', 'yml']:
                return self._write_yaml(data, output_path)
            elif format == 'xml':
                return self._write_xml(data, output_path)
            elif format == 'csv':
                return self._write_csv(data, output_path)
            elif format == 'txt':
                return self._write_text(data, output_path)
            else:
                self.monitor.log_event('unsupported_output_format', {
                    'format': format
                }, severity='ERROR')
                return False
                
        except Exception as e:
            self.monitor.log_event('output_write_failed', {
                'format': format,
                'error': str(e)
            }, severity='ERROR')
            return False
    
    def _write_json(self, data: Any, output_path: str) -> bool:
        """Write data as JSON."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    
    def _write_yaml(self, data: Any, output_path: str) -> bool:
        """Write data as YAML."""
        try:
            import yaml
            
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            
            return True
            
        except ImportError:
            self.monitor.log_event('dependency_missing', {
                'library': 'PyYAML',
                'install_command': 'pip install PyYAML'
            }, severity='ERROR')
            return False
    
    def _write_xml(self, data: Any, output_path: str) -> bool:
        """Write data as XML."""
        try:
            import xml.etree.ElementTree as ET
            from xml.dom import minidom
            
            def dict_to_element(tag, data):
                """Convert dict to XML element."""
                element = ET.Element(tag)
                
                if isinstance(data, dict):
                    # Handle attributes
                    if '@attributes' in data:
                        for key, value in data['@attributes'].items():
                            element.set(key, str(value))
                    
                    # Handle text content
                    if '@text' in data:
                        element.text = str(data['@text'])
                    
                    # Handle child elements
                    for key, value in data.items():
                        if key not in ['@attributes', '@text']:
                            if isinstance(value, list):
                                for item in value:
                                    child = dict_to_element(key, item)
                                    element.append(child)
                            else:
                                child = dict_to_element(key, value)
                                element.append(child)
                
                elif isinstance(data, list):
                    # If data is a list at root, wrap in container
                    for item in data:
                        child = dict_to_element('item', item)
                        element.append(child)
                
                else:
                    # Simple value
                    element.text = str(data)
                
                return element
            
            # Get root tag
            if isinstance(data, dict) and len(data) == 1:
                root_tag = list(data.keys())[0]
                root = dict_to_element(root_tag, data[root_tag])
            else:
                root = dict_to_element('root', data)
            
            # Pretty print XML
            xml_str = ET.tostring(root, encoding='unicode')
            pretty_xml = minidom.parseString(xml_str).toprettyxml(indent='  ')
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(pretty_xml)
            
            return True
            
        except Exception as e:
            self.monitor.log_event('xml_write_failed', {
                'error': str(e)
            }, severity='ERROR')
            return False
    
    def _write_csv(self, data: Any, output_path: str) -> bool:
        """Write data as CSV."""
        try:
            # Convert data to list of dictionaries if needed
            if isinstance(data, dict):
                # If dict, try to find a list inside it
                for value in data.values():
                    if isinstance(value, list):
                        data = value
                        break
                else:
                    # If no list found, wrap dict in list
                    data = [data]
            
            if not isinstance(data, list) or not data:
                self.monitor.log_event('csv_conversion_warning', {
                    'message': 'Data is not in list format suitable for CSV'
                }, severity='WARNING')
                return False
            
            # Flatten nested structures for CSV
            flat_data = []
            for item in data:
                if isinstance(item, dict):
                    flat_item = {}
                    for key, value in item.items():
                        if isinstance(value, (dict, list)):
                            flat_item[key] = json.dumps(value)
                        else:
                            flat_item[key] = value
                    flat_data.append(flat_item)
                else:
                    flat_data.append({'value': str(item)})
            
            # Write CSV
            if flat_data:
                with open(output_path, 'w', encoding='utf-8', newline='') as f:
                    fieldnames = flat_data[0].keys()
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(flat_data)
            
            return True
            
        except Exception as e:
            self.monitor.log_event('csv_write_failed', {
                'error': str(e)
            }, severity='ERROR')
            return False
    
    def _write_text(self, data: Any, output_path: str) -> bool:
        """Write data as formatted text."""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(data, indent=2, ensure_ascii=False))
        return True
