from project_proteus.env.base import BaseConfig


class SimpleConfig(BaseConfig):
    
    class database:
        #path to the database
        path = ""
        #which candlestick interval should be used in the environment
        candlestick_interval = ""

    class portfolio:
        #the initial amount of the quote asset
        #example: symbol=BTCUSDT --> initial_amount = amount of USDT in the beginning
        initial_amount = 1000
        #trading fees of the exchange in percent
        trading_fees = 0.036 #[%]

    class env:
        #number of steps the agent can take in the environment before it gets reset
        num_steps = 10

        window_length = 10