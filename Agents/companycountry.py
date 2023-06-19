import random
from mesa import Agent
from mesa.time import RandomActivation
import yaml

class CompanyAgent(Agent):
    def __init__(self, unique_id, model, country_agent, company_name):
        super().__init__(unique_id, model)

        # Load yaml file
        with open('Agents/agent_config.yaml') as yaml_file:
            self.data = yaml.safe_load(yaml_file)

        company_data = self.data["CompanyAgent"]

        self.talent = random.randint(*company_data["talent_range"]) 
        self.resources = company_data["initial_resources"].copy()
        self.prev_resources = self.resources.copy() 
        self.country_agent = country_agent 
        self.company_name = company_name  
        self.capabilities_score = 0
        self.public_opinion = 0
        self.partners = []
        
        self.influence = company_data["influence"]
        self.project_launch_threshold = company_data["project_launch_threshold"]
        self.government_lobby_money_threshold = company_data["government_lobby_money_threshold"]
        self.cooperation_thresholds = company_data["cooperation_thresholds"]
        self.project_launch_cost = company_data["project_launch_cost"]
        self.government_lobby_talent_threshold = company_data["government_lobby_talent_threshold"]
        self.competition_percentage = company_data["competition_percentage"]
        #print(f'Created CompanyAgent with id {self.unique_id}')
    
    def add_partner(self, partner):
        """
        Add a partner to this company's list of partners.

        Args:
        partner (CompanyAgent): The company to add as a partner.

        Returns:
        None
        """
        # Check if the partner is already in the list
        if partner not in self.partners:
            self.partners.append(partner)

    def report(self):
        return {'Talent': self.talent,
                'Company Name': self.company_name,}

    def get_country(self):
        return self.country_agent.country

    def increase_capabilities(self):
      #increase capabilities score
      self.capabilities_score += self.resources["chips"] * 0.1

    def cooperate_with(self, other_agent):
        if (self.resources["money"] > self.cooperation_thresholds["money"] and self.cooperation_thresholds["chips"]):
            self.resources["money"] -= self.cooperation_thresholds["money"]
            other_agent.resources["chips"] -= self.cooperation_thresholds["chips"]

            # Decrease anxiety score due to successful cooperation
            self.public_opinion -= 1
            other_agent.public_opinion -= 1

            return True  # Cooperation was successful
        else:
            return False  # Cooperation failed due to insufficient resources

    def send_private_message(self, message, receiver):
     # Sends a private message without distortion
        message_content = self.evaluate_message_content(message)
        receiver.receive_message(message_content, self)


 #   def send_public_message(self, message, channel):
 #       message_content = self.evaluate_message_content(message)
 #       distorted_message = self.model.communication_channels[channel].distort_message(message_content)
 #       for agent in self.model.schedule.agents: 
 #           agent.receive_message(distorted_message, self)


    def send_public_message(self, message_type):
        message_content = self.evaluate_message_content(message_type)
     # Iterate over all communication channels in the model
        for channel in self.model.communication_channels.keys():
            # Distort the message using the model's method
            distorted_message = self.model.communication_channels[channel].distort_message(message_content)
            # Send the distorted message to all agents
            for agent in self.model.schedule.agents:
                # Only send the message if the agent has a 'receive_message' method
                if hasattr(agent, "receive_message") and callable(getattr(agent, "receive_message")):
                    try:
                        agent.receive_message(distorted_message, self)
                    except TypeError:
                    # The agent's receive_message method does not accept the correct arguments
                        continue


  
    def receive_message(self, message, sender):
        # Calculate the influence factor. If the sender is a CompanyAgent, use its influence, otherwise use 1.
        influence_factor = sender.influence if isinstance(sender, CompanyAgent) else 1

        # Update public opinion score based on the message content
        if "More Money" in message or "More Chips" in message:
            self.public_opinion -= 1 * influence_factor
        elif "Less Money" in message or "Less Chips" in message:
            self.public_opinion += 1 * influence_factor


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


    def launch_project(self):
        if self.resources["money"] >= self.project_launch_cost:  # Assuming launching a project requires 30 money
            self.resources["money"] -= self.project_launch_cost
            self.increase_capabilities()  # Launching a project increases capabilities

            # This decreases the country's level. Decrease own public opinion level, using a percentage decrease for demonstration
            self.country_agent.public_opinion *= 0.9
            self.public_opinion *= 0.9
            # Increase anxiety level of other agents
            for agent in self.model.schedule.agents:
                if isinstance(agent, CountryAgent) and agent.unique_id != self.unique_id + 1:
                    agent.public_opinion += self.capabilities_score * 0.01  # Using capabilities score as a factor
            for channel in self.model.communication_channels.keys():
                self.send_public_message(self.evaluate_message_content('money'))
            return True  # Successfully launched project
        else:
            # Increase own PO and country level if project fails
            self.country_agent.public_opinion += 1
            self.public_opinion += 1 
            for channel in self.model.communication_channels.keys():
                self.send_public_message(self.evaluate_message_content('money'))

            return False  # Failed to launch project due to insufficient money
       

    def lobby_government(self):
        if self.talent >=self.government_lobby_talent_threshold:  # Lobbying government requires talent score >= 5
            # Lobbying government might increase resources
            self.resources["money"] += random.randint(10, 20)  # Increase in money
            self.resources["chips"] += random.randint(5, 10)  # Increase in chips
            for channel in self.model.communication_channels.keys():
                self.send_public_message(self.evaluate_message_content('money'))
            return True  # Successfully lobbied government
        for channel in self.model.communication_channels.keys():
            self.send_public_message(self.evaluate_message_content('money'))
        return False  # Failed to lobby government due to insufficient talent

    def compete_with(self, other_company):
        # Companies compete based on their capabilities
        if self.capabilities_score > other_company.capabilities_score:
            # Winning company takes some resources from the losing company
            self.resources["money"] += other_company.resources["money"] * 0.1  # Takes 10% of other's money
            other_company.resources["money"] *= 0.9  # Loses 10% of money
            for channel in self.model.communication_channels.keys():
                self.send_public_message(self.evaluate_message_content('money'))
            return True  # This company wins
        for channel in self.model.communication_channels.keys():
            self.send_public_message(self.evaluate_message_content('money'))
        return False  # This company loses
    
        self.send_public_message(self.evaluate_message_content('money'))


    def expected_gain_launch_project(self):
            # Assume that the expected gain from launching a project is proportional to the capabilities score
         # and the number of chips
        if self.resources["money"] >= self.project_launch_cost:
            return self.capabilities_score * 2 + self.resources["chips"]
        else:
            return 0

    def expected_gain_lobby_government(self):
        # Assume that the expected gain from lobbying the government is proportional to the talent
        if self.resources["money"] <= self.government_lobby_money_threshold and self.talent > self.government_lobby_talent_threshold:
            return self.talent * 2  # The number 2 is arbitrary and can be adjusted
        else:
            return 0

    def expected_gain_cooperate_with(self, other):
        # Assume that the expected gain from cooperation is proportional to the sum of the agent's and the other agent's resources
        if (self.resources["money"] > self.cooperation_thresholds["money"] and self.resources["chips"] > self.cooperation_thresholds["chips"]):
            return sum(self.resources.values()) + sum(other.resources.values())
        else:
            return 0


    def choose_action(self):
        # Find all other company agents
        other_companies = [agent for agent in self.model.schedule.agents if isinstance(agent, CompanyAgent) and agent is not self]

        # Check if there are any other companies
        if not other_companies:
            other_company = None  # No other companies to cooperate with
        else:
            # Choose a random company to cooperate with
            other_company = random.choice(other_companies)

        # Calculate the average resources of other companies
        average_money = sum(agent.resources["money"] for agent in other_companies) / len(other_companies) if other_companies else 0
        average_chips = sum(agent.resources["chips"] for agent in other_companies) / len(other_companies) if other_companies else 0

        # Calculate the resource factors, which are greater than 1 if the agent has less resources than average, and less than 1 otherwise
        money_factor = 1 + (average_money - self.resources["money"]) / average_money if average_money > 0 else 1
        chips_factor = 1 + (average_chips - self.resources["chips"]) / average_chips if average_chips > 0 else 1

        actions = {
            'launch_project': (self.expected_gain_launch_project() * money_factor * chips_factor, self.launch_project),
            'lobby_government': (self.expected_gain_lobby_government() * money_factor, self.lobby_government),
            'cooperate_with_country': (self.expected_gain_cooperate_with(self.country_agent) * money_factor * chips_factor, self.cooperate_with, self.country_agent),
            'cooperate_with_company': (other_company and self.expected_gain_cooperate_with(other_company) * money_factor * chips_factor, self.cooperate_with, other_company)
        }

    # Choose the action with the highest expected gain
        best_action, best_value = max(actions.items(), key=lambda item: item[1][0] if item[1] else -1)

        if best_value and len(best_value) == 3:  # If the action requires another agent, call the action with the other agent as an argument
            best_value[1](best_value[2])
        elif best_value:  # Otherwise, call the action without arguments
            best_value[1]()




    def step(self):
        #print(f'Step function called for agent {self.unique_id}')
        self.choose_action()


class CountryAgent(Agent):
    def __init__(self, unique_id, model, country, silicon_export_rate=0, processing_capacity=0):
        super().__init__(unique_id, model)

        # Load yaml file
        with open('Agents/agent_config.yaml') as yaml_file:
            data = yaml.safe_load(yaml_file)


        country_data = data["CountryAgent"]

        self.resources = country_data["initial_resources"].copy() 
        self.country = country  # Country the agent belongs to
        self.public_opinion = 0  # The anxiety level of the agent
        self.company = None  # The CompanyAgent associated with this country, initialized to None
        self.debt = 0
        self.gdp = 0  # Initialize GDP to 0
        self.prev_resources = self.resources.copy() 
        self.silicon_export_rate = silicon_export_rate
        self.processing_capacity = processing_capacity # Copy of resource levels at the previous time step
        self.research_capacity = 0

        self.decision_thresholds = country_data["decision_thresholds"]
        self.cooperation_thresholds = country_data["cooperation_thresholds"]
        self.sanctions_cost = country_data["sanctions_cost"]
        self.sanctions_percentage = country_data["sanctions_percentage"]
        self.alliance_cost = country_data["alliance_cost"]
        self.alliance_gain = country_data["alliance_gain"]
        self.research_investment_cost = country_data["research_investment_cost"]
        self.research_capacity_gain = country_data["research_capacity_gain"]

        
    def report(self):
        return {'Country': self.country,}
    
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
        receiver.receive_message(message_content, self)

    def send_public_message(self, message_type):    
        message_content = self.evaluate_message_content(message_type)
        # Iterate over all communication channels in the model
        for channel in self.model.communication_channels.keys():
        # Distort the message using the model's method
            distorted_message = self.model.communication_channels[channel].distort_message(message_content)
            # Send the distorted message to all agents
            for agent in self.model.schedule.agents:
                # Only send the message if the agent has a 'receive_message' method
                if hasattr(agent, "receive_message") and callable(getattr(agent, "receive_message")):
                    try:
                        agent.receive_message(distorted_message, self)
                    except TypeError:
                        # The agent's receive_message method does not accept the correct arguments
                        continue


  
    def receive_message(self, message, sender):
        # Calculate the influence factor. If the sender is a CompanyAgent, use its influence, otherwise use 1.
        influence_factor = sender.influence if isinstance(sender, CompanyAgent) else 1

        # Update public opinion score based on the message content
        if "More Money" in message or "More Chips" in message:
            self.public_opinion -= 1 * influence_factor
        elif "Less Money" in message or "Less Chips" in message:
            self.public_opinion += 1 * influence_factor


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

    def impose_sanctions(self, other):
      #Implement the logic of imposing sanctions
      ### add probability of inherence
      if self.resources["money"] > self.sanctions_cost: #sanctions require money
          self.resources["money"] -= self.sanctions_cost #pay for the sanctions
          # ^ does this make sense?
          other.resources["money"] -= other.resources["money"] * self.sanctions_percentage  # Other agent loses 20% of money
          for channel in self.model.communication_channels.keys():
            self.send_public_message(self.evaluate_message_content('money'))
          return True #succesfully imposed sanctions
      else:
          for channel in self.model.communication_channels.keys():
            self.send_public_message(self.evaluate_message_content('money'))
          return False #failed to impose sanctions

    def invest_in_research(self):
        """Invest in research and increase research capacity."""
        self.resources["money"] -= self.research_investment_cost
        self.research_capacity += self.research_capacity_gain
        # If there is a company affiliated with this country, they also benefit from the research investment
        if self.company:
            self.company.resources["money"] += self.research_capacity_gain
        self.send_public_message(self.evaluate_message_content('money')) 

    def expected_gain_invest_in_research(self):
        if self.resources["money"] > self.research_investment_cost:
            return self.research_capacity_gain
        else:
            return 0
    def expected_gain_form_alliance(self):
        """Calculate the expected gain from forming an alliance."""

        # Calculate the potential gain as the alliance_gain minus the alliance_cost
        potential_gain = self.alliance_gain - self.alliance_cost

        # If the agent doesn't have enough money to pay the alliance cost, the potential gain is negative
        if self.resources["money"] < self.alliance_cost:
            return -potential_gain

        # If there are no other countries to form an alliance with, the potential gain is 0
        if not any(isinstance(agent, CountryAgent) and agent is not self for agent in self.model.schedule.agents):
            return 0

        # Otherwise, return the potential gain
        return potential_gain


    def expected_gain_impose_sanctions(self):
        """Calculate the expected gain from imposing sanctions."""

        # Calculate the potential gain as the sanctions_percentage times the total money of all other countries
        potential_gain = self.sanctions_percentage * sum(agent.resources["money"] for agent in self.model.schedule.agents if isinstance(agent, CountryAgent) and agent is not self)

        # If the agent doesn't have enough money to pay the sanctions cost, the potential gain is negative
        if self.resources["money"] < self.sanctions_cost:
            return -potential_gain

        # Otherwise, return the potential gain
        return potential_gain

    def form_alliance(self, other):   
        """Form an alliance with another country and share the benefit."""
        # Form an alliance
        self.resources["money"] -= self.alliance_cost
        self.research_capacity += self.alliance_gain

        # The other country also benefits from the alliance
        other.resources["money"] += self.alliance_gain

        self.send_public_message(self.evaluate_message_content('money')) 

        return True  # Successfully formed an alliance

    def choose_action(self):
        # Find all other country agents
        other_countries = [agent for agent in self.model.schedule.agents if isinstance(agent, CountryAgent) and agent is not self]

        # Check if there are any other countries
        if not other_countries:
            other_country = None  # No other countries to take action with
        else:
            # Choose a random country to take action with
            other_country = random.choice(other_countries)

        # Calculate the average resources of other countries
        average_money = sum(agent.resources["money"] for agent in other_countries) / len(other_countries)
        average_chips = sum(agent.resources["chips"] for agent in other_countries) / len(other_countries)

        # Calculate the resource factors, which are greater than 1 if the agent has less resources than average, and less than 1 otherwise
        money_factor = 1 + (average_money - self.resources["money"]) / average_money if average_money > 0 else 1
        chips_factor = 1 + (average_chips - self.resources["chips"]) / average_chips if average_chips > 0 else 1

        # Calculate the expected gain of each action, multiplied by the resource factors
        actions = {
            'invest_in_research': (self.expected_gain_invest_in_research() * money_factor * chips_factor, self.invest_in_research),
            'form_alliance': (self.expected_gain_form_alliance() * money_factor, self.form_alliance),
            'impose_sanctions': (self.expected_gain_impose_sanctions() * money_factor, self.impose_sanctions)
        }

    # Choose the action with the highest expected gain
        best_action, best_value = max(actions.items(), key=lambda item: item[1][0])

        if best_action == 'invest_in_research':
            best_value[1]()  # call invest_in_research()
        elif best_action == 'form_alliance' and other_country:
            best_value[1](other_country)  # call form_alliance(other_country)
        elif best_action == 'impose_sanctions' and other_country:
            best_value[1](other_country)  # call impose_sanctions(other_country)


    def step(self):
        self.choose_action()
        self.prev_resources = self.resources.copy()  # Save current resource levels for the next time step
        self.gdp = self.calculate_gdp()
    
class NvidiaAgent(CompanyAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = 'Nvidia'
        self.talent = random.randint(*self.data["CompanyAgent"]["Nvidia"]["talent_range"])
        self.resources = self.data["CompanyAgent"]["Nvidia"]["initial_resources"].copy()

    def order_chips_from_TSMC(self):
        # Find the TSMC agent in the model's schedule
        TSMC_agent = None
        for agent in self.model.schedule.agents:
            if isinstance(agent, TSMCAgent):
                TSMC_agent = agent
                break

        if TSMC_agent is None:
            raise Exception("TSMC agent not found in the model's schedule.")

        # Calculate quantity of chips to order
        # We'll use 10% of the available money, and 5 chips per point of capabilities
        quantity = int(self.resources["money"] * 0.1) + self.capabilities_score * 5

        # Calculate the cost of the chips (assuming 1 chip costs 10 money)
        cost = quantity * 10

        # Check if Nvidia has enough money
        if self.resources["money"] >= cost:
            # Subtract money from Nvidia and add chips
            self.resources["money"] -= cost
            self.resources["chips"] += quantity

            # Add money to TSMC
            TSMC_agent.resources["money"] += cost
        else:
            raise Exception("Nvidia does not have enough resources to complete the transaction.")



class TSMCAgent(CompanyAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = 'TSMC'
        self.talent = random.randint(*self.data["CompanyAgent"]["TSMC"]["talent_range"])
        self.resources = self.data["CompanyAgent"]["TSMC"]["initial_resources"].copy()


class SMICAgent(CompanyAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = 'SMIC'
        self.talent = random.randint(*self.data["CompanyAgent"]["SMIC"]["talent_range"])
        self.resources = self.data["CompanyAgent"]["SMIC"]["initial_resources"].copy()


class InfineonAgent(CompanyAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = 'Infineon'
        self.talent = random.randint(*self.data["CompanyAgent"]["Infineon"]["talent_range"])
        self.resources = self.data["CompanyAgent"]["Infineon"]["initial_resources"].copy()

class RenesasAgent(CompanyAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = 'Renesas'
        self.talent = random.randint(*self.data["CompanyAgent"]["Renesas"]["talent_range"])
        self.resources = self.data["CompanyAgent"]["Renesas"]["initial_resources"].copy()
