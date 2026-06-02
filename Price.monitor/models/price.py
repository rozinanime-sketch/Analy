from datetime import datetime


class PriceRecord:
    def __init__(self, stock_id: int, price: float, datetime_str: str):
        self.stock_id = stock_id
        self.price = price
        self.datetime_str = datetime_str

    @property
    def datetime(self) -> datetime:
        return datetime.fromisoformat(self.datetime_str)

    @property
    def formatted_date(self) -> str:
        return self.datetime.strftime("%d.%m.%Y %H:%M")

    def __repr__(self):
        return f"PriceRecord(stock_id={self.stock_id}, price={self.price}, at={self.formatted_date})"
