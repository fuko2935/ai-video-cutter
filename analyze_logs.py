#!/usr/bin/env python3
"""
Log analiz aracı
"""
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime

def analyze_performance_logs(log_file='logs/app/performance.log'):
    """Performance loglarını analiz et"""
    durations = defaultdict(list)
    
    try:
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if 'message' in data and 'duration' in data:
                        func_name = data['message']
                        duration = data['duration']
                        durations[func_name].append(duration)
                except:
                    continue
        
        print("\n=== Performance Analysis ===")
        print(f"{'Function':<40} {'Calls':<10} {'Avg(s)':<10} {'Min(s)':<10} {'Max(s)':<10}")
        print("-" * 80)
        
        for func, times in sorted(durations.items()):
            avg_time = sum(times) / len(times)
            print(f"{func:<40} {len(times):<10} {avg_time:<10.3f} {min(times):<10.3f} {max(times):<10.3f}")
            
    except FileNotFoundError:
        print(f"Performance log file not found: {log_file}")

def analyze_errors(log_file='logs/errors/errors.log'):
    """Error loglarını analiz et"""
    errors = Counter()
    
    try:
        with open(log_file, 'r') as f:
            content = f.read()
            
        error_blocks = content.split('-' * 80)
        
        for block in error_blocks:
            if 'ERROR' in block:
                lines = block.strip().split('\n')
                if lines:
                    error_type = lines[0].split('-')[-1].strip() if '-' in lines[0] else 'Unknown'
                    errors[error_type] += 1
        
        print("\n=== Error Analysis ===")
        print(f"{'Error Type':<50} {'Count':<10}")
        print("-" * 60)
        
        for error, count in errors.most_common():
            print(f"{error[:50]:<50} {count:<10}")
            
    except FileNotFoundError:
        print(f"Error log file not found: {log_file}")

def analyze_api_requests(log_file='logs/api/requests.log'):
    """API request loglarını analiz et"""
    endpoints = Counter()
    status_codes = Counter()
    
    try:
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if 'path' in data:
                        endpoints[data['path']] += 1
                    if 'status_code' in data:
                        status_codes[data['status_code']] += 1
                except:
                    continue
        
        print("\n=== API Request Analysis ===")
        print(f"{'Endpoint':<40} {'Requests':<10}")
        print("-" * 50)
        
        for endpoint, count in endpoints.most_common(10):
            print(f"{endpoint:<40} {count:<10}")
        
        print(f"\n{'Status Code':<15} {'Count':<10}")
        print("-" * 25)
        
        for code, count in sorted(status_codes.items()):
            print(f"{code:<15} {count:<10}")
            
    except FileNotFoundError:
        print(f"API log file not found: {log_file}")

if __name__ == '__main__':
    print("Log Analyzer")
    print("=" * 80)
    
    analyze_performance_logs()
    analyze_errors()
    analyze_api_requests()