import random
from mesa import Agent
from mesa.time import RandomActivation


class CompanyAgent(Agent):
    def __init__(self, unique_id, model, country_agent, company_name):
        super().__init__(unique_id, model)
        self.talent = random.randint(1,10)  
        self.resources = {"money": 100, "chips": 50}  
        self.country_agent = country_agent 
        self.company_name = company_name  
        self.capabilities_score = 0
        self.anxiety_score = 0

    def get_country(self):
        return self.country_agent.country

    def increase_capabilities(self):
      #increase capabilities score
      self.capabilities_score += 1

    def cooperate_with(self, other_agent):
        if isinstance(other_agent, CompanyAgent):
            # Define the logic of cooperation with another company here.
            if self.resources["money"] > 30 and other_agent.resources["chips"] > 30:
                self.resources["money"] -= 10
                other_agent.resources["money"] += 10
                self.resources["chips"] += 10
                other_agent.resources["chips"] -= 10

                # Decrease anxiety score due to successful cooperation
                self.anxiety_score -= 1
                other_agent.anxiety_score -= 1

                return True  # Cooperation was successful
            else:
                return False  # Cooperation failed due to insufficient resources
        elif isinstance(other_agent, CountryAgent):
            # Define the logic of cooperation with a country here.
            if self.resources["money"] > 30 and other_agent.resources["chips"] > 30:
                self.resources["money"] -= 10
                other_agent.resources["money"] += 10
                self.resources["chips"] += 10
                other_agent.resources["chips"] -= 10

                # Decrease anxiety score due to successful cooperation
                self.anxiety_score -= 1
                other_agent.anxiety_score -= 1

                return True  # Cooperation was successful
            else:
                return False  # Cooperation failed due to insufficient resources


    def receive_message(self, message):   
      # A simple example of receiving a message: change anxiety level based on the message content
        if "High Money" in message or "Very High Money" in message or "High Chips" in message or "Very High Chips" in message:
            self.anxiety_score -= 1
        elif "Low Chips" in message or "Low Money" in message:
            self.anxiety_score += 1

    def launch_project(self):
        if self.resources["money"] >= 30:  # Assuming launching a project requires 30 money
            self.resources["money"] -= 30
            self.increase_capabilities()  # Launching a project increases capabilities

            # This decreases the country's level. Decrease own anxiety level, using a percentage decrease for demonstration
            self.country_agent.anxiety_score *= 0.9
            self.anxiety_score *= 0.9
            # Increase anxiety level of other agents
            for agent in self.model.schedule.agents:
                if isinstance(agent, CountryAgent) and agent.unique_id != self.unique_id + 1:
                    agent.anxiety_score += self.capabilities_score * 0.01  # Using capabilities score as a factor
            return True  # Successfully launched project
        else:
            # Increase own anxiety level and country level if project fails
            self.country_agent.anxiety_score += 1
            self.anxiety_score += 1 
            return False  # Failed to launch project due to insufficient money
       

    def lobby_government(self):
        if self.talent >= 5:  # Lobbying government requires talent score >= 5
            # Lobbying government might increase resources
            self.resources["money"] += random.randint(10, 20)  # Increase in money
            self.resources["chips"] += random.randint(5, 10)  # Increase in chips
            return True  # Successfully lobbied government
        return False  # Failed to lobby government due to insufficient talent

    def compete_with(self, other_company):
        # Companies compete based on their capabilities
        if self.capabilities_score > other_company.capabilities_score:
            # Winning company takes some resources from the losing company
            self.resources["money"] += other_company.resources["money"] * 0.1  # Takes 10% of other's money
            other_company.resources["money"] *= 0.9  # Loses 10% of money
            return True  # This company wins
        return False  # This company loses


    def choose_action(self):
        if self.resources["money"] > 20 and self.resources["chips"] < 20:  # lowered the thresholds
            self.launch_project()
        elif self.resources["money"] <= 50 and self.talent > 3:  # lowered the thresholds
            self.lobby_government()
        elif len([agent for agent in self.model.schedule.agents if agent is not self]) > 0:
            other = random.choice([agent for agent in self.model.schedule.agents if agent is not self])
            self.cooperate_with(other)
        else:
            other = random.choice([agent for agent in self.model.schedule.agents if isinstance(agent, CompanyAgent) and agent is not self])
            self.compete_with(other)


    def step(self):
        self.choose_action()

    
