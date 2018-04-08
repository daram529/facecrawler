from crawler_engine_abc import CrawlerEngine
from insta_crawler import InstagramCrawlerEngine, BetterDriver
from threading import Thread, Event
import os
import signal
import queue
import time
import argparse


class Crawler:
    """
    Crawler system class. Comprises all modules required for crawling.
    """
    def __init__(self, crawler_engine_cls, webdriver_cls, hash_tag, num_workers):
        if not issubclass(crawler_engine_cls, CrawlerEngine):
            raise self.CrawlerEngineMismatchError
        self.crawler_engine_cls = crawler_engine_cls
        self.webdriver_cls = webdriver_cls
        self.hash_tag = hash_tag
        self.stopper = Event()

        # create worker threads
        self.workers = self.create_workers(num_workers)

        # end gracefully upon Ctrl+C
        handler = SignalHandler(self.stopper, self.workers)
        signal.signal(signal.SIGINT, handler)


    def create_workers(self, num_workers=1):
        """
        Args:
            num_workers (int): number of workers

        Returns:
            workers (set[Thread]): set of workers
        """

        # create workers
        workers = set()
        for _ in range(num_workers):
            if issubclass(self.crawler_engine_cls, Thread):
                crawler_engine_inst = self.crawler_engine_cls(
                        self.webdriver_cls(),
                        hash_tag=self.hash_tag,
                        thread_stopper=self.stopper)
                workers.add(crawler_engine_inst)
            else:
                workers.add(Thread(
                    target=self.crawler_engine_cls(self.webdriver_cls()),
                    kwargs={
                        'hash_tag': self.hash_tag
                    }))
        return workers

    def start(self):
        """
        Start crawling.
        """
        for i, worker in enumerate(self.workers):
            worker.start()
            print('Worker {} started'.format(i))
        print('Logger thread started')

    def close(self):
        """
        Stop crawling and close any additional running functionalities.
        """
        if self.logger is not None:
            logger.close()

    class CrawlerEngineMismatchError(Exception):
        """
        Exception indicating that crawler engine is not type of CrawlerEngine.
        """
        def __init__(self, message=''):
            self.message = message


class SignalHandler:
    """
    Signal handler for crawler.
    """
    def __init__(self, stopper: Event, workers):
        self.stopper = stopper
        self.workers = workers

    def __call__(self, signum, frame):
        print('SIGINT received')
        self.stopper.set()  # set stop thread event

        for worker in self.workers:
            worker.join()


if __name__ == '__main__':
    # parse arguments
    argparser = argparse.ArgumentParser(description='Facecrawler')
    argparser.add_argument('-t', '--nthread', type=int, default=1, help='number of worker threads')
    argparser.add_argument('-H', '--hashtag', type=str, default="samsung", help="hashtag")
    args = argparser.parse_args()

    # create a crawler and start crawling
    crawler = Crawler(
            crawler_engine_cls=InstagramCrawlerEngine,
            webdriver_cls=BetterDriver,
            num_workers=args.nthread,
            hash_tag=args.hashtag)
    crawler.start()
