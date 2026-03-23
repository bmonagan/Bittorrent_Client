import argparse
import asyncio
import signal
import logging

from .torrent import Torrent
from .client import TorrentClient
from .tracker import Tracker


def _log_torrent_summary(torrent: Torrent):
    logging.info('Torrent: %s', torrent.output_file)
    logging.info('Total size: %d bytes', torrent.total_size)
    logging.info('Pieces: %d (piece length: %d bytes)', len(torrent.pieces), torrent.piece_length)
    logging.info('Trackers: %d', len(torrent.announce_urls))


async def async_main():
    parser = argparse.ArgumentParser()
    parser.add_argument('torrent', help='the .torrent to download')
    parser.add_argument("-v","--verbose",action='store_true', help ='enable verbose output')
    parser.add_argument('--show-trackers', action='store_true',
                        help='print announce URLs and exit')
    parser.add_argument('--probe-trackers', action='store_true',
                        help='announce once to tracker(s) and exit')
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.INFO)

    torrent = Torrent(args.torrent)

    if args.show_trackers:
        for idx, url in enumerate(torrent.announce_urls, start=1):
            print(f'{idx}. {url}')
        return 0

    if args.probe_trackers:
        tracker = Tracker(torrent)
        try:
            response = await tracker.connect(first=True, uploaded=0, downloaded=0)
            peer_count = len(response.peers)
            print(f'Tracker probe succeeded: peers={peer_count}, interval={response.interval}')
            return 0
        except (RuntimeError, ConnectionError) as exc:
            logging.error(str(exc))
            return 1
        finally:
            await tracker.close()

            _log_torrent_summary(torrent)

    client = TorrentClient(torrent)
    task = asyncio.create_task(client.start())

    def signal_handler(*_):
        logging.info('Exiting, please wait untill everything is shutdown...')
        client.stop()
        task.cancel()

    signal.signal(signal.SIGINT, signal_handler)

    try:
        await task
        return 0
    except asyncio.CancelledError:
        logging.warning('Event loop was canceled.')
        return 1
    except (RuntimeError, ConnectionError) as exc:
        logging.error(str(exc))
        return 1
    finally:
        await client.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(async_main()))