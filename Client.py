import pandas as pd
import socket
import json
import sys
from threading import Thread
from Strategies import MA, ZscoreBreak


class Trading_Client:
    def __init__(self, HOST="localhost", PORT=9999, init_capital=1e6, Strategy=None):
        self.HOST = HOST
        self.PORT = PORT
        self.capital = init_capital
        self.set_strategy(Strategy)

    def set_strategy(self, Strategy):
        self.Strategy = Strategy

    def _connect(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as self.sock:
            self.sock.connect((self.HOST, self.PORT))
            while True:
                try:
                    received = str(self.sock.recv(1024), "utf-8")
                    print("Received: {}".format(received))
                    try:
                        rcvd = received.replace("'", '"')
                    except TypeError:
                        print("Not received")
                    rcvd = json.loads(rcvd)
                    self.date = rcvd['Date']
                    self.price = float(rcvd['Close'])
                    order = self.Strategy(received=received, current_capital=self.capital)
                    cash_remain = self.capital
                    if order is not None:
                        self.send_order(order)
                        self.handle_order(order)
                    print(f'Cash:{cash_remain} -> {self.capital}\n')
                except TypeError:
                    break
            sys.exit(0)

    def handle_order(self, order):
        signal = order['Direction']
        amount = order['Amount']
        if signal == 'Buy':
            self.capital -= amount * self.price

        elif signal == 'Sell':
            self.capital += amount * self.price

    def send_order(self, order):
        self.sock.sendall(bytes(str(order), "utf-8"))


if __name__ == "__main__":
    trading = MA(fraction=0.1)

    client = Trading_Client(Strategy=trading.generate_signal)
    client._connect()
