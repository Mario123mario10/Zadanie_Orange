import requests
import time
import json
from datetime import datetime
from jsonschema import validate, ValidationError
import logging
from subprocess import Popen, PIPE
import threading

# Schemat dla JSON
schema = {
    "type": "object",
    "properties": {
        "gS": {"type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+-master_[0-9a-f]{8}$"},
        "aS": {"type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+-master_[0-9a-f]{8}$"},
        "ahS": {"type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+-master_[0-9a-f]{8}$"},
        "iaS": {"type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+-master_[0-9a-f]{8}$"},
        "nS": {"type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+-master_[0-9a-f]{8}$"},
        "lS": {"type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+-master_[0-9a-f]{8}$"}
    },
    "required": ["gS", "aS", "ahS", "iaS", "nS", "lS"]
}

# Ustawienia logowania
logging.basicConfig(filename='log.txt', level=logging.INFO, format='%(message)s')

# Funkcja do sprawdzania API
def check_api(url, total_checks, delay):
    for _ in range(total_checks):
        start_time = time.time()
        try:
            response = requests.get(url)
            round_trip_time = time.time() - start_time
            status_code = response.status_code
            content_type = response.headers.get('Content-Type', '')
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message = f'{current_time} - Czas odpowiedzi: {round_trip_time:.2f} s, Kod statusu: {status_code}, Typ zawartości: {content_type}'

            logging.info(message)
            print(message)

            if status_code == 200 and 'json' in content_type:
                try:
                    data = response.json()
                    validate(instance=data, schema=schema)
                    success_message = f'{current_time} - JSON jest prawidłowy i zgodny ze schematem.'
                    logging.info(success_message)
                    print(success_message)
                except json.JSONDecodeError:
                    error_message = f'{current_time} - Błąd przy dekodowaniu JSON.'
                    logging.error(error_message)
                    print(error_message)
                except ValidationError as ve:
                    error_message = f'{current_time} - Błąd walidacji JSON: {ve}'
                    logging.error(error_message)
                    print(error_message)
            else:
                error_message = f'{current_time} - Nieprawidłowy status odpowiedzi HTTP lub typ zawartości.'
                logging.error(error_message)
                print(error_message)

        except requests.RequestException as e:
            error_message = f'{current_time} - Błąd żądania: {e}'
            logging.error(error_message)
            print(error_message)

        time.sleep(delay)

def measure_ping(host, delay, running_event):
# Funkcja do pomiaru pingu (zadanie dodatkowe)

    ping_count = 0
    sent_packets = 0
    received_packets = 0
    lost_packets = 0
    min_time = float('inf')
    max_time = 0
    total_time = 0

    while running_event.is_set():
        process = Popen(['ping', '-n', '1', host], stdout=PIPE, stderr=PIPE)
        output, error = process.communicate()

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if process.returncode == 0:
            sent_packets += 1
            received_packets += 1
            lines = output.split('\n')
            for line in lines:
                if "time" in line.lower():
                    time_ms = float(line.split('time=')[1].split('ms')[0].strip())
                    min_time = min(min_time, time_ms)
                    max_time = max(max_time, time_ms)
                    total_time += time_ms
                    ping_message = f'{current_time} - Ping do {host}: {time_ms*1000:.2f} ms'
        else:
            sent_packets += 1
            lost_packets += 1
            ping_message = f'{current_time} - Ping do {host}: Brak odpowiedzi'
        ping_count += 1

        logging.info(ping_message)
        print(ping_message)
        time.sleep(delay)

    avg_time = total_time / received_packets if received_packets > 0 else 0
    report = (f"Ping statistics for {host}:\n"
              f"Packets: Sent = {sent_packets}, Received = {received_packets}, "
              f"Lost = {lost_packets} ({lost_packets/sent_packets*100:.0f}% loss),\n"
              f"Approximate round trip times in milli-seconds:\n"
              f"Minimum = {min_time:.2f}ms, Maximum = {max_time:.2f}ms, Average = {avg_time:.2f}ms")

    logging.info(report)
    print(report)

# Parametry
url = "https://tvgo.orange.pl/gpapi/status"
total_checks = 10 # X = 10
delay = 5 # Y = 5

# Zmienna warunkowa do kontroli wątku pingu
ping_thread_running = threading.Event()
ping_thread_running.set()

# Watek do pomiaru pingu
ping_thread = threading.Thread(target=measure_ping, args=('tvgo.orange.pl', delay, ping_thread_running))
ping_thread.start()

# Wykonanie sprawdzeń
check_api(url, total_checks, delay)

#Zakonczenie watku mierzacego ping
ping_thread_running.clear()
ping_thread.join()