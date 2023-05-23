from Agents.company import *
from Agents.country import *
from Agents.communication import *
from Agents.resource import *


import random
from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
import random
import numpy as np
import networkx as nx

class GameModel(Model):
    def __init__(self, N):
        self.communication_channels = {"Press Conference": CommunicationChannel("Press Conference", 0.1),
                                        "Twitter": CommunicationChannel("Twitter", 0.5)}
        self.num_agents = N
        self.schedule = RandomActivation(self)
        self.china_invades_taiwan = False #indicator of war
        self.invasion_probability = 0 #probability of invasion
        self.company_affiliations = {"US": "Nvidia", "China": "SMIC", "EU": "Infineon", "Japan": "Renesas", "Taiwan": "TSMC"}  # Company affiliations
        #Create agents
        for i in range(self.num_agents):
            country = random.choice(["US", "China", "EU", "Japan", "Taiwan"])
            country_agent = CountryAgent(i*2+1, self, country)
            company = self.company_affiliations[country]
            company_agent = CompanyAgent(i*2, self, country_agent, company)
            country_agent.set_company(company_agent)
            self.schedule.add(country_agent)
            self.schedule.add(company_agent)
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
                             "Country": lambda a: a.get_country() if isinstance(a, CompanyAgent) else a.country,
                             "Anxiety Level": lambda a: a.anxiety_score if isinstance(a, CountryAgent) else None,
                              "Capabilities Score": lambda a: a.capabilities_score if isinstance(a, CompanyAgent) else None})

    def check_invasion_condition(self):
        for agent in self.schedule.agents:
            if isinstance(agent, CountryAgent) and agent.country == "China":
                self.invasion_probability = max(0, 1 - agent.anxiety_score / 10)
                break
    def get_agent_by_id(self, unique_id):
      """Get an agent by its unique_id."""
      for agent in self.schedule.agents:
        if agent.unique_id == unique_id:
            return agent
      return None  # No agent found
    
    def step(self):
      '''Advance the model by one step.'''
      self.datacollector.collect(self) #collect data
      self.schedule.step()
      self.check_invasion_condition()
      if np.random.random() < self.invasion_probability:
        self.china_invades_taiwan = True