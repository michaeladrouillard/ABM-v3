import random
from mesa import Agent
from mesa.time import RandomActivation

class CountryAgent(Agent):
    def __init__(self, unique_id, model, country):
        super().__init__(unique_id, model)
        self.resources = {"money": 100, "chips": 50}  # Initial resources
        self.country = country  # Country the agent belongs to
        self.anxiety_score = 0  # The anxiety level of the agent
        self.company = None  # The CompanyAgent associated with this country, initialized to None
        self.debt = 0
        self.gdp = 0  # Initialize GDP to 0
    
    def set_company(self, company_agent):
        self.company = company_agent  # Associate a CompanyAgent with this CountryAgent
        self.gdp = self.calculate_gdp()  # Update GDP after company agent is set

    
    def calculate_gdp(self):
        """Calculate the GDP based on the resources of the country and its affiliated company."""
        if self.company:
            company_resources = self.company.resources["money"] + self.company.resources["chips"]
        else:
            company_resources = 0
        country_resources = self.resources["money"] + self.resources["chips"]
        return company_resources + country_resources

    def approve_project(self, project_cost):
        self.debt += project_cost

    def send_private_message(self, message, receiver):
        # Sends a private message without 
        message_content = self.evaluate_message_content(message)
        receiver.receive_message(message)

    def send_public_message(self, message, channel):
        # Sends a public message through a communication 
        message_content = self.evaluate_message_content(message)
        distorted_message = self.model.communication_channels[channel].distort_message(message)
        for agent in self.model.schedule.agents:  # The message is received by all agents
            agent.receive_message(distorted_message)
  
    def receive_message(self, message):   
        # A simple example of receiving a message: change anxiety level based on the message content
        if "High Money" in message or "Very High Money" in message or "High Chips" in message or "Very High Chips" in message:
            self.anxiety_score += 1
        elif "Low Chips" in message:
            self.anxiety_score -= 1

    def evaluate_message_content(self, message_type):
        """ Evaluate message content based on the message type and current resources. """
        if message_type == 'money':
            if self.resources['money'] < 50:
                return 'Low Money'
            elif self.resources['money'] < 100:
                return 'High Money'
            else:
                return 'Very High Money'
        elif message_type == 'chips':
            if self.resources['chips'] < 20:
                return 'Low Chips'
            elif self.resources['chips'] < 50:
                return 'High Chips'
            else:
                return 'Very High Chips'
        else:
            return ''

    def cooperate_with(self, other_agent):
        if isinstance(other_agent, CompanyAgent):
            # Define the logic of cooperation with a company here.
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
            # Define the logic of cooperation with another country here.
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
        if self.resources["money"] > 30 and self.resources["chips"] < 20:  # lowered the thresholds
          other = random.choice([agent for agent in self.model.schedule.agents if agent is not self])
          self.impose_sanctions(other)
        elif self.anxiety_score > 7:  # Assuming a high anxiety level is above 7
          # Make riskier decisions, e.g., approve a high cost project by going into debt
          self.resources['money'] -= 60
          self.approve_project(60)  # Just for demonstration, you can modify according to your needs
        elif self.gdp < 5:  # If the country's GDP is less than 5 trillion dollars
            # Make riskier decisions, e.g., approve a high cost project by going into debt
            self.resources['money'] -= 60
            self.approve_project(60)
        elif len([agent for agent in self.model.schedule.agents if agent is not self]) > 0:
            other = random.choice([agent for agent in self.model.schedule.agents if agent is not self])
            self.cooperate_with(other)
        else:
            message_type = random.choice(['money', 'chips'])
            message_content = self.evaluate_message_content(message_type)
            receiver = random.choice([agent for agent in self.model.schedule.agents if agent is not self])
            self.send_private_message(message_content, receiver)

    def step(self):
        self.choose_action()