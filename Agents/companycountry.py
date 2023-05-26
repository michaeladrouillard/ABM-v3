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
        if self.resources["money"] > 20:  # Condition for launching a project
            self.launch_project()
        elif self.resources["money"] <= 50 and self.talent > 3:  # Condition for lobbying government
            self.lobby_government()
        elif len([agent for agent in self.model.schedule.agents if agent is not self]) > 0:
            # Choose to cooperate with a country agent
            other = random.choice([agent for agent in self.model.schedule.agents if isinstance(agent, CountryAgent) and agent is not self])
            self.cooperate_with(other)
        else:
            # Choose to cooperate with a company agent
            other = random.choice([agent for agent in self.model.schedule.agents if isinstance(agent, CompanyAgent) and agent is not self])
            self.cooperate_with(other)


    def step(self):
        self.choose_action()


class CountryAgent(Agent):
    def __init__(self, unique_id, model, country):
        super().__init__(unique_id, model)
        self.resources = {"money": 100, "chips": 50}  # Initial resources
        self.country = country  # Country the agent belongs to
        self.anxiety_score = 0  # The anxiety level of the agent
        self.company = None  # The CompanyAgent associated with this country, initialized to None
        self.debt = 0
        self.gdp = 0  # Initialize GDP to 0
        self.prev_resources = self.resources.copy()  # Copy of resource levels at the previous time step
   
    def set_company(self, company_agent):
        self.company = company_agent  # Associate a CompanyAgent with this CountryAgent
        self.gdp = self.calculate_gdp()  # Update GDP after company agent is set

    
    def calculate_gdp(self):
        """Calculate the GDP based on the resources of the country and its affiliated company."""
        if self.company:
            company_resources = self.company.resources["money"] + self.company.resources["chips"]
            # Let's assume that the capabilities score of the company directly contributes to the GDP
            company_cap_score = self.company.capabilities_score
        else:
            company_resources = 0
            company_cap_score = 0
        country_resources = self.resources["money"] + self.resources["chips"]
        return company_resources + country_resources + company_cap_score

    def approve_project(self, project_cost):
        self.debt += project_cost

    def send_private_message(self, message, receiver):
        # Sends a private message without 
        message_content = self.evaluate_message_content(message)
        receiver.receive_message(message)

    def send_public_message(self, message, channel):
        distorted_message = self.model.communication_channels[channel].distort_message(message)
        for agent in self.model.schedule.agents: 
            agent.receive_message(distorted_message)
  
    def receive_message(self, message):   
        if "More Money" in message:
            self.anxiety_score += self.model.communication_channels["Twitter"].distortion if "Twitter" in message else self.model.communication_channels["Press Conference"].distortion
        elif "Less Money" in message:
            self.anxiety_score -= self.model.communication_channels["Twitter"].distortion if "Twitter" in message else self.model.communication_channels["Press Conference"].distortion


    def evaluate_message_content(self, message_type):
        """Evaluate message content based on the message type and changes in resources."""
        if message_type == 'money':
            if self.resources['money'] > self.prev_resources['money']:
                return 'More Money'
            elif self.resources['money'] < self.prev_resources['money']:
                return 'Less Money'
            else:
                return 'Same Money'
        elif message_type == 'chips':
            if self.resources['chips'] > self.prev_resources['chips']:
                return 'More Chips'
            elif self.resources['chips'] < self.prev_resources['chips']:
                return 'Less Chips'
            else:
                return 'Same Chips'
        else:
            return ''

    def cooperate_with(self, other_agent):
        if self.resources["money"] > 30 and other_agent.resources["chips"] > 30:
            self.resources["money"] -= 10
            other_agent.resources["money"] += 10
            self.resources["chips"] += 10

            # Decrease anxiety score due to successful cooperation
            self.anxiety_score -= 1
            other_agent.anxiety_score -= 1

            return True  # Cooperation was successful
        else:
            return False  # Cooperation failed due to insufficient resources

    def impose_sanctions(self, other):
      #Implement the logic of imposing sanctions
      ### add probability of inherence
      if self.resources["money"] > 30: #sanctions require money
          self.resources["money"] -= 30 #pay for the sanctions
          # ^ does this make sense?
          other.resources["money"] -= other.resources["money"] * 0.2  # Other agent loses 20% of money
          return True #succesfully imposed sanctions
      else:
          return False #failed to impose sanctions

    def choose_action(self):
        # Calculate current GDP
        current_gdp = self.calculate_gdp()

        # Choose the communication channel randomly
        channel = random.choice(list(self.model.communication_channels.keys()))

        # Check if there are any other agents to impose sanctions on
        other_agents = [agent for agent in self.model.schedule.agents if agent is not self]
    
        if self.resources["money"] > 30 and self.resources["chips"] < 20 and other_agents:
            prospective_money = self.resources["money"] - 10
            prospective_gdp = prospective_money + self.resources["chips"]
            if prospective_gdp > current_gdp:
                other = random.choice(other_agents)
                self.impose_sanctions(other)
                self.send_public_message(self.evaluate_message_content('money'), channel)

        if self.anxiety_score > 7 or self.gdp < 5:
            if self.resources["money"] > 60: 
                prospective_money = self.resources["money"] - 60
                prospective_gdp = prospective_money + self.resources["chips"]
                if prospective_gdp > current_gdp:
                    self.resources['money'] -= 60
                    self.approve_project(60)
                    self.send_public_message(self.evaluate_message_content('money'), channel)

        country_agents = [agent for agent in self.model.schedule.agents if isinstance(agent, CountryAgent) and agent is not self]
        if country_agents and self.resources["money"] > 30 and self.resources["chips"] > 30:
            prospective_money = self.resources["money"] - 10
            prospective_chips = self.resources["chips"] + 10
            prospective_gdp = prospective_money + prospective_chips
            if prospective_gdp > current_gdp:
                other = random.choice(country_agents)
                self.cooperate_with(other)
                self.send_public_message(self.evaluate_message_content('money'), channel)

        company_agents = [agent for agent in self.model.schedule.agents if isinstance(agent, CompanyAgent) and agent is not self]
        if company_agents and self.resources["money"] > 30 and self.resources["chips"] > 30:
            prospective_money = self.resources["money"] - 10
            prospective_chips = self.resources["chips"] + 10
            prospective_gdp = prospective_money + prospective_chips
            if prospective_gdp > current_gdp:
                other = random.choice(company_agents)
                self.cooperate_with(other)
                self.send_public_message(self.evaluate_message_content('money'), channel)

        self.send_public_message(self.evaluate_message_content('money'), channel)

    def step(self):
        self.choose_action()
        self.prev_resources = self.resources.copy()  # Save current resource levels for the next time step
        self.gdp = self.calculate_gdp()
    
