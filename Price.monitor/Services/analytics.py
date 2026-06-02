class Analytics:
    def calculate(self, prices: list) -> dict:
        if not prices:
            return None
        return {
            "avg": round(sum(prices) / len(prices), 2),
            "min": min(prices),
            "max": max(prices)
        }