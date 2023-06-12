import numpy as np
import json
from collections import deque

class MA:
    def __init__(self,fraction = 0.1):
        self.window_50 = deque()
        self.window_20 = deque()
        self.MA50 = [0 for i in range(49)]
        self.MA20 = [0 for i in range(49)]
        self.fraction = fraction

    def update_window50(self,price):
        if len(self.window_50) < 50:
            self.window_50.append(price)
        else:
            self.window_50.popleft()
            self.window_50.append(price)

    def update_window20(self,price):
        if len(self.window_20) < 20:
            self.window_20.append(price)
        else:
            self.window_20.popleft()
            self.window_20.append(price)

    def Signal_Changed(self):
        self.MA50.append(np.average(self.window_50))
        self.MA20.append(np.average(self.window_20))
        current_signal = np.average(self.window_50) < np.average(self.window_20)
        return current_signal != self.signal

    def generate_signal(self,received,current_capital):
        try:
            received = received.replace("'",'"')
        except TypeError:
            pass
        received = json.loads(received)
        time = received['Date']
        price = float(received['Close'])
        current_holdings = float(received['Holdings'])
        self.update_window20(price)
        self.update_window50(price)

        if len(self.window_50) < 50 or len(self.window_20) < 20:
            order = None
        else:
            if self.Signal_Changed():
                print('Signal Changed!')
                if np.average(self.window_50) < np.average(self.window_20):
                    order = {'Direction': 'Sell', 'Amount':current_holdings}
                else:
                    order = {'Direction': 'Buy', 'Amount':self.fraction * current_capital / price}
            else:
                order = None
        self.signal = np.average(self.window_50) < np.average(self.window_20)
        return order

class ZscoreBreak:
    def __init__(self, window=60, entry_threshold=1.0, exit_threshold=0, fraction=0.1):
        self.window = window
        self.entry_threshold = entry_threshold
        self.exit_threshold = exit_threshold
        self.data = deque()
        self.fraction = fraction

    def update_price(self, price):
        if len(self.data) < self.window:
            self.data.append(price)
        else:
            self.data.popleft()
            self.data.append(price)

    def generate_signal(self, received, current_capital):
        try:
            received = received.replace("'",'"')
        except TypeError:
            pass
        received = json.loads(received)
        time = received['Date']
        price = float(received['Close'])
        current_holdings = float(received['Holdings'])

        self.update_price(price)

        if len(self.data) < self.window:
            order = None
            return order

        # Calculate moving average
        data_mavg = np.average(self.data)

        # Calculate spread
        data_spread = self.data - data_mavg

        # Calculate z-score with a rolling window
        data_zscore = (data_spread - np.average(data_spread)) / np.std(data_spread)

        # Generate trading signals
        last_row = data_zscore[-1]
        if last_row < -self.entry_threshold:
            order = {'Direction': 'Buy', 'Amount': self.fraction * current_capital / price}
        elif last_row * data_zscore[-2] < 0:  # z_score crossed zero
            order = {'Direction': 'Sell', 'Amount': current_holdings}
        else:
            order = None

        return order