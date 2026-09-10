import os


# Integration tests assert against the deterministic synthetic seed dataset.
# Keep that fixture source explicit while the demo application uses Comtrade.
os.environ["TRADE_DATA_SOURCE"] = "Development Trade Data"
