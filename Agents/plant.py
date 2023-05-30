import random
from mesa import Agent
from mesa.time import RandomActivation

class ProcessingPlantAgent(Agent):
    def __init__(self, unique_id, model, country_agent):
        super().__init__(unique_id, model)
        self.resources = {"chips": 50, "money": 50}
        self.country_agent = country_agent

    def process(self):
        # A simple processing model
        if self.country_agent.resources["silicon"] > 0:
            processed = self.country_agent.resources["silicon"] * self.country_agent.processing_capacity
            self.country_agent.resources["silicon"] -= processed
            self.country_agent.resources["chips"] += processed * 10  # Assume each unit of silicon gives 10 chips
    
    def receive_resources(self, amount):
        self.resources["silicon"] += amount
    
    def step(self):
        self.process()