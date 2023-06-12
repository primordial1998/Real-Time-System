import socket
import threading
import csv
import json
import sys
import time


class Server:
    def __init__(self, host, port, data_file_path, wait=0.1):
        self.host = host
        self.port = port
        self.data_file_path = data_file_path
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.lock = threading.Lock()
        self.holding = 0
        self.wait = wait

    def listen(self):
        print('Server Established')
        self.sock.listen(5)
        while True:
            print('Listening for client')
            client, address = self.sock.accept()
            client.settimeout(100)
            threading.Thread(target=self.listen_to_client, args=(client, address)).start()
            threading.Thread(target=self.send_stream_to_client,
                             args=(client, self.send_csv())).start()

    def send_csv(self):
        data = open(self.data_file_path, 'r')
        csv_reader = csv.DictReader(data)
        output = [row for row in csv_reader]
        return output

    def convert_string_to_json(self, string):
        return json.dumps(string)

    def send_stream_to_client(self, client, buffer):
        for i in buffer:
            print(i)
            i['Holdings'] = self.holding # send current holding
            try:
                client.send((self.convert_string_to_json(i) + '\n').encode('utf-8'))
                time.sleep(self.wait)
            except:
                print('End of Streaming')
                return False
        return False

    def listen_to_client(self, client, address):
        while True:
            try:
                data = str(client.recv(1024), "utf-8").replace("'", '"')
                if data:
                    # Set the response to echo back the received data
                    ans = json.loads(data.rstrip('\n\r '))
                    self.handle_client_answer(ans)
                else:
                    print('Client Disconnected')
                    return False
            except:
                print("Unexpected Error:")
                client.close()
                return False

    def handle_client_answer(self, answer):
        print(answer)
        holding = self.holding
        if answer['Direction'] == 'Buy':
            self.holding += answer['Amount']
        elif answer['Direction'] == 'Sell':
            self.holding -= answer['Amount']
        print(f'Holdings:|{holding} -> {self.holding}\n')


if __name__ == '__main__':
    Server = Server('127.0.0.1', 9999, 'AAPL.csv')
    Server.listen()
