import pyartnet
import time
import threading
import numpy as np


class ArtNetController:
    def __init__(self, config):
        self.ip = config["ip"]
        self.rows = config["rows"]
        self.columns = config["columns"]
        self.universes = (self.rows * self.columns * 3) // 512 + 1
        self.running = False
        self.fade_speed = 0.1
        self.artnet = pyartnet.ArtNetNode(self.ip)
        self.setup_universes()

    def setup_universes(self):
        self.universe_channels = []
        for u in range(self.universes):
            universe = self.artnet.add_universe(u)
            channels = universe.add_channel(start=0, width=min(512, (self.rows * self.columns * 3) - u * 512))
            self.universe_channels.append(channels)

    def send_frame(self, frame):
        for u in range(self.universes):
            start_idx = u * 512
            end_idx = min(start_idx + 512, len(frame))
            self.universe_channels[u].set_values(frame[start_idx:end_idx], fade_time=self.fade_speed)

    def run_effect(self):
        self.running = True
        hue = 0
        direction = 1
        while self.running:
            frame = np.zeros(self.rows * self.columns * 3, dtype=np.uint8)

            if direction == 1:
                for col in range(self.columns):
                    hue = (hue + 5) % 256
                    color = self.hsv_to_rgb(hue, 255, 255)
                    for row in range(self.rows):
                        led_idx = (row * self.columns + col) * 3
                        frame[led_idx:led_idx + 3] = color
                    self.send_frame(frame)
                    time.sleep(0.05)
                direction = -1
            else:
                for row in range(self.rows):
                    hue = (hue + 5) % 256
                    color = self.hsv_to_rgb(hue, 255, 255)
                    for col in range(self.columns):
                        led_idx = (row * self.columns + col) * 3
                        frame[led_idx:led_idx + 3] = color
                    self.send_frame(frame)
                    time.sleep(0.05)
                direction = 1

    def hsv_to_rgb(self, h, s, v):
        f = lambda n: int(v * (1 - s * max(0, min(n, 4 - n, 1))))
        return [f(n) for n in (5 + h / 43, 3 + h / 43, 1 + h / 43)]

    def start(self):
        self.thread = threading.Thread(target=self.run_effect, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        self.thread.join()
