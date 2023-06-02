from Agents.companycountry import *
from Agents.communication import *
from Agents.resource import *
from Agents.mine import *
from Agents.plant import *

import random
from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
import random
import numpy as np
import networkx as nx
import yaml

class GameModel(Model):
    def __init__(self, N, config_file='config.yaml'):
        self.communication_channels = {"Press Conference": CommunicationChannel("Press Conference", 0.1),
                                        "Twitter": CommunicationChannel("Twitter", 0.5)}
        self.num_agents = N
        self.schedule = RandomActivation(self)
        self.china_invades_taiwan = False #indicator of war
        self.invasion_probability = 0 #probability of invasion
        self.company_affiliations = {"US": "Nvidia", "China": "SMIC", "EU": "Infineon", "Japan": "Renesas", "Taiwan": "TSMC"}  # Company affiliations
        self.config = self.load_config(config_file)
        #Create agents
        countries = ["US", "China", "EU", "Japan", "Taiwan"]
        random.shuffle(countries)  # Shuffle the list to add randomness
        agent_id = 0
        for i, country in enumerate(countries[:N]):  # Use the first N countries from the shuffled list
            country_config = self.config["countries"].get(country, {})
            num_mines = country_config.pop('mines', 0)
            num_plants = country_config.pop('plants', 0)
            country_agent = CountryAgent(agent_id, self, country, **country_config)
            agent_id += 1  # Increment the agent ID
            company = self.company_affiliations[country]
            company_agent = CompanyAgent(agent_id, self, country_agent, company)
            agent_id += 1  # Increment the agent ID
            country_agent.set_company(company_agent)
            self.schedule.add(country_agent)
            self.schedule.add(company_agent)

            for _ in range(num_mines):
                mine_agent = MineAgent(agent_id, self, country_agent)
                self.schedule.add(mine_agent)
                agent_id += 1  # Increment the agent ID
            for _ in range(num_plants):
                processing_plant_agent = ProcessingPlantAgent(agent_id, self, country_agent)
                self.schedule.add(processing_plant_agent)
                agent_id += 1  # Increment the agent ID
        additional_companies = self.config["additional_companies"]  # Load the number of additional companies from the yaml file
        for _ in range(additional_companies):
            country_agent = random.choice(self.schedule.agents)  # Choose a random country agent
            company_name = f"Company_{agent_id}"  # Generate a unique company name based on the agent ID
            company_agent = CompanyAgent(agent_id, self, country_agent, company_name)
            agent_id += 1  # Increment the agent ID

            # Randomize the company's resources and talent
            company_agent.resources["money"] = random.randint(*self.config["CompanyAgent"]["money_range"])
            company_agent.resources["chips"] = random.randint(*self.config["CompanyAgent"]["chips_range"])
            company_agent.talent = random.randint(*self.config["CompanyAgent"]["talent_range"])

            self.schedule.add(company_agent)  # Add the company agent to the schedule


        # Create a random network of agents
        G = nx.erdos_renyi_graph(n=self.num_agents, p=0.1)
        self.network = nx.relabel_nodes(G, dict(zip(range(self.num_agents), self.schedule.agents)))

        #Update compute_total_capabilities_growth_rate function
        def compute_total_capabilities_growth_rate(model):
            total_growth_rate = sum(a.capabilities_score for a in model.schedule.agents if isinstance(a, CompanyAgent))
            return total_growth_rate

        #Initialize a data collector
        self.datacollector = DataCollector(
            model_reporters={"Total Money": lambda m: sum(a.resources["money"] for a in m.schedule.agents),
                            "Total Chips": lambda m: sum(a.resources["chips"] for a in m.schedule.agents),
                            "China Invades Taiwan": lambda m: m.china_invades_taiwan,
                            "Invasion Probability": lambda m: m.invasion_probability,
                            "Total Capabilities Growth Rate": compute_total_capabilities_growth_rate,
                            "GDP": lambda m: {agent.country: agent.calculate_gdp() for agent in m.schedule.agents if isinstance(agent, CountryAgent)}},
            agent_reporters={"Money": lambda a: a.resources["money"], 
                             "Chips": lambda a: a.resources["chips"],
                             "Talent": lambda a: a.talent if isinstance(a, CompanyAgent) else None,
                             #"Country": lambda a: a.get_country() if isinstance(a, CompanyAgent) else a.country,
                             "Public Opinion": lambda a: a.public_opinion if isinstance(a, CountryAgent) else None,
                              "Capabilities Score": lambda a: a.capabilities_score if isinstance(a, CompanyAgent) else None})

    def check_invasion_condition(self):
        for agent in self.schedule.agents:
            if isinstance(agent, CountryAgent) and agent.country == "China":
                self.invasion_probability = max(0, 1 - agent.public_opinion / 10)
                break
    def get_agent_by_id(self, unique_id):
      """Get an agent by its unique_id."""
      for agent in self.schedule.agents:
        if agent.unique_id == unique_id:
            return agent
      return None  # No agent found
    
  
    def load_config(self, config_file):
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    
    def step(self):
      '''Advance the model by one step.'''
      self.datacollector.collect(self) #collect data
      self.schedule.step()
      self.check_invasion_condition()
      if np.random.random() < self.invasion_probability:
        self.china_invades_taiwan = True

            # Find the Chinese mine and Japanese processing plant
        # Find the Chinese mine and Japanese processing plant
      chinese_mine = next((agent for agent in self.schedule.agents if isinstance(agent, MineAgent) and agent.country == "China"), None)
      japanese_plant = next((agent for agent in self.schedule.agents if isinstance(agent, ProcessingPlantAgent) and agent.country == "Japan"), None)

      if chinese_mine and japanese_plant:
            # Determine how much silicon to send
        transfer_amount = self.config["resource_transfer"]["China"]["Japan"]["silicon"]
        amount = min(chinese_mine.resources["silicon"], transfer_amount)

            # Transfer the silicon
        amount_sent = chinese_mine.send_resources(amount)
        japanese_plant.receive_resources(amount_sent)