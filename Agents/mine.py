import random
from mesa import Agent
from mesa.time import RandomActivation
import json

class MineAgent(Agent):
    def __init__(self, unique_id, model, country_agent):
        super().__init__(unique_id, model)
        self.country_agent = country_agent
        self.country = country_agent.country 

        # Load JSON file
        with open('Agents/agent_config.json') as json_file:
            data = json.load(json_file)

        mine_data = data["MineAgent"]

        # Set initial resources based on the JSON file
        self.resources = mine_data["initial_resources"]

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
        
    def receive_message(self, message):   
        if "More Money" in message:
            self.anxiety_score += self.model.communication_channels["Twitter"].distortion if "Twitter" in message else self.model.communication_channels["Press Conference"].distortion
        elif "Less Money" in message:
            self.anxiety_score -= self.model.communication_channels["Twitter"].distortion if "Twitter" in message else self.model.communication_channels["Press Conference"].distortion


    def step(self):
        self.extract()