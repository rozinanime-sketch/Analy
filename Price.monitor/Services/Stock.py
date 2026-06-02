import yfinance as yf


class StockParser:
    def get_price(self, ticker: str) -> float:
        try:
            stock = yf.Ticker(ticker)
            data = stock.history(period="1d")
            if not data.empty:
                return round(data['Close'].iloc[-1], 2)
            return 0.0
        except Exception as e:
            print(f"Ошибка при получении цены для {ticker}: {e}")
            return 0.0

    def get_name(self, ticker: str) -> str:
        try:
            stock = yf.Ticker(ticker)
            info = stock.fast_info
            name = getattr(info, 'display_name', None) or ticker
            return name
        except Exception:
            return ticker