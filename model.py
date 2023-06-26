from Agents.companycountry import CountryAgent, CompanyAgent, NvidiaAgent, SMICAgent, InfineonAgent, RenesasAgent, TSMCAgent, IntelAgent, HuaHongAgent, STMicroelectronicsAgent, SonyAgent, MediaTekAgent, ASMLAgent, SumcoAgent
from Agents.communication import CommunicationChannel
from Agents.resource import Resource
from Agents.mine import MineAgent
from Agents.plant import ProcessingPlantAgent




import random
from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
import random
import numpy as np
import networkx as nx
import yaml
import matplotlib.pyplot as plt

class GameModel(Model):
    def __init__(self, agent_dict):
        #Define communication channels
        self.communication_channels = {"Press Conference": CommunicationChannel("Press Conference", 0.1, self),
                                        "Twitter": CommunicationChannel("Twitter", 0.5, self)}
        #Creating a schedule using Mesa's RandomActivation
        self.schedule = RandomActivation(self)
        #Initializing the flags and counters of the main risk we're investigating
        self.china_invades_taiwan = False #indicator of war
        self.invasion_probability = 0 #probability of invasion
        self.company_class_mapping = {
    "ASML": ASMLAgent,
    "Nvidia": NvidiaAgent,
    "Intel": IntelAgent,
    "SMIC": SMICAgent,
    "HuaHong": HuaHongAgent,
    "Infineon": InfineonAgent,
    "STMicroelectronics": STMicroelectronicsAgent,
    "Renesas": RenesasAgent,
    "Sony": SonyAgent,
    "TSMC": TSMCAgent,
    "MediaTek": MediaTekAgent,
    "Sumco": SumcoAgent,}


        agent_id = 0
        # Loop over each country and its corresponding list of companies from the YAML file
        for country, companies in agent_dict["company_country_map"].items():
            country_config = agent_dict["countries"].get(country, {})
            num_mines = country_config.pop('mines', 0)
            num_plants = country_config.pop('plants', 0)

            # Create a CountryAgent for each country
            country_agent = CountryAgent(agent_id, self, country, **country_config)
            agent_id += 1  # Increment the agent ID
            
            self.schedule.add(country_agent)
            for company in companies:
                CompanyAgentClass = self.company_class_mapping.get(company, CompanyAgent)
                company_agent = CompanyAgentClass(agent_id, self, country_agent, company)
                agent_id += 1  
                country_agent.set_company(company_agent)
                self.schedule.add(company_agent)

            for _ in range(num_mines):
                mine_agent = MineAgent(agent_id, self, country_agent)
                self.schedule.add(mine_agent)
                agent_id += 1  # Increment the agent ID
            for _ in range(num_plants):
                processing_plant_agent = ProcessingPlantAgent(agent_id, self, country_agent)
                self.schedule.add(processing_plant_agent)
                agent_id += 1  # Increment the agent ID

        additional_companies = agent_dict["additional_companies"]  # Load the number of additional companies from the yaml file
        for _ in range(additional_companies):
            country_agent = random.choice(self.schedule.agents)  # Choose a random country agent
            company_name = f"Company_{agent_id}"  # Generate a unique company name based on the agent ID
            company_agent = CompanyAgent(agent_id, self, country_agent, company_name)
            agent_id += 1  # Increment the agent ID

            # Randomize the company's resources and talent
            company_agent.resources["money"] = random.randint(*agent_dict["CompanyAgent"]["money_range"])
            company_agent.resources["chips"] = random.randint(*agent_dict["CompanyAgent"]["chips_range"])
            company_agent.talent = random.randint(*agent_dict["CompanyAgent"]["talent_range"])

            self.schedule.add(company_agent)  # Add the company agent to the schedule



        #Initialize a data collector
        self.datacollector = DataCollector(
            model_reporters={"Total Money": lambda m: sum(a.resources["money"] for a in m.schedule.agents),
                            "Total Chips": lambda m: sum(a.resources["chips"] for a in m.schedule.agents),
                            "China Invades Taiwan": lambda m: m.china_invades_taiwan,
                            "Invasion Probability": lambda m: m.invasion_probability,
                            "Total Capabilities Growth Rate": lambda m: sum(a.capabilities_score for a in m.schedule.agents if isinstance(a, CompanyAgent)),
                            "GDP": lambda m: {agent.country: agent.calculate_gdp() for agent in m.schedule.agents if isinstance(agent, CountryAgent)}},
            agent_reporters={"Agent Report": lambda a: a.report()} )

    #def load_config(self, config_file):
        #with open(config_file, 'r') as f:
            #return yaml.safe_load(f)
        self.create_network(agent_dict["partnerships"])
        self.print_agents()

    def create_network(self, partnerships):
    # Create an empty graph
        G = nx.Graph()

    # Add nodes from your agents
        for agent in self.schedule.agents:
            G.add_node(agent)

    # Add edges based on partnerships
        for partnership in partnerships:
            company1, company2 = partnership
         # Find agents corresponding to company1 and company2
            agent1 = next((agent for agent in self.schedule.agents if isinstance(agent, CompanyAgent) and agent.company_name == company1), None)
            agent2 = next((agent for agent in self.schedule.agents if isinstance(agent, CompanyAgent) and agent.company_name == company2), None)
            if agent1 is not None and agent2 is not None:
                G.add_edge(agent1, agent2)

        self.network = G

    def visualize_network(self):
        plt.figure(figsize=(10, 10))
        pos = nx.spring_layout(self.network)  # positions for all nodes

        # nodes
        nx.draw_networkx_nodes(self.network, pos, node_size=700)

        # edges
        nx.draw_networkx_edges(self.network, pos, width=2.0, edge_color='black')

        # labels
        #nx.draw_networkx_labels(self.network, pos, font_size=20, font_family='sans-serif')

        plt.axis('off')
        plt.show()

    def get_agent_by_id(self, unique_id):
      """Get an agent by its unique_id."""
      for agent in self.schedule.agents:
        if agent.unique_id == unique_id:
            return agent
      return None  # No agent found
    
    def print_agents(self):
        for agent in self.schedule.agents:
            print(f'Agent ID: {agent.unique_id}, Agent Type: {agent.__class__.__name__}')

    def step(self):
      '''Advance the model by one step.'''
      self.datacollector.collect(self) #collect data
      self.schedule.step()
