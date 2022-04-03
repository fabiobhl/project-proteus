#external library imports
import torch

#package imports
from project_proteus.env.base import BaseConfig


class BaseEnv():

    def __init__(self, config: BaseConfig, headless: bool, device: str) -> None:
        """
        Base environment on which all environments get built on.
        """
    
        #save the arguments
        self.config = config
        self.headless = headless
        
        #setup device
        if device == None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

    def step(self, actions):
        raise NotImplementedError()

    def reset(self):
        raise NotImplementedError()

    def render(self):
        """
        Renders to screen if headless is set to false
        """
        pass


