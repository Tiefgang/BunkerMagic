import pyartnet
import asyncio
import time
import threading
import numpy as np


class ArtNetController:
    def __init__(self, config, port=6454):
        self.ip = config["ip"]
        self.rows = config["rows"]
        self.columns = config["columns"]
        self.universes = (self.rows * self.columns * 3) // 512 + 1
        self.running = False
        self.fade_speed = 0.1
        self.artnet = pyartnet.ArtNetNode(self.ip, port, start_refresh_task=False)
        self.setup_universes()

    def setup_universes(self):
        self.universe_channels = []
        for u in range(self.universes):
            universe = self.artnet.add_universe(u)
            channels = universe.add_channel(start=1, width=min(512, (self.rows * self.columns * 3) - u * 512))
            self.universe_channels.append(channels)

    async def send_frame(self, frame):
        for u in range(self.universes):
            start_idx = u * 512
            end_idx = min(start_idx + 512, len(frame))
            await self.universe_channels[u].set_values(frame[start_idx:end_idx])

        for u in range(self.universes):
            await self.universe_channels[u]

    async def run_effect(self):
        self.running = True
        hue = 128
        direction = 1
        while self.running:
            self.artnet.start_refresh()
            print(f"sending artnet to {self.ip}")
            frame = np.zeros(self.rows * self.columns * 3, dtype=np.uint8)

            if direction == 1:
                for col in range(self.columns):
                    hue = (hue + 5) % 256
                    color = self.hsv_to_rgb(hue, 255, 255)
                    for row in range(self.rows):
                        led_idx = (row * self.columns + col) * 3
                        frame[led_idx:led_idx + 3] = color
                    await self.send_frame(frame)
                    time.sleep(0.2)
                direction = -1
            else:
                for row in range(self.rows):
                    hue = (hue + 5) % 256
                    color = self.hsv_to_rgb(hue, 255, 255)
                    for col in range(self.columns):
                        led_idx = (row * self.columns + col) * 3
                        frame[led_idx:led_idx + 3] = color
                    await self.send_frame(frame)
                    time.sleep(0.2)
                direction = 1
            print(f"artnet loop processed")
            self.artnet.stop_refresh()
            self.running = False

    def hsv_to_rgb(self, h, s, v):
        f = lambda n: int(v * (1 - s * max(0, min(n, 4 - n, 1))))
        return [f(n) for n in (5 + h / 43, 3 + h / 43, 1 + h / 43)]

    def start(self):
        asyncio.run(self.run_effect())

    def stop(self):
        self.running = False
