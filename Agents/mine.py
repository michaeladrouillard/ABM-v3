import random
from mesa import Agent
from mesa.time import RandomActivation

class MineAgent(Agent):
    def __init__(self, unique_id, model, country_agent):
        super().__init__(unique_id, model)
        self.resources = {"silicon": 100, "money": 50, "chips": 0}  # Initial resources
        self.country_agent = country_agent

    def extract(self):
        # A simple extraction model
        if self.resources["silicon"] > 0:
            extracted = self.resources["silicon"] * self.country_agent.silicon_export_rate
            self.resources["silicon"] -= extracted
            self.country_agent.resources["silicon"] += extracted

    def send_resources(self, amount):
        if self.resources["silicon"] >= amount:
            self.resources["silicon"] -= amount
            return amount
        else:
            return 0


    def step(self):
        self.extract()