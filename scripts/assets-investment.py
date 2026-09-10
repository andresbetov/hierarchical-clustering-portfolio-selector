"""Legacy entrypoint kept for backwards compatibility with docs and habits.

Thin wrapper: all logic lives in portfolio_engine.cli (installable package).
"""

from portfolio_engine.cli import main

if __name__ == "__main__":
    main()
