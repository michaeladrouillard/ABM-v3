import random
from mesa import Agent
from mesa.time import RandomActivation

class CommunicationChannel:
  def __init__(self, name, distortion):
    self.name = name
    self.distortion = distortion

  def distort_message(self, message):
    # Distort the message based on the distortion level
    if self.distortion > random.random():
        # For instance, if the distortion level is higher than a random number, exaggerate the situation
        if 'Money' in message:
            return message.replace('High', 'Very High') if 'High' in message else message.replace('Low', 'Very Low')
        elif 'Chips' in message:
            return message.replace('High', 'Very High') if 'High' in message else message.replace('Low', 'Very Low')
    return message