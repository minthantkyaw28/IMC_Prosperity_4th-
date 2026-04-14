import math
from typing import List
from datamodel import OrderDepth, TradingState, Order

# =========================================================
# POSITION LIMITS — confirm against portal before submitting
# =========================================================
POSITION_LIMITS = {
    'ASH_COATED_OSMIUM': 20,
    'INTARIAN_PEPPER_ROOT': 20,
}

class Trader:

    def run(self, state: TradingState):
        result = {}
        conversions = 0
        traderData = ""

        for product, order_depth in state.order_depths.items():
            orders: List[Order] = []
            position = state.position.get(product, 0)
            limit = POSITION_LIMITS.get(product, 20)

            buy_orders  = order_depth.buy_orders   # {price: volume}  volume > 0
            sell_orders = order_depth.sell_orders  # {price: volume}  volume < 0 (negative)

            best_bid = max(buy_orders)  if buy_orders  else None
            best_ask = min(sell_orders) if sell_orders else None

            # =====================================================
            # INTARIAN_PEPPER_ROOT — Aggressive trend entry
            # =====================================================
            # EDA finding: price rises ~1,000 pts every single day (+10%).
            # Best strategy: get to max long (+20) immediately at t=0 by
            # sweeping ALL ask levels. Holding costs nothing; the trend does work.
            # Theoretical PnL on day 0: ~19,850 XIRECs.
            # =====================================================
            if product == 'INTARIAN_PEPPER_ROOT':
                need = limit - position
                if need > 0 and sell_orders:
                    # Sweep ask levels 1→2→3 until we fill all 'need' units.
                    # Place one order priced above the deepest ask so the engine
                    # fills us through all available levels in one shot.
                    ask_prices = sorted(sell_orders.keys())   # ascending
                    deepest_ask = ask_prices[-1]              # worst level we'll pay
                    orders.append(Order(product, deepest_ask, need))

                result[product] = orders

            # =====================================================
            # ASH_COATED_OSMIUM — Market Making
            # =====================================================
            # EDA finding: price is perfectly mean-reverting around ~10,000.
            # Market spread is consistently 16 pts. We quote at half_spread=8
            # (inside the market) to attract fills while keeping strong edge.
            # Wider spreads earn more per fill; backtests show hs=8 > hs=5 > hs=3.
            # Inventory skew shifts both quotes proportionally to our position,
            # reducing the chance of building a one-sided book.
            # =====================================================
            elif product == 'ASH_COATED_OSMIUM':
                if best_bid is None and best_ask is None:
                    result[product] = orders
                    continue

                if best_bid is None:
                    mid = best_ask
                elif best_ask is None:
                    mid = best_bid
                else:
                    mid = (best_bid + best_ask) / 2.0

                half_spread = 8
                # k=0: no inventory skew. Backtests show removing skew increases fills
                # and PnL on all 3 historical days. Osmium is mean-reverting so residual
                # position marks to mid cleanly at end of day — skew only hurts us by
                # pulling quotes away from the market after large fills.
                our_bid = math.floor(mid - half_spread)
                our_ask = math.ceil(mid  + half_spread)

                # Quote size 10: backtest optimum (hs=8, qs=10, k=0).
                # Caps at 10 per side to avoid exhausting capacity in one fill,
                # keeping both sides active throughout the session.
                quote_size = 10
                bid_capacity = min(quote_size, limit - position)
                ask_capacity = min(quote_size, limit + position)

                if bid_capacity > 0:
                    orders.append(Order(product, our_bid,  bid_capacity))
                if ask_capacity > 0:
                    orders.append(Order(product, our_ask, -ask_capacity))

                result[product] = orders

        return result, conversions, traderData
