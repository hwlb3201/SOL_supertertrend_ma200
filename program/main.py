import asyncio
import time
from constants import ABORT_ALL_POSITIONS, FIND_COINTEGRATED, PLACE_TRADES, MANAGE_EXITS
from func_connections import connect_dydx
from func_private import get_open_positions,is_open_positions, place_limit_order,Bid_ASK,cancel_order
from func_public import construct_market_prices,supertrend
import pandas as pd
from func_messaging import send_message

send_message("Bot launch successful")

async def bot():
  market='SOL-USD'
  size=0.1
  try:
    print("")
    print("Program started...")
    print("Connecting to Client...")
    client = await connect_dydx()
    print('connect successful')
    print()
  except Exception as e:
    print("Error connecting to client: ", e)
    send_message(f"Failed to connect to client {e}")
    exit(1)
  
    

  Is_position=await is_open_positions(client,market)

 
  if Is_position==True:
      print('There is position')
      position_inf=await get_open_positions(client,market)
      position_side=position_inf[0]  
      unrealizedPnl=float(position_inf[2])
      print(position_side)
      if position_side=="LONG":
           print(f"construct {market} price- Please wait......")
           candle=await construct_market_prices(client,market)
           Strategy=supertrend(candle,7,200,3)
           if Strategy[-1]==0:
                  orderbook=await Bid_ASK(client, market)
                  ask=float(orderbook[1])
                  side = "SELL"
                  await cancel_order(client,market)
                  await place_limit_order(client, market, side, size, ask, False)
                  send_message(f"Square the {position_side} {market} at {ask}, the unrealized is {unrealizedPnl}")
           else: 
                  orderbook=await Bid_ASK(client, market)
                  Stop_price=float(orderbook[1])
                  unrealizedPnl=float(position_inf[2])
                  send_message(f"The unrealized is {unrealizedPnl} and stop loss at {Stop_price}")
      elif position_side=="SHORT":
           print(f"construct {market} price- Please wait......")
           candle=await construct_market_prices(client,market)
           Strategy=supertrend(candle,7,200,3)
           if Strategy[-1]==0:
                  orderbook=await Bid_ASK(client, market)
                  bid=float(orderbook[0])
                  side="BUY"
                  await cancel_order(client,market)
                  await place_limit_order(client, market, side, size, bid, False)
                  send_message(f"Square the {position_side} {market} at {bid}, the unrealized is {unrealizedPnl}")
           else:
                orderbook=await Bid_ASK(client, market)
                Stop_price=float(orderbook[0])
                unrealizedPnl=float(position_inf[2])
                send_message(f"The unrealized is {unrealizedPnl} and stop loss is at {Stop_price} ")                                                                                    
  else:
      print('There is no position')
      print(f"construct {market} price- Please wait......")
      candle=await construct_market_prices(client,market)
      Strategy=supertrend(candle,7,200,3)
      print(Strategy.tail(60))
      if Strategy['trend'][-1]==1:
            orderbook=await Bid_ASK(client, market)
            bid=float(orderbook[0])
            side="BUY"
            await cancel_order(client,market)
            await place_limit_order(client, market, side, size, bid, False)
            send_message(f'Place a Buy order for {market} at {bid}')
      elif Strategy['trend'][-1]==-1:
            orderbook=await Bid_ASK(client, market)
            ask=float(orderbook[1])
            side="SELL"
            await cancel_order(client,market)
            await place_limit_order(client, market, side, size, ask, False)
            send_message(f'Place a Sell order for {market} at {ask}')
      else:
           print(f'There is no signal for either long/Short {market}')
           

      

  time.sleep(1800)


while True:
      try:
           asyncio.run(bot())
      except:
           print('+++++ MAYBE AN INTERNET PROB OR SOMETHING')


    
      
  
