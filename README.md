# Pragmatic Play Slot Analyzer

Automated tool for analyzing Pragmatic Play slot game sessions. The project uses Playwright for browser automation, intercepts game requests, and collects spin statistics.

## Overview

This project automates the gameplay of **Gates of Olympus** slot by Pragmatic Play and collects detailed statistics:

- **SpinCollector** — intercepts and parses responses from the game server
- **PlaywrightAsync** — base class for browser automation
- **Pragmatic** — main class managing the gameplay process

### Workflow:

1. Launches browser via Playwright
2. Opens Gates of Olympus demo version
3. Closes popups (cookies, age confirmation)
4. Locates the game iframe
5. Activates autoplay mode
6. Intercepts all requests to `/gameService`
7. Collects statistics for each spin
8. After reaching spin limit (default: 100), saves Excel report

### Generated Statistics:

- Balance (starting, final, peak)
- Wins (count, max, min, frequency)
- Bonuses (Free Spins, first bonus)
- Streaks (longest losing/winning)
- Financial metrics (RTP, total wagered, total returned)
- Hit Rate and LDW (Loss Disguised as Win)

## Installation

### Requirements:

- Python >= 3.12
- Poetry

### Install dependencies:

```bash
poetry install
```

### Install Playwright browsers:

```bash
poetry run playwright install
```

## Usage

### Run the analyzer:

```bash
poetry run python main.py
```

## Project Structure

```
pragmatic/
├── base/
│   └── playwright_async.py    # Base Playwright class
├── loggers/
│   └── logger.py              # Logging configuration
├── services/
│   ├── pragmatic.py           # Main game management class
│   └── spin_manager.py        # Spin collection and analysis
├── sources/
│   └── videos/                # Video recordings (if enabled)
├── logs/                      # Application logs
├── main.py                    # Entry point
├── pyproject.toml             # Poetry configuration
└── spins.xlsx                 # Analysis results
```

## Output

After execution, the following files are generated:

### spins.xlsx
Excel file with two sheets:
1. **Spins** — detailed information for each spin
2. **Analytics** — aggregated session statistics

### sources/videos/
Video recording of the entire session (if video recording is enabled)

## Configuration

### Change spin limit:

In `services/pragmatic.py`:

```python
self.collector = SpinCollector(spin_limit=100)  # Change to desired value
```

### Enable headless mode:

In `services/pragmatic.py`, `execute()` method:

```python
await self.init_browser(headless=True)
```

### Disable video recording:

In `services/pragmatic.py`, `execute()` method:

```python
await self.init_browser(record_video=False)
```
