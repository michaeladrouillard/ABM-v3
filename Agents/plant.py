import random
from mesa import Agent
from mesa.time import RandomActivation
import json

class ProcessingPlantAgent(Agent):
    def __init__(self, unique_id, model, country_agent):
        super().__init__(unique_id, model)
        self.country_agent = country_agent
        self.country = country_agent.country 
        self.anxiety_score  = 0
        # Load JSON file
        with open('Agents/agent_config.json') as json_file:
            data = json.load(json_file)

        plant_data = data["ProcessingPlantAgent"]

        # Set initial resources based on the JSON file
        self.resources = plant_data["initial_resources"]

    def process(self):
        # A simple processing model
        if self.country_agent.resources["silicon"] > 0:
            processed = self.country_agent.resources["silicon"] * self.country_agent.processing_capacity
            self.country_agent.resources["silicon"] -= processed
            self.country_agent.resources["chips"] += processed * 10  # Assume each unit of silicon gives 10 chips
    
    def receive_resources(self, amount):
        self.resources["silicon"] += amount
    
    def receive_message(self, message):   
        if "More Money" in message:
            self.anxiety_score += self.model.communication_channels["Twitter"].distortion if "Twitter" in message else self.model.communication_channels["Press Conference"].distortion
        elif "Less Money" in message:
            self.anxiety_score -= self.model.communication_channels["Twitter"].distortion if "Twitter" in message else self.model.communication_channels["Press Conference"].distortion


    def step(self):
        self.process()