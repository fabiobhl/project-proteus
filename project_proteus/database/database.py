#standard libraries imports
import os
import shutil
import json

#package imports
from project_proteus import REPO_PATH
from project_proteus.database import DbId
from project_proteus.utils import read_config

#external libraries imports
from binance.client import Client
import pandas as pd


class DataBase():
    """
    Description:
        This is the base Database class, on which every other Database Objects builds upon.
    Arguments:
        -path[string]:  Path of the Database
    """
    
    def __init__(self, path):
        #save the params
        self.path = path

        #check if the path exists and is a database
        if not os.path.isdir(path):
            raise Exception("The path you chose is not existing")
        if not os.path.isfile(os.path.join(path, "dbid.json")):
            raise Exception("The path you chose is not a DataBase")
        
        #setup dbid
        self.dbid = DbId(path=self.path)
    
    def __getitem__(self, index):
        """
        Description:
            Method for accessing data of the database. The access is direct from the harddrive (slower but more memory efficient)
        Arguments:
            -index[string, list]:   Generally: [candlestick_interval, list of features]. To access the whole dataframe only specify the candlestick_interval you want e.g. db["5m"].
                                    To access only one feature specify the candlestick_interval and the feature you want e.g. db["5m", "close"]
                                    To access multiple features specify the datatype and a list of features you want e.g. db["5m", ["close", "open"]]
        Return:
            -data[pd.DataFrame]:    Returns always a DataFrame in the shape (rows, number of specified features) 
        """
        
        #set the path
        if type(index) == tuple:
            path = os.path.join(self.path, index[0])
        elif type(index) == str:
            path = os.path.join(self.path, index)
        else:
            raise Exception("Your chosen index is not valid")

        #check if path is available
        if not os.path.isdir(path):
            raise Exception("Your chosen kline-interval is not available")

        #access whole dataframe of certain kline-interval
        if type(index) == str:
            #load in the data and return
            try:
                #get path
                csv_path = os.path.join(path, f"{index}.csv")
                #load data
                data = pd.read_csv(filepath_or_buffer=csv_path, index_col="index")
                #convert the date columns
                data["close_time"]= pd.to_datetime(data["close_time"])
                data["open_time"]= pd.to_datetime(data["open_time"])
                
                return data

            except:
                raise Exception("Your chosen kline-interval is not available in this DataBase")

        #access one feature of a kline-interval
        elif type(index) == tuple and len(index) == 2 and type(index[0]) == str and type(index[1]) == str:
            try:
                #get path
                csv_path = os.path.join(path, f"{index[0]}.csv")
                #load data
                data = pd.read_csv(filepath_or_buffer=csv_path, usecols=[index[1]])
                
                #convert the date columns
                if "close_time" in data.columns:
                    data["close_time"]= pd.to_datetime(data["close_time"])
                if "open_time" in data.columns:
                    data["open_time"]= pd.to_datetime(data["open_time"])

                return data
            
            except:
                raise Exception("Your chosen feature is not available in this DataBase")
            
        #access list of features of a kline-interval
        elif type(index) == tuple and len(index) == 2 and type(index[0]) == str and type(index[1]) == list:
            try:
                #get path
                csv_path = os.path.join(path, f"{index[0]}.csv")
                #load data
                data = pd.read_csv(filepath_or_buffer=csv_path, usecols=index[1])
                
                #convert the date columns
                if "close_time" in data.columns:
                    data["close_time"]= pd.to_datetime(data["close_time"])
                if "open_time" in data.columns:
                    data["open_time"]= pd.to_datetime(data["open_time"])

                return data[index[1]]
            
            except:
                raise Exception("One/multiple of your chosen feature/s is/are not available in this DataBase")
        
        #throw error on all other accesses
        else:
            raise Exception("Your index is not possible, please check your index and the documentation on the DataBase object")
    
    @staticmethod
    def _download_kline_interval(symbol, start_date, end_date, candlestick_interval, config_path):   
        """
        Description:
            Helper method for downloading all the kline data.           
        Arguments:
            -symbol[string]:                        The Cryptocurrency you want to trade (Note: With accordance to the Binance API)
            -start_date[string]:                    The date of the start of your data
            -end_date[string]:                      The date of the end of your data
            -candlestick_interval[string]:          On what interval the candlestick data should be downloaded
            -config_path[string]:                   Path to the config file, if none is given, it is assumed that the config-file is in the same folder as the file this method gets called from
        Return:
            -data[pd.DataFrame]:                    Returns the created DataBase object
        """
        #read in the config
        config = read_config(path=config_path)

        #create the client
        client = Client(api_key=config["binance"]["key"], api_secret=config["binance"]["secret"])

        #download the data and safe it in a dataframe
        print(f"Downloading {candlestick_interval} klines...")
        raw_data = client.get_historical_klines(symbol=symbol, interval=candlestick_interval, start_str=start_date, end_str=end_date)
        data = pd.DataFrame(raw_data)

        #clean the dataframe
        data = data.astype(float)
        data.drop(data.columns[[7,8,9,10,11]], axis=1, inplace=True)
        data.rename(columns = {0:'open_time', 1:'open', 2:'high', 3:'low', 4:'close', 5:'volume', 6:'close_time'}, inplace=True)

        #set the correct times
        data['close_time'] += 1
        data['close_time'] = pd.to_datetime(data['close_time'], unit='ms')
        data['open_time'] = pd.to_datetime(data['open_time'], unit='ms')

        #check for nan values
        if data.isna().values.any():
            raise Exception("Nan values in data, please discard this object and try again")

        #reset the index
        data.reset_index(inplace=True, drop=True)

        return data

    def add_candlestick_interval(self, candlestick_interval, config_path=None):
        """
        Description:
            Method for adding a candlestick interval to the database
        Arguments:
            -candlestick_interval[string]:          On what interval the candlestick data should be downloaded
            -config_path[string]:                   Path to the config file, if none is given, it is assumed that the config-file is in the same folder as the file this method gets called from
        """
        #check if interval already exists
        if os.path.isdir(os.path.join(self.path, candlestick_interval)):
            raise Exception("Your chosen candlestick_interval already exists")

        #download interval
        data = self._download_kline_interval(symbol=self.dbid["symbol"], start_date=self.dbid["date_range"][0], end_date=self.dbid["date_range"][1], candlestick_interval=candlestick_interval, config_path=config_path)

        #create the directory
        os.mkdir(os.path.join(self.path, candlestick_interval))

        #save the data to csv's
        data.to_csv(path_or_buf=os.path.join(self.path, candlestick_interval, f"{candlestick_interval}.csv"), index_label="index")

        #add candlestick_interval to dbid
        self.dbid["candlestick_interval"].append(candlestick_interval)
        self.dbid.dump()

        print(f"{candlestick_interval} klines have been succesfully added!")

    @classmethod
    def create(cls, save_path: str, symbol: str, date_span: tuple, candlestick_intervals: str, config_path: str = None):
        """
        Description:
            This method creates a DataBase-Folder at a given location with the specified data.           
        Arguments:
            -save_path[string]:                     The location, where the folder gets created (Note: The name of the folder should be in the save_path e.g: "C:/.../desired_name")
            -symbol[string]:                        The Cryptocurrency you want to trade (Note: With accordance to the Binance API)
            -date_span[tuple]:                      Tuple of datetime.date objects in the form: (startdate, enddate)
            -candlestick_intervals[list[string]]:   On what interval the candlestick data should be downloaded
            -config_path[string]:                   Path to the config file, if none is given, it is assumed that the config-file is in the same folder as the file this method gets called from
        Return:
            -DataBase[DataBase object]:             Returns the created DataBase object
        """
       
        #check if the specified directory already exists
        if os.path.isdir(save_path):
            raise Exception("Please choose a directory, that does not already exist")
        
        #create the directory
        os.mkdir(save_path)

        #get the dates and format them
        startdate = date_span[0].strftime("%d %b, %Y")
        enddate = date_span[1].strftime("%d %b, %Y")

        """
        Download the data and save it to directory
        """
        try:
            for candlestick_interval in candlestick_intervals:
                #download the data
                data = cls._download_kline_interval(symbol=symbol, start_date=startdate, end_date=enddate, candlestick_interval=candlestick_interval, config_path=config_path)
                #create the directory
                os.mkdir(os.path.join(save_path, candlestick_interval))
                #save the data to csv's
                data.to_csv(path_or_buf=os.path.join(save_path, candlestick_interval, f"{candlestick_interval}.csv"), index_label="index")
        
        except Exception as e:
            shutil.rmtree(save_path)
            raise e
        
        print("======Finished downloading======")
        
        """
        Creating the dbid and saving it
        """
        #create the dbid
        dbid = {
            "symbol": symbol,
            "date_range": (startdate, enddate),
            "candlestick_interval": [candlestick_interval for candlestick_interval in candlestick_intervals]
        }

        #save the dbid
        with open(os.path.join(save_path, "dbid.json"), 'w') as fp:
            json.dump(dbid, fp,  indent=4)
        
        return cls(path=save_path)

if __name__ == "__main__":
    pass