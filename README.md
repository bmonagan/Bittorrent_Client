# BitTorrent Client

A Python implementation of a BitTorrent client that downloads files from peer-to-peer networks using the BitTorrent protocol. This project serves as an educational exploration of how BitTorrent works under the hood.

## Motivation

Existing BitTorrent clients like Transmission, qBittorrent, and Deluge are production-ready but often come with heavy dependencies, complex architectures, and a steep learning curve for understanding the underlying protocol mechanics. Python bindings to libraries like libtorrent are powerful but obscure the implementation details behind C++ abstractions.

The goal of this project is to provide a clean, from-scratch implementation of a BitTorrent client in pure Python that makes the protocol transparent and understandable. Rather than building a fully-featured production client, this implementation prioritizes:

- **Educational Value**: Clear code that demonstrates core BitTorrent concepts
- **Simplicity**: Minimal dependencies and straightforward abstractions
- **Transparency**: Understand exactly how peers are discovered, how pieces are requested, and how downloads are coordinated
- **Async-First Design**: Showcase modern Python async/await patterns for concurrent I/O
- **Modular Architecture**: Clearly separated concerns (bencoding, tracker communication, peer protocol)

## Overview

This BitTorrent client implements the core functionality needed to:
- Parse `.torrent` metafiles
- Connect to BitTorrent trackers
- Discover and communicate with peers
- Download files in a multi-threaded, asynchronous manner
- Verify downloaded pieces using SHA-1 checksums

## Features

### Current Implementation
- ✅ **Torrent Parsing**: Reads and parses `.torrent` files with support for single and multi-file torrents
- ✅ **Tracker Communication**: HTTP/HTTPS tracker discovery and peer list retrieval
- ✅ **Peer Connections**: Asynchronous peer-to-peer connections using the BitTorrent wire protocol
- ✅ **Piece Management**: Strategic piece selection and verification using SHA-1 hashing
- ✅ **Async Downloads**: Multi-peer concurrent downloads with configurable connection pools
- ✅ **CLI Interface**: Command-line interface with verbose logging and tracker inspection tools
- ✅ **Custom Bencoding**: Custom bencode/bdecode implementation for protocol communication

### Planned Features
- 🔄 **Seeding**: Support for uploading (seeding) downloaded content
- 🎨 **GUI**: Graphical user interface for easier usage
- 📝 **Improved Code Quality**: Type hints, docstrings, and code cleanup

## Installation

### Prerequisites
- Python 3.12 or higher
- pip or poetry package manager

### Setup

1. **Clone the repository** (or navigate to the project directory)
```bash
cd Bittorrent_Client
```

2. **Create a virtual environment** (recommended)
```bash
python -m venv .venv
```

3. **Activate the virtual environment**
   - On Windows:
   ```bash
   .venv\Scripts\Activate.ps1
   ```
   - On macOS/Linux:
   ```bash
   source .venv/bin/activate
   ```

4. **Install dependencies**
```bash
pip install -e .
```

Or with poetry:
```bash
poetry install
```

## Usage

### Basic Download

To download a torrent file:

```bash
python -m src.main data/mint.torrent
```

### With Verbose Output

Enable detailed logging to see what's happening:

```bash
python -m src.main data/ubuntu.torrent -v
```

### Inspect Tracker List

View all tracker announce URLs in a torrent file without downloading:

```bash
python -m src.main data/arch.torrent --show-trackers
```

### Probe Trackers

Test tracker connectivity and retrieve initial peer information:

```bash
python -m src.main data/cachyos.torrent --probe-trackers
```

### Available Command-Line Options

- `torrent`: Path to the `.torrent` file to download (required)
- `-v, --verbose`: Enable verbose logging output
- `--show-trackers`: Display all announce URLs and exit
- `--probe-trackers`: Connect to tracker(s) once and display peer info, then exit

## Project Structure

```
src/
├── __init__.py              # Package initialization
├── main.py                  # Entry point and CLI argument handling
├── client.py                # TorrentClient - main downloading logic
├── torrent.py               # Torrent - metadata parsing and management
├── tracker.py               # Tracker/TrackerResponse - tracker communication
├── protocol.py              # PeerConnection - peer wire protocol implementation
├── local_bencoding.py       # Custom bencode/bdecode implementation
└── utils.py                 # Utility functions

data/
└── *.torrent                # Sample torrent files for testing

testing/
├── bencoding_testing.py     # Tests for bencoding module
├── torrent_file_read.py     # Tests for torrent parsing
├── torrent_test.py          # Integration tests
└── udp_test.py              # UDP tracker tests
```

## Architecture

### Core Components

1. **Torrent Parser** (`torrent.py`)
   - Parses `.torrent` metafiles using bencode decoding
   - Extracts metadata: files, piece hashes, announce URLs, info hash
   - Calculates SHA-1 hash of the info dictionary (required for tracker communication)

2. **Tracker Communication** (`tracker.py`)
   - Communicates with HTTP/HTTPS trackers
   - Announces client presence and retrieves peer lists
   - Parses tracker responses in bencode format
   - Handles failure responses and retry logic

3. **Peer Connections** (`protocol.py`)
   - Implements the BitTorrent wire protocol
   - Manages connections to individual peers
   - Handles handshakes, piece requests, and data reception
   - Queues peers for connection and manages connection pooling

4. **Client** (`client.py`)
   - Orchestrates the download process
   - Creates and manages a pool of peer connections
   - Periodically announces to tracker and enqueues new peers
   - Coordinates piece manager and peer workers
   - Handles graceful shutdown

5. **Piece Management** (`client.py`)
   - Tracks which pieces have been downloaded and verified
   - Implements strategic piece selection (rarest-first, progressive)
   - Verifies pieces using SHA-1 checksums
   - Persists downloaded data to disk

6. **Bencode Support** (`local_bencoding.py`)
   - Custom implementation of bencode encoding/decoding
   - Supports integers, strings, lists, and dictionaries
   - Used for protocol communication and custom message formats

## Dependencies

- **aiohttp** (≥3.12.15): Asynchronous HTTP client for tracker communication
- **bencodepy** (≥0.9.5): Bencode encoding/decoding for torrent and tracker protocol
- **bitstring** (≥4.3.1): Bit manipulation utilities for the BitTorrent protocol

## How It Works

### Download Flow

1. **Parse Torrent**: Load and parse the `.torrent` file to extract metadata
2. **Announce to Tracker**: Send announce request to tracker with download status
3. **Receive Peers**: Get list of available peers from tracker
4. **Connect to Peers**: Establish peer connections using BitTorrent wire protocol
5. **Request Pieces**: Request specific pieces/blocks from peers
6. **Verify & Save**: Verify downloaded pieces using SHA-1 and write to disk
7. **Repeat**: Continue requesting pieces until torrent is complete

### BitTorrent Protocol Overview

- **Handshake**: Exchange protocol version and client info with peers
- **Piece Exchange**: Request and receive 16KB blocks of pieces
- **Verification**: Compare downloaded data SHA-1 hash with torrent metadata
- **Status Updates**: Exchange interested/choked status to manage bandwidth

## Development Status

**Current Version**: 0.1.0 (Early Development)

This is an educational project under active development. Core downloading functionality is implemented and working, but the codebase is still being refined with:
- Type hints and docstrings
- Code organization and cleanup
- Error handling improvements
- Performance optimizations

## Testing

Sample torrent files are included in the `data/` directory for testing:
- `mint.torrent` - Linux Mint distribution
- `ubuntu.torrent` - Ubuntu distribution
- `arch.torrent` - Arch Linux distribution
- `cachyos.torrent` - CachyOS distribution
- `historyofpelo.torrent` - Historical archive
- And others

Test files are available in the `testing/` directory for unit and integration testing.

## Common Issues & Notes

- **Async Session Management**: The tracker communication uses `aiohttp.ClientSession` which must be properly closed. Always ensure the session is closed in exception handlers or via explicit async cleanup.
- **Peer Timeouts**: Some peers may be unreachable or slow; the client includes timeout logic to skip unresponsive peers.
- **Tracker Types**: Currently supports HTTP/HTTPS trackers; UDP tracker support is in testing.

## Contributing

This project welcomes improvements and contributions. Some areas for enhancement:
- Implement UDP tracker support
- Add protocol extension support (PEX, DHT)
- Improve piece selection strategies
- Add upload/seeding capability
- Create a user-friendly GUI


## Resources

- [BitTorrent Specification](http://www.bittorrent.org/beps/bep_0003.html) - Official protocol specification
- [BEP 5 - DHT Protocol](http://www.bittorrent.org/beps/bep_0005.html)
- [BEP 6 - Fast Extension](http://www.bittorrent.org/beps/bep_0006.html)

## Author

bmonagan

---

**Note**: This client is for educational purposes. Ensure you have the right to download any torrents using this client and comply with local laws and regulations.
