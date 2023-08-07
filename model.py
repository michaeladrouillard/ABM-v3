from Agents.companycountry import CountryAgent, CompanyAgent, NvidiaAgent, SMICAgent, InfineonAgent, RenesasAgent, TSMCAgent, IntelAgent, HuaHongAgent, STMicroelectronicsAgent, SonyAgent, MediaTekAgent, ASMLAgent, SumcoAgent, SamsungAgent, CustomerAgent, SamsungSub, SiltronicAgent, FujimiAgent, SKSiltronAgent, ShinEtsuAgent, GlobalFoundriesAgent, AMDAgent, QualcommAgent, AmazonAgent, GoogleAgent, PeopleAgent, AppleAgent, MetaAgent, OpenAIAgent, TexasInstrumentsAgent
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
        self.country_agents = {}  
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
    "Sumco": SumcoAgent,
    "Samsung": SamsungAgent,
    "SamsungSub": SamsungSub,
    "Siltronic": SiltronicAgent,
    "Fujimi": FujimiAgent,
    "SKSiltron": SKSiltronAgent,
    "ShinEtsu": ShinEtsuAgent,
    "GlobalFoundries": GlobalFoundriesAgent,
    "AMD": AMDAgent,
    "Qualcomm": QualcommAgent,
    "Amazon": AmazonAgent,
    "Google" : GoogleAgent,
    "Apple": AppleAgent,
    "Meta": MetaAgent,
    "OpenAI": OpenAIAgent,
    "TexasInstruments": TexasInstrumentsAgent}


        agent_id = 0
        people_agent = PeopleAgent(agent_id, self)
        agent_id += 1  # Increment the agent ID
        self.schedule.add(people_agent)
        # Loop over each country and its corresponding list of companies from the YAML file
        for country, companies in agent_dict["company_country_map"].items():
            country_config = agent_dict["countries"].get(country, {})
            num_mines = country_config.pop('mines', 0)
            num_plants = country_config.pop('plants', 0)

            # Create a CountryAgent for each country
            country_agent = CountryAgent(agent_id, self, country, **country_config)
            agent_id += 1  # Increment the agent ID
            self.schedule.add(country_agent)
            #store the country agent in the dictionary
            self.country_agents[country] = country_agent

            for company in companies:
                CompanyAgentClass = self.company_class_mapping.get(company, CompanyAgent)
                # Look up the country agent in the dictionary when creating the company agent
                company_agent = CompanyAgentClass(agent_id, self, self.country_agents[country], company)
                agent_id += 1  
                #country_agent.set_company(company_agent)
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
            country_agent = random.choice([agent for agent in self.schedule.agents if isinstance(agent, CountryAgent)])  # Choose a random country agent
            company_name = f"Company_{agent_id}"  # Generate a unique company name based on the agent ID
            company_agent = CompanyAgent(agent_id, self, country_agent, company_name)
            agent_id += 1  # Increment the agent ID

            # Randomize the company's resources and talent
            company_agent.resources["money"] = random.randint(*agent_dict["CompanyAgent"]["money_range"])
            company_agent.resources["chips"] = random.randint(*agent_dict["CompanyAgent"]["chips_range"])
            company_agent.talent = random.randint(*agent_dict["CompanyAgent"]["talent_range"])

            self.schedule.add(company_agent)  # Add the company agent to the schedule


        num_customers = 5  # Adjust this value to change the number of customers

        for _ in range(num_customers):
            # Create a CustomerAgent
            customer_agent = CustomerAgent(agent_id, self)
            agent_id += 1  # Increment the agent ID

            self.schedule.add(customer_agent) 
            
        #Initialize a data collector
        self.datacollector = DataCollector(
            model_reporters={"Total Money": lambda m: sum(a.resources["money"] for a in m.schedule.agents if not isinstance(a, PeopleAgent)),
                            "Total Chips": lambda m: sum(a.resources["chips"] for a in m.schedule.agents if not isinstance(a, PeopleAgent)),
                            "Total Capabilities Growth Rate": lambda m: sum(a.capabilities_score for a in m.schedule.agents if isinstance(a, CompanyAgent)),
                            "GDP": lambda m: {agent.country: agent.calculate_gdp() for agent in m.schedule.agents if isinstance(agent, CountryAgent)}},
            agent_reporters={"Money": lambda a: a.resources["money"] if not isinstance(a, PeopleAgent) else None,
                             "CompanyName": lambda a: a.company_name if hasattr(a, 'company_name') else None} )

        self.print_agents()


    def get_agent_by_id(self, unique_id):
      """Get an agent by its unique_id."""
      for agent in self.schedule.agents:
        if agent.unique_id == unique_id:
            return agent
      return None  # No agent found
    
    def print_final_counts(self):
        total_launch_project = sum(agent.launch_project_count for agent in self.schedule.agents if isinstance(agent, CompanyAgent))
        total_lobby_government = sum(agent.lobby_government_count for agent in self.schedule.agents if isinstance(agent, CompanyAgent))
        total_compete_with = sum(agent.compete_with_count for agent in self.schedule.agents if isinstance(agent, CompanyAgent))
    
        print(f"Total launch_project actions performed: {total_launch_project}")
        print(f"Total lobby_government actions performed: {total_lobby_government}")
        print(f"Total compete_with actions performed: {total_compete_with}")


    def print_agents(self):
        for agent in self.schedule.agents:
            print(f'Agent ID: {agent.unique_id}, Agent Type: {agent.__class__.__name__}')

    def step(self):
      '''Advance the model by one step.'''
      self.datacollector.collect(self) #collect data
      self.schedule.step()

