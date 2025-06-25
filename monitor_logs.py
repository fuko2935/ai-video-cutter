#!/usr/bin/env python3
"""
Log izleme aracı
"""
import sys
import time
import os
from datetime import datetime

def tail_file(filename, lines=20):
    """Dosyanın son satırlarını göster"""
    try:
        with open(filename, 'r') as f:
            content = f.readlines()
            return ''.join(content[-lines:])
    except FileNotFoundError:
        return f"File not found: {filename}"

def monitor_logs():
    """Canlı log izleme"""
    log_files = {
        '1': 'logs/app/debug.log',
        '2': 'logs/errors/errors.log',
        '3': 'logs/api/requests.log',
        '4': 'logs/app/performance.log'
    }
    
    print("Log Monitor - Press Ctrl+C to exit")
    print("=" * 50)
    print("Select log file:")
    for key, value in log_files.items():
        print(f"{key}: {value}")
    
    choice = input("Enter choice (1-4): ")
    log_file = log_files.get(choice, 'logs/app/debug.log')
    
    print(f"\nMonitoring: {log_file}")
    print("=" * 50)
    
    last_size = 0
    
    try:
        while True:
            if os.path.exists(log_file):
                current_size = os.path.getsize(log_file)
                
                if current_size > last_size:
                    with open(log_file, 'r') as f:
                        f.seek(last_size)
                        new_content = f.read()
                        if new_content:
                            print(new_content, end='')
                    last_size = current_size
            
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")

if __name__ == '__main__':
    monitor_logs()