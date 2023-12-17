# Queue class implementation
from queue import Queue
from asyncio import PriorityQueue

import CONFIG
from DataPoint import Request


class PlatformQueue():
    def __init__(self, max_size=CONFIG.N_INITIAL_CAPACITY):
        self.queue = PriorityQueue(max_size)

    def put(self, item):
        if isinstance(item, Request):
            priority = item.priority
        else:
            priority = CONFIG.PRIORITY_DEFAULT

        self.queue.put_nowait((priority, item))

    def put_priority_highest(self, item):
        self.queue.put_nowait((0, item))

    def get(self):
        data = self.queue.get_nowait()[1]
        return data

    def size(self):
        return self.queue.qsize()

    def is_empty(self):
        return self.queue.empty()

    def is_full(self):
        return self.queue.full()
