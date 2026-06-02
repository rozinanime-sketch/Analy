class Stock:
    def __init__(self, id: int, ticker: str, name: str, target_price: float, retention_days: int = 30):
        self.id = id
        self.ticker = ticker.upper()
        self.name = name
        self.target_price = target_price
        self.retention_days = retention_days

    def __repr__(self):
        return f"Stock({self.ticker}, target={self.target_price})"


class PriceRecord:
    def __init__(self, stock_id: int, price: float, datetime_str: str):
        self.stock_id = stock_id
        self.price = price
        self.datetime_str = datetime_str