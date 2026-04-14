import jsonpickle
import math
from typing import Dict, List
from datamodel import OrderDepth, UserId, TradingState, Order

# =========================================================
# GLOBALS & CONSTANTS
# =========================================================

# IMPORTANT: Confirm these position limits against the portal.
# These dictate our maximum allowed inventory at any time.
POSITION_LIMITS = {
    'ASH_COATED_OSMIUM': 20,
    'INTARIAN_PEPPER_ROOT': 20
}

class Trader:

    def __init__(self):
        # We define constants for the EMA (Exponential Moving Average) smoothing
        self.SHORT_EMA_ALPHA = 2 / (5 + 1)   # roughly a 5-period EMA
        self.LONG_EMA_ALPHA  = 2 / (20 + 1)  # roughly a 20-period EMA

    def run(self, state: TradingState):
        """
        Takes the current TradingState and returns:
        1. A dict mapping product symbols to a list of Orders
        2. An integer indicating conversion counts (not heavily used in Round 1)
        3. A String representation of the trader state (persisted across iterations)
        """
        result = {}
        conversions = 0
        
        # 1. Deserialize our persistent state
        # We track our EMAs for Pepper Root here.
        trader_state = {
            "pepper_short_ema": None,
            "pepper_long_ema": None
        }
        
        if state.traderData:
            try:
                trader_state = jsonpickle.decode(state.traderData)
            except Exception as e:
                # Fallback to defaults if deserialization fails
                pass

        # 2. Iterate through the order books of the products
        for product in state.order_depths:
            order_depth: OrderDepth = state.order_depths[product]
            orders: List[Order] = []
            
            # Determine best bids and asks safely
            best_bid = max(order_depth.buy_orders.keys()) if len(order_depth.buy_orders) > 0 else None
            best_ask = min(order_depth.sell_orders.keys()) if len(order_depth.sell_orders) > 0 else None
            
            if best_bid is None or best_ask is None:
                continue # Skip if orderbook is empty on one side

            mid_price = (best_bid + best_ask) / 2.0
            current_position = state.position.get(product, 0)
            limit = POSITION_LIMITS.get(product, 20)

            # =========================================================
            # STRATEGY 1: ASH_COATED_OSMIUM (Market Making)
            # =========================================================
            if product == 'ASH_COATED_OSMIUM':
                # Based on our EDA, the median spread is 16. 
                # We want to capture 8 credits on the bid and 8 credits on the ask.
                base_half_spread = 8
                
                # We skew our prices based on our inventory to prevent adverse selection
                # Example: If we hold +5 inventory, our bid drops by 5, and our ask drops by 5
                # This makes us less likely to buy more, and more likely to sell our stock.
                skew = current_position  # Linear skew
                
                our_bid = math.floor(mid_price - base_half_spread - skew)
                our_ask = math.ceil(mid_price + base_half_spread - skew)

                # Determine sizes (quoting 5 is safe based on EDA median execution size)
                bid_size = min(5, limit - current_position)
                ask_size = max(-5, -limit - current_position)

                if bid_size > 0:
                    orders.append(Order(product, our_bid, bid_size))
                if ask_size < 0:
                    orders.append(Order(product, our_ask, ask_size))
                    
                result[product] = orders

            # =========================================================
            # STRATEGY 2: INTARIAN_PEPPER_ROOT (EMA Trend Following)
            # =========================================================
            elif product == 'INTARIAN_PEPPER_ROOT':
                
                # Initialize EMAs if they are None (first iteration)
                if trader_state["pepper_short_ema"] is None:
                    trader_state["pepper_short_ema"] = mid_price
                    trader_state["pepper_long_ema"] = mid_price
                else:
                    # Update EMAs
                    prev_short = trader_state["pepper_short_ema"]
                    prev_long = trader_state["pepper_long_ema"]
                    
                    trader_state["pepper_short_ema"] = (mid_price * self.SHORT_EMA_ALPHA) + (prev_short * (1 - self.SHORT_EMA_ALPHA))
                    trader_state["pepper_long_ema"] = (mid_price * self.LONG_EMA_ALPHA) + (prev_long * (1 - self.LONG_EMA_ALPHA))

                short_ema = trader_state["pepper_short_ema"]
                long_ema = trader_state["pepper_long_ema"]

                # Momentum Crossover Logic
                # If short term EMA is above long term EMA, we are in an uptrend -> BUY
                if short_ema > long_ema:
                    buy_size = limit - current_position
                    if buy_size > 0:
                        # We use a market order (aggressively taking best ask)
                        orders.append(Order(product, best_ask, buy_size))
                
                # If short term EMA drops below long term EMA, downtrend -> SELL
                elif short_ema < long_ema:
                    sell_size = -limit - current_position
                    if sell_size < 0:
                        # Market order taking best bid
                        orders.append(Order(product, best_bid, sell_size))

                result[product] = orders

        # 3. Serialize state for the next iteration
        traderData = jsonpickle.encode(trader_state)
        
        return result, conversions, traderData
