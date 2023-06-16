import random
from mesa import Agent
from mesa.time import RandomActivation

#Define the Resource class
class Resource:
  def __init__(self, name, model):
    self.name = name
    #self.quantity = quantity
    #initialize other parameters for Resource here

  def transfer(self, sender, receiver, amount):
    #implement the logic of transferring resources
    #think about how this would be applied... chips sent to countries? idk
    if sender.resources[self.name] >= amount:
      sender.resources[self.name] -= amount
      receiver.resources[self.name] += amount