#!/usr/bin/env python3
import csv
import requests
import sys

def check_urls(inventory_file, base_url='http://localhost:5000'):
    results = {'ok': 0, 'fail': 0, 'errors': []}
    
    try:
        with open(inventory_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                old_url = row.get('old_url', '').strip()
                expected_new_url = row.get('new_url', '').strip()
                
                if not old_url:
                    continue
                
                try:
                    full_old_url = base_url + old_url
                    response = requests.get(full_old_url, allow_redirects=False, timeout=5)
                    
                    if old_url.startswith('/catalog/') and old_url != '/catalog/':
                        if response.status_code == 301:
                            location = response.headers.get('Location', '')
                            if expected_new_url and location != expected_new_url:
                                results['errors'].append(f"{old_url}: 301 -> {location} (ожидалось {expected_new_url})")
                                results['fail'] += 1
                            else:
                                new_response = requests.get(base_url + location, timeout=5)
                                if new_response.status_code == 200:
                                    results['ok'] += 1
                                else:
                                    results['errors'].append(f"{old_url}: 301 -> {location} -> {new_response.status_code}")
                                    results['fail'] += 1
                        else:
                            results['errors'].append(f"{old_url}: ожидался 301, получен {response.status_code}")
                            results['fail'] += 1
                    else:
                        if response.status_code in [200, 301]:
                            results['ok'] += 1
                        else:
                            results['errors'].append(f"{old_url}: {response.status_code}")
                            results['fail'] += 1
                            
                except requests.RequestException as e:
                    results['errors'].append(f"{old_url}: {str(e)}")
                    results['fail'] += 1
    
    except FileNotFoundError:
        print(f"Файл {inventory_file} не найден")
        return
    
    print(f"\nРезультаты проверки:")
    print(f"OK: {results['ok']}")
    print(f"Ошибки: {results['fail']}")
    
    if results['errors']:
        print("\nОшибки:")
        for err in results['errors'][:20]:
            print(f"  - {err}")
        if len(results['errors']) > 20:
            print(f"  ... и ещё {len(results['errors']) - 20} ошибок")


if __name__ == '__main__':
    inventory = sys.argv[1] if len(sys.argv) > 1 else 'url_inventory.csv'
    base = sys.argv[2] if len(sys.argv) > 2 else 'http://localhost:5000'
    check_urls(inventory, base)
