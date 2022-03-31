#standard libraries
import atexit
import json
import os

class DbId():
    """
    Description:
        Class which can be used like a dictionary.
        This Class is not threadsafe! The changes to the dictionary, only get written to disk when the instance goes out of scope!
        To write changes to the harddrive use self.dump()
    Arguments:
        -path[string]:     Path of the database
    """

    def __init__(self, path):
        #save path of dbid
        self.path = os.path.join(path, "dbid.json")

        #load in the dbid
        with open(self.path) as json_file:
            self.dbid = json.load(json_file)

        #register the dump at the end of lifetime
        atexit.register(self.dump)
        
    def __getitem__(self, key):
        return self.dbid[key]

    def __setitem__(self, key, item):
        #change the dict in ram
        self.dbid[key] = item

    def dump(self):
        #save changes to json file
        with open(self.path, 'w') as fp:
            json.dump(self.dbid, fp,  indent=4)

if __name__ == "__main__":
    pass