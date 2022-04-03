#standard lirabries import
import random

#external library imports
import numpy as np
import torch

#package imports
from project_proteus.env.base import BaseEnv
from project_proteus.env.simple import SimpleConfig
from project_proteus.database import DataBase


class SimpleEnv(BaseEnv):

    def __init__(self, config: SimpleConfig, headless=True, device=None) -> None:
        """
        Description:
            Simple market environment with a discrete action space: on every step the agent can choose to either:
            "open_long", "open_short", "close_long", "close_short" or "hold".
            Everything is implemented on the basis of pytorch.
        Arguments:
            -config[SimpleConfig]:          Config file for this environment, see SimpleConfig for more info.
            -headless[bool]:                Whether the env should get rendered or not
            -device[str]:                   On which device the environment should run
        """
        #run BaseEnv initialization
        super().__init__(config=config, headless=headless, device=device)

        #save num_steps
        self.num_steps = self.config.env.num_steps
        #save window length
        self.window_length = self.config.env.window_length
        
        """
        DataBase setup
        """
        #parse database config
        self._parse_database_config()

        """
        Actions setup
        """
        self.action_mapper = {
            "buy": 0,
            "sell": 1,
            "hold": 2
        }
        self.inverse_action_mapper = ["open_long", "open_short", "close_long", "close_short", "hold"]

        """
        Portfolio setup
        """
        self.portfolio = Portfolio(env=self)

    def reset(self):
        """
        Resets all the episode specific variables
        """
        #reset index variables
        self.local_index = 0
        self.index = random.randint(self.window_length-1, self.data_length-self.num_steps-1)
        

        #setup buffers
        self.action_buffer = np.zeros(shape=(self.config.env.num_steps))
        self.action_buffer[:] = None

    def step(self, action: int):
        """
        Description:
            Steps the simulation one timestep forward
        """

        #check if action is possible
        if action not in range(0,3):
            raise Exception(f"The chosen action: {action} is not possible")
        
        #save action in action_buffer
        self.action_buffer[self.local_index] = action

        #process action in portfolio
        self.portfolio.process_action(action)

        #render the environment
        self.render()

        #update the indeces
        self.index += 1
        self.local_index += 1

    """
    Constructor helper methods
    """
    def _parse_database_config(self):
        """
        Parses the database config and checks if all settings are possible
        This method does:
            -creates database and saves it under self.db
            -checks if candlestick_interval is available and raises an exception if its not available
            -saves the close prices and the corresponding times
        """

        #save candlestick_interval
        self.candlestick_interval = self.config.database.candlestick_interval

        #create database
        self.db = DataBase(path=self.config.database.path)

        #check if candlestick_interval is available
        if not self.db.check_candlestick_interval(self.candlestick_interval):
            raise Exception("Your chosen candlestick interval is not available in the chosen database")

        #save the close prices and corresponding times
        self.time_close = self.db[self.candlestick_interval, ["close_time", "close"]].to_numpy()

        #read in the data
        self.data = self.db[self.candlestick_interval].drop(["close_time", "open_time"], axis=1).to_numpy()
        self.data = torch.tensor(self.data, dtype=torch.float64, device=self.device)

        #get data parameters
        self.data_length = self.data.shape[0]

    """
    Getters and Setters
    """
    @property
    def current_price(self):
        """
        Description:
            Gets the current price at the moment.
        """
        return self.time_close[self.index, 1]

    @property
    def current_time(self):
        """
        Description:
            Gets the current time.
        """
        return self.time_close[self.index, 0]


class Portfolio():

    def __init__(self, env: SimpleEnv) -> None:
        """
        Description:
            Class for managing the portfolio
        Arguments:
            -env[SimpleEnv]:          Environement that this portfolio is used in
        """

        #save arguments
        self.env = env
        
        #save asset infos
        self.base_asset = self.env.db.dbid["base_asset"]
        self.quote_asset = self.env.db.dbid["quote_asset"]

        #save initial quote asset amount
        self.inital_quote_asset_amount = self.env.config.portfolio.initial_amount

        #setup initial portfolio
        self.quote_asset_amount = self.inital_quote_asset_amount
        self.base_asset_amount = 0

        #save trading fees
        self.trading_fees_percent = self.env.config.portfolio.trading_fees
        self.trading_fees = self.env.config.portfolio.trading_fees/100

        #setup trading status
        self.trading_status = "buy"


    def process_action(self, action):
        """
        Description:
            Imitates exchange and updates base and quote assets accordingly
        Arguments:
            -action[int]:       The action that the agent has chosen to take
        """

        #if chose action is hold
        if action == self.env.action_mapper["hold"]:
            return
        
        if self.trading_status == "buy" and action == self.env.action_mapper["buy"]:
            
            self.base_asset_amount = (self.quote_asset_amount / self.env.current_price) * (1-self.trading_fees)
            self.quote_asset_amount = 0
            
            self.trading_status = "sell"
            return

        if self.trading_status == "sell" and action == self.env.action_mapper["sell"]:

            self.quote_asset_amount = (self.base_asset_amount * self.env.current_price) * (1-self.trading_fees)
            self.base_asset_amount = 0

            self.trading_status = "buy"
            return

    @property
    def total_profit(self):
        """
        Returns total profit in quote asset
        """

        total_qa_amount = self.quote_asset_amount + self.base_asset_amount*self.env.current_price

        return total_qa_amount - self.inital_quote_asset_amount

if __name__ == "__main__":

    class MyConf(SimpleConfig):

        class database(SimpleConfig.database):
            #path to the database
            path = "/Users/fabio/Desktop/project-proteus/databases/test_futures"
            #which candlestick interval should be used in the environment
            candlestick_interval = "5m"

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

    conf = MyConf()

    env = SimpleEnv(config=conf, headless=True, device=None)

    env.reset()

    for i in range(10):
        env.step(random.randint(0,2))

    print(env.portfolio)