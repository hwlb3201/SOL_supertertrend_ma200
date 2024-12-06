from constants import RESOLUTION
from func_utils import get_ISO_times
import pandas as pd
import numpy as np
import time





from pprint import pprint

# Get relevant time periods for ISO from and to
ISO_TIMES = get_ISO_times()

# Get Recent Candles
async def get_candles_recent(client, market):

  # Define output
  close_prices = []

  # Protect API
  time.sleep(0.2)

  # Get Prices from DYDX V4
  response = await client.indexer.markets.get_perpetual_market_candles(
    market = market, 
    resolution = RESOLUTION
  )

  # Candles
  candles = response

  # Structure data
  for candle in candles["candles"]:
    close_prices.append(candle["close"])

  # Construct and return close price series
  close_prices.reverse()
  prices_result = np.array(close_prices).astype(np.float64)
  return prices_result


# Get Historical Candles
async def get_candles_historical(client, market):

  # Define output
  data = []

  # Extract historical price data for each timeframe
  for timeframe in ISO_TIMES.keys():

    # Confirm times needed
    tf_obj = ISO_TIMES[timeframe]
    from_iso = tf_obj["from_iso"] + ".000Z"
    to_iso = tf_obj["to_iso"] + ".000Z"

    # Protect rate limits
    time.sleep(0.2)

    response = await client.indexer.markets.get_perpetual_market_candles(
      market = market, 
      resolution = RESOLUTION, 
      from_iso = from_iso,
      to_iso = to_iso,
      limit = 100
    )

    candles = response

    # Structure data
    for candle in candles["candles"]:
      data.append({"datetime": candle["startedAt"],"Open":candle['open'],"High":candle['high'],'Low':candle['low'],"Close":candle['close'],'Volume': candle['usdVolume'] })

  # Construct and return DataFrame
  return data




# Construct market prices
async def construct_market_prices(client,market):

  # Set initial DateFrame
  data = await get_candles_historical(client, market)
  df = pd.DataFrame(data)
  df['datetime']=df['datetime'].str.replace('.000Z','')
  df['datetime']=df['datetime'].str.replace('T',' ')
  df.set_index("datetime", inplace=True)
  df.index=pd.to_datetime(df.index)
  df=df.sort_index()
  df.Open=df.Open.astype(float)
  df.High=df.High.astype(float)
  df.Low=df.Low.astype(float)
  df.Close=df.Close.astype(float)
  df.Volume=df.Volume.astype(float)


  return df


def supertrend(df,period,ma_period,atr_multiplier):
      df['Pc']=df['Close'].shift(1)
      df['H-L']=abs(df['High']-df['Low'])
      df['H-Pc']=abs(df['High']-df['Pc'])
      df['L-Pc']=abs(df['Low']-df['Pc'])
      df['tr']=df[['H-L','H-Pc','L-Pc']].max(axis=1)
      df['atr']=df['tr'].rolling(period).mean()
      avg=(df['High']+df['Low'])/2
      df['upperband']=avg+(atr_multiplier*df['atr'])
      df['lowerband']=avg-(atr_multiplier*df['atr'])
      df[f'MA_{ma_period}']=df['Close'].rolling(ma_period).mean()
      df['trend']=0
      for current in range(1,len(df.index)):
            previous=current-1
            if df['Close'][current]>df[f'MA_{ma_period}'][current]:
                  if df['Close'][current]>df['upperband'][previous]:
                        df['trend'][current]=1
                  elif df['Close'][current]<df['lowerband'][previous]:
                        df['trend'][current]=0
                  else:
                        if df['trend'][previous]==-1:
                             df['trend'][current]=0
                        else:     
                             df['trend'][current]=df['trend'][previous]
                             if df['trend'][current]==1 and df['lowerband'][current]<df['lowerband'][previous]:
                                  df['lowerband'][current]=df['lowerband'][previous]
                             if df['trend'][current]==0 and df['upperband'][current]>df['upperband'][previous]:
                                  df['upperband'][current]=df['upperband'][previous]              
            if df['Close'][current]<df[f'MA_{ma_period}'][current]:
                  if df['Close'][current]<df['lowerband'][previous]:
                        df['trend'][current]=-1
                  elif df['Close'][current]>df['upperband'][previous]:
                        df['trend'][current]=0
                  else:
                        if df['trend'][previous]==1:
                             df['trend'][current]=0
                        else:
                             df['trend'][current]=df['trend'][previous]
                             if df['trend'][current]==-1 and df['upperband'][current]>df['upperband'][previous]:
                                  df['upperband'][current]=df['upperband'][previous]
                             if df['trend'][current]==0 and df['lowerband'][current]<df['lowerband'][previous]:
                                  df['lowerband'][current]=df['lowerband'][previous]                   
      return df
