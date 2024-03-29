import random
from mesa import Agent
from mesa.time import RandomActivation
import yaml
from collections import deque
import math
import logging
logging.basicConfig(filename='agent_actions.log', level=logging.INFO)


import random
from mesa import Agent
from mesa.time import RandomActivation
import yaml
import numpy as np


class PeopleAgent(Agent):
    def __init__(self, unique_id, model):
        self.unique_id = unique_id
        self.model = model

    def provide_data(self):
        # In this simple example, it just provides a constant amount each time it's called.
        return 1000

    def step(self):
        self.provide_data()

class CompanyAgent(Agent):
    def __init__(self, unique_id, model, country_agent, company_name):
        super().__init__(unique_id, model)
        self.launch_project_count = 0
        self.lobby_government_count = 0
        self.compete_with_count = 0
        with open('Agents/agent_config.yaml') as yaml_file:
            self.data = yaml.safe_load(yaml_file)

        self.company_data = self.data["CompanyAgent"]

        self.talent = random.randint(*self.company_data["talent_range"]) 
        self.resources = self.company_data["initial_resources"].copy()
        self.prev_resources = self.resources.copy() 
        self.money_history = []  # List to keep track of money over time
        self.lookback_steps = self.company_data["lookback_steps"]  # Lookback steps for trend analysis
        self.optimization_horizon = 1  # Initialize optimization horizon as 1
        self.country_agent = country_agent 
        self.company_name = company_name  
        self.capabilities_score = 0
        self.partners = []
        self.chip_price_history = [] 
        self.chips_in_stock = 0
        self.order_book = []

        self.influence = self.company_data["influence"]
        self.project_launch_threshold = self.company_data["project_launch_threshold"]
        self.government_lobby_money_threshold = self.company_data["government_lobby_money_threshold"]
        self.cooperation_thresholds = self.company_data["cooperation_thresholds"]
        self.project_launch_cost = self.company_data["project_launch_cost"]
        self.government_lobby_talent_threshold = self.company_data["government_lobby_talent_threshold"]
        self.competition_percentage = self.company_data["competition_percentage"]
        self.history = {"launch_project": [], "lobby_government": [], "cooperate_with_country": [], "cooperate_with_company": [], "compete_with_company": []}

    def calculate_expenses(self):
        # Use percentages or fixed values from the company_data as cost factors
        rd_cost_factor = self.company_data["rd_cost_factor"]
        production_cost_factor = self.company_data["production_cost_factor"]
        marketing_cost_factor = self.company_data["marketing_cost_factor"]
        administration_cost_factor = self.company_data["administration_cost_factor"]
        logistics_cost_factor = self.company_data["logistics_cost_factor"]
        infrastructure_cost_factor = self.company_data["infrastructure_cost_factor"]
        personnel_cost_factor = self.company_data["personnel_cost_factor"]


        # The expenses are calculated as a percentage of the company's monetary resources
        rd_expense = self.resources["money"] * rd_cost_factor
        production_expense = self.resources["money"] * production_cost_factor
        marketing_expense = self.resources["money"] * marketing_cost_factor
        administration_expense = self.resources["money"] * administration_cost_factor
        logistics_expense = self.resources["money"] * logistics_cost_factor
        infrastructure_expense = self.resources["money"] * infrastructure_cost_factor
        personnel_expense = self.resources["money"] * personnel_cost_factor

        total_expenses = personnel_expense + rd_expense + production_expense + marketing_expense + administration_expense + logistics_expense + infrastructure_expense

        # Deduct expenses from the company's resources, allowing the money to go negative to represent debt
        self.resources["money"] -= total_expenses
        print(f"{self.company_name} Expenses:")
        print(f"R&D: {rd_expense}")
        print(f"Production: {production_expense}")
        print(f"Marketing: {marketing_expense}")
        print(f"Administration: {administration_expense}")
        print(f"Logistics: {logistics_expense}")
        print(f"Infrastructure: {infrastructure_expense}")
        print(f"Total expenses: {total_expenses}")
        print(f"Remaining money (including debt): {self.resources['money']}")

        return total_expenses


    def set_price(self, quantity):
            # Calculate the price of the chips based on the demand and supply
            # Use the historical price if available
            if self.chip_price_history:
                avg_past_price = sum(self.chip_price_history) / len(self.chip_price_history)
            else:
                avg_past_price = 20  # Initial price if no historical price available

            # Price adjustment based on demand and supply
            price_adj = len(self.order_book) - self.chips_in_stock / 1000

            # Competition factor, assuming more competition leads to lower prices
            competition_factor = 1 - 0.01 * len(self.model.schedule.agents)

        # Calculate the price per chip
            price_per_chip = avg_past_price + price_adj * competition_factor

        # Calculate the total price
            price = quantity * price_per_chip

            return price
        
    def update_trend_and_horizon(self):
        # Update the money history
        if len(self.money_history) >= self.lookback_steps:
            self.money_history.pop(0)  # Remove the oldest value if we've reached the desired history length
        self.money_history.append(self.resources["money"])  # Add the current money value

        # Calculate the trend based on differences in money
        diff = [j-i for i, j in zip(self.money_history[:-1], self.money_history[1:])]

        # Based on the trend, set the optimization horizon
        if all(d < 0 for d in diff):  # All differences are negative, money is decreasing
            self.optimization_horizon = 1  # Optimize for the next step
        elif all(d >= 0 for d in diff):  # All differences are non-negative, money is increasing or stable
            self.optimization_horizon = self.lookback_steps  # Optimize further into the future
        else:  # Mixed trend
            self.optimization_horizon = 1  # You can set this based on your preference

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

    def increase_capabilities(self):
      #increase capabilities score
      self.capabilities_score += self.resources["chips"] * 0.1 + self.talent * 0.1

    def cooperate_with(self, other_agent):
        if (self.resources["money"] > self.cooperation_thresholds["money"] and self.cooperation_thresholds["chips"]):
            self.resources["money"] -= self.cooperation_thresholds["money"]

            return True  # Cooperation was successful
        else:
            return False  # Cooperation failed due to insufficient resources

    def send_private_message(self, message, receiver):
     # Sends a private message without distortion
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
        self.launch_project_count += 1
        previous_money = self.resources["money"]
        previous_chips = self.resources["chips"]
        if self.resources["money"] >= self.project_launch_cost:  
            self.resources["money"] -= self.project_launch_cost
            self.increase_capabilities()  # Launching a project increases capabilities

            # Logic for sending messages
            for agent in self.model.schedule.agents:
                if isinstance(agent, CountryAgent) and agent.unique_id != self.unique_id + 1:
                    self.capabilities_score * 0.01  # Using capabilities score as a factor
            for channel in self.model.communication_channels.keys():
                self.send_public_message(self.evaluate_message_content('money'))
            
            #Recording the net change
            net_change = self.resources["money"] - previous_money, self.resources["chips"] - previous_chips
            self.history["launch_project"].append(net_change)
            return True  # Successfully launched project
        else:
            for channel in self.model.communication_channels.keys():
                self.send_public_message(self.evaluate_message_content('money'))
            net_change = self.resources["money"] - previous_money, self.resources["chips"] - previous_chips
            self.history["launch_project"].append(net_change)
            return False  # Failed to launch project due to insufficient money


    def lobby_government(self):
        self.lobby_government_count += 1
        if self.talent >= self.government_lobby_talent_threshold:  
            # Request the government for resources
            potential_gain = random.randint(10, 20), random.randint(5, 10)  # Potential increase in money and chips
            self.country_agent.receive_lobby_request(self, potential_gain)
            return True  # Successfully lobbied government
        return False 

    def compete_with(self, other_company):
        self.compete_with_count += 1
        previous_money = self.resources["money"]
        previous_chips = self.resources["chips"]
        # Companies compete based on their capabilities
        if self.capabilities_score > other_company.capabilities_score:
            # Winning company takes some resources from the losing company
            self.resources["money"] += other_company.resources["money"] * 0.1  # Takes 10% of other's money
            other_company.resources["money"] *= 0.9  # Loses 10% of money
            for channel in self.model.communication_channels.keys():
                self.send_public_message(self.evaluate_message_content('money'))
            net_change = self.resources["money"] - previous_money, self.resources["chips"] - previous_chips
            self.history["compete_with_company"].append((other_company.unique_id, net_change))
            return True  # This company wins
        for channel in self.model.communication_channels.keys():
            self.send_public_message(self.evaluate_message_content('money'))
        net_change = self.resources["money"] - previous_money, self.resources["chips"] - previous_chips
        self.history["compete_with_company"].append((other_company.unique_id, net_change))
        self.send_public_message(self.evaluate_message_content('money'))      
        return False  # This company loses


    def expected_gain_compete_with(self, other_company):
        if self.history["compete_with_company"]:
            compete_with_same_company_history = [(company_id, net_money + net_chips) for company_id, (net_money, net_chips) in self.history["compete_with_company"] if company_id == other_company.unique_id]
            if compete_with_same_company_history:
                # Compute a weighted average of past gains, with more recent gains weighted more heavily
                weights = [i+1 for i in range(len(compete_with_same_company_history))]
                avg_past_gain = sum(gain * weight for (_, gain), weight in zip(compete_with_same_company_history, weights)) / sum(weights)  
                # The win rate is the percentage of past competitions that resulted in a gain
                win_rate = sum(1 for _, net_change in compete_with_same_company_history if net_change > 0) / len(compete_with_same_company_history)
            else:
                avg_past_gain = 0
                win_rate = 0.5
        else:
            avg_past_gain = 0
            win_rate = 0.5

        potential_gain = other_company.resources["money"] * 0.1
        expected_gain = win_rate * potential_gain + avg_past_gain
        noise = np.random.normal(0, abs(expected_gain) * 0.1)  # Assuming the standard deviation is 10% of the expected gain
        expected_gain += noise
        if self.capabilities_score < other_company.capabilities_score:
            expected_gain *= 0.5

        return expected_gain



    def buy_resources_from(self, other_agent, resource_type, quantity):
        # Check if the other agent has enough of the resource
        if other_agent.resources[resource_type] >= quantity:
            # Calculate the cost of the resources (assuming each unit of resource costs 5 money)
            cost = quantity * 5

            #As it stands, you can't go into debt to buy resources
            if self.resources["money"] >= cost:
                self.resources["money"] -= cost
                self.resources[resource_type] += quantity

                # Subtract the resources from the other agent and add the money
                other_agent.resources[resource_type] -= quantity
                other_agent.resources["money"] += cost

    def expected_gain_launch_project(self):
        # Adjust the expected gain based on the average outcome of previous launches
        if self.history["launch_project"]:
            # Compute a weighted average of past gains, with more recent gains weighted more heavily
            weights = [i+1 for i in range(len(self.history["launch_project"]))]
            avg_past_gain = sum((net_money + net_chips) * weight for (net_money, net_chips), weight in zip(self.history["launch_project"], weights)) / sum(weights)
        
            # The expected gain is the average past gain
            expected_gain = avg_past_gain
        else:
            # If there's no history of launching projects, the expected gain is 0
            expected_gain = 0

        # Adding a noise term that follows a normal distribution
        noise = np.random.normal(0, abs(expected_gain) * 0.1)  # Assuming the standard deviation is 10% of the expected gain
        expected_gain += noise

        return expected_gain



    def expected_gain_lobby_government(self):
        if self.resources["money"] <= self.government_lobby_money_threshold and self.talent > self.government_lobby_talent_threshold:
            if self.history["lobby_government"]:
                # Compute a weighted average of past gains, with more recent gains weighted more heavily
                weights = [i+1 for i in range(len(self.history["lobby_government"]))]
                avg_past_gain = sum((net_money + net_chips) * weight for (net_money, net_chips), weight in zip(self.history["lobby_government"], weights)) / sum(weights)
            
                # The expected gain is the average past gain adjusted by the talent
                expected_gain = avg_past_gain * self.talent * 2
            else:
                # If there's no history of lobbying government, the expected gain is 0
                expected_gain = 0

            # Adding a noise term that follows a normal distribution
            noise = np.random.normal(0, abs(expected_gain) * 0.1)  # Assuming the standard deviation is 10% of the expected gain
            expected_gain += noise

            return expected_gain
        else:
            return 0

    def expected_gain_cooperate_with(self, other):
        if self.resources["money"] > self.cooperation_thresholds["money"] and self.resources["chips"] > self.cooperation_thresholds["chips"]:
            if self.history["cooperate_with_country"]:
                # Compute a weighted average of past gains, with more recent gains weighted more heavily
                weights = [i+1 for i in range(len(self.history["cooperate_with_country"]))]
                avg_past_gain = sum((net_money + net_chips) * weight for (net_money, net_chips), weight in zip(self.history["cooperate_with_country"], weights)) / sum(weights)
            
                # The expected gain is the average past gain adjusted by the sum of resources
                expected_gain = avg_past_gain * (sum(self.resources.values()) + sum(other.resources.values()))
            else:
                # If there's no history of cooperation with the country, the expected gain is 0
                expected_gain = 0

            # Adding a noise term that follows a normal distribution
            noise = np.random.normal(0, abs(expected_gain) * 0.1)  # Assuming the standard deviation is 10% of the expected gain
            expected_gain += noise

            return expected_gain
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

        # Risky actions
        risky_actions_multiplier = 1 if self.optimization_horizon > 1 else 0.5
        safe_actions_multiplier = 1 if self.optimization_horizon > 1 else 1.5


        actions = {
            'launch_project': (self.expected_gain_launch_project() * money_factor * chips_factor * risky_actions_multiplier, self.launch_project),
            'lobby_government': (self.expected_gain_lobby_government() * money_factor * safe_actions_multiplier, self.lobby_government),
            'cooperate_with_country': (self.expected_gain_cooperate_with(self.country_agent) * money_factor * chips_factor * safe_actions_multiplier, self.cooperate_with, self.country_agent),
            'cooperate_with_company': (other_company and self.expected_gain_cooperate_with(other_company) * money_factor * chips_factor * safe_actions_multiplier, self.cooperate_with, other_company),
            'compete_with_company': (other_company and self.expected_gain_compete_with(other_company) * money_factor * chips_factor * risky_actions_multiplier, self.compete_with, other_company)
        }

        # Choose the action with the highest expected gain
        best_action, best_value = max(actions.items(), key=lambda item: item[1][0] if item[1] else -1)

        if best_value and len(best_value) == 3:  # If the action requires another agent, call the action with the other agent as an argument
            best_value[1](best_value[2])
        elif best_value:  # Otherwise, call the action without arguments
            best_value[1]()




    def step(self):
        self.choose_action()
        self.prev_resources = self.resources.copy()
        self.update_trend_and_horizon()
   # Keep the chip price history within the lookback steps
        if len(self.chip_price_history) > self.lookback_steps:
            self.chip_price_history.pop(0)
        self.calculate_expenses()

class CountryAgent(Agent):
    def __init__(self, unique_id, model, country, silicon_export_rate=0, processing_capacity=0):
        super().__init__(unique_id, model)

        # Load yaml file
        with open('Agents/agent_config.yaml') as yaml_file:
            data = yaml.safe_load(yaml_file)


        country_data = data["CountryAgent"]

        self.resources = country_data["initial_resources"].copy() 
        self.country = country  # Country the agent belongs to
        self.company = None  # The CompanyAgent associated with this country, initialized to None
        self.debt = 0
        self.gdp = 0  # Initialize GDP to 0
        self.prev_resources = self.resources.copy() 
        self.silicon_export_rate = silicon_export_rate
        self.processing_capacity = processing_capacity # Copy of resource levels at the previous time step
        self.research_capacity = 0
        self.lobby_requests = {}  # A dictionary to hold the lobby requests of company agents


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
        company_agent.country_agent = self

    
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

    def receive_lobby_request(self, company, potential_gain):
         self.lobby_requests[company] = {
            "potential_gain": potential_gain,
            "steps_remaining": 5  # or however many steps we want the delay in decision making to be
        }
         
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
      ### we need to add probability of adherence
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

    def process_lobby_requests(self):
        for company, request_info in list(self.lobby_requests.items()):
            request_info["steps_remaining"] -= 1
            if request_info["steps_remaining"] > 0:
                continue  # Skip this request if it's not ready to be processed yet

           
            money_gain, chips_gain = request_info["potential_gain"]

            # Decision-making: probabilistic
            approval_probability = np.random.uniform(0, 1)  # Random float between 0 and 1
            if approval_probability < 0.6:  #chance of approval
                
                self.resources["money"] -= money_gain  # Decrease the country's resources
                self.resources["chips"] -= chips_gain
                company.resources["money"] += money_gain  # Increase the company's resources
                company.resources["chips"] += chips_gain

            else:

                del self.lobby_requests[company]  # Remove processed requests




    def choose_action(self):
        logging.info(f"{self.__class__.__name__} with id {self.unique_id} is performing choose_action.")
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
        self.process_lobby_requests()
        self.choose_action()
        self.prev_resources = self.resources.copy()  # Save current resource levels for the next time step
        self.gdp = self.calculate_gdp()
    
class NvidiaAgent(CompanyAgent):
    def __init__(self, unique_id, model, country_agent, company_name):
        super().__init__(unique_id, model, country_agent, company_name)
        self.type = 'Nvidia'
        self.talent = random.randint(*self.company_data["Nvidia"]["talent_range"])
        self.resources = self.company_data["Nvidia"]["initial_resources"].copy()
        self.capabilities_score = 0
        self.order_book = deque()

    def receive_payment(self, amount):
        self.resources['money'] += amount

    def receive_order(self, ordering_agent, quantity):
        self.order_book.append((ordering_agent, quantity))  # Append the new order to the order book


    def r_and_d(self):
        # Calculate the increase in capabilities score based on money and talent
        increase = self.resources["money"] * self.talent / 10
        self.capabilities_score += increase

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
        #Nvidia will always order at least one chip
        quantity = max(1, int(self.resources["money"] * 0.1) + self.capabilities_score * 2)

        # Calculate the cost of the chips (assuming 1 chip costs 10 money)
        cost = quantity * 10

        # Check if Nvidia has enough money
        if self.resources["money"] >= cost:
            # Subtract money from Nvidia
            self.resources["money"] -= cost
        # Send the payment to TSMC
            TSMC_agent.receive_payment(cost)
        # Place the order with TSMC
            TSMC_agent.receive_order(self, quantity)

    
    def receive_chips(self, quantity):
        # Add the received chips to Nvidia's resources
        self.chips_in_stock += quantity


    def step(self):
        self.order_chips_from_TSMC()
        self.r_and_d()
        self.choose_action()
        self.prev_resources = self.resources.copy()
        self.update_trend_and_horizon()
   # Keep the chip price history within the lookback steps
        if len(self.chip_price_history) > self.lookback_steps:
            self.chip_price_history.pop(0)
        self.calculate_expenses()


class IntelAgent(CompanyAgent):
    def __init__(self, unique_id, model, country_agent, company_name):
        super().__init__(unique_id, model, country_agent, company_name)
        self.type = 'Intel'
        self.talent = random.randint(*self.company_data["Intel"]["talent_range"])
        self.resources = self.company_data["Intel"]["initial_resources"].copy()
        self.capabilities_score = 0
        self.order_book = deque()

    def receive_payment(self, amount):
        self.resources['money'] += amount

    def r_and_d(self):
        # Calculate the increase in capabilities score based on money and talent
        increase = self.resources["money"] * self.talent / 10
        self.capabilities_score += increase

    def receive_order(self, ordering_agent, quantity):
        self.order_book.append((ordering_agent, quantity))  # Append the new order to the order book

    def manufacture_chips(self):
        if len(self.order_book) == 0:  # If the order book is empty, there's nothing to manufacture
            return None
        
        ordering_agent, quantity = self.order_book[0]  # Get the oldest order from the order book

        # Check how many chips intel can manufacture with its current resources
        max_quantity = min(self.resources['wafers']//2, self.resources['services'], quantity) 
        
        # If intel can't manufacture any chips, return None
        if max_quantity <= 0:
            return None

        # Subtract the used resources and add the manufactured chips
        self.resources['wafers'] -= max_quantity*2
        self.resources['services'] -= max_quantity
        self.resources['chips'] += max_quantity

        # Update the order in the order book or remove it if it's been completely fulfilled
        if max_quantity < quantity:
            self.order_book[0] = (ordering_agent, quantity - max_quantity)
        else:
            self.order_book.popleft()

        # Send the manufactured chips to the ordering agent
        self.send_chips_to(ordering_agent, max_quantity)
        # Return the details of the order that's just been processed
        return ordering_agent, max_quantity

    def send_chips_to(self, receiving_agent, quantity):
        # Subtract the chips from fabintel and add them to the receiving agent
        self.resources['chips'] -= quantity
        receiving_agent.receive_chips(quantity) 


    def step(self):
        # Find the ASMLAgent and SUMCOAgent in the model's schedule
        asml_agent = None
        siltronic_agent = None
        for agent in self.model.schedule.agents:
            if isinstance(agent, ASMLAgent) and asml_agent is None:
                asml_agent = agent
            elif isinstance(agent, SiltronicAgent) and siltronic_agent is None:
                siltronic_agent = agent

            # If we found both agents, we can break the loop
            if asml_agent is not None and siltronic_agent is not None:
                break

        self.buy_resources_from(asml_agent, 'services', 10)
        self.buy_resources_from(siltronic_agent, 'wafers', 10)
        self.manufacture_chips()
        self.r_and_d()
        self.choose_action()
        self.prev_resources = self.resources.copy()
        self.update_trend_and_horizon()
   # Keep the chip price history within the lookback steps
        if len(self.chip_price_history) > self.lookback_steps:
            self.chip_price_history.pop(0)
        self.calculate_expenses()


class TSMCAgent(CompanyAgent):
    def __init__(self, unique_id, model, country_agent, company_name):
        super().__init__(unique_id, model, country_agent, company_name)
        self.type = 'TSMC'
        self.talent = random.randint(*self.company_data["TSMC"]["talent_range"])
        self.resources = self.company_data["TSMC"]["initial_resources"].copy()
        self.order_book = deque()  # Initialize the order book as an empty deque

    def r_and_d(self):
        # Calculate the increase in capabilities score based on money and talent
        increase = self.resources["money"] * self.talent / 10
        self.capabilities_score += increase

    def receive_order(self, ordering_agent, quantity):
        self.order_book.append((ordering_agent, quantity))  # Append the new order to the order book


    def receive_payment(self, amount):
        # Add the received money to TSMC's resources
        self.resources['money'] += amount


    def manufacture_chips(self):
        if len(self.order_book) == 0:  # If the order book is empty, there's nothing to manufacture
            return None
        
        ordering_agent, quantity = self.order_book[0]  # Get the oldest order from the order book

        # Check how many chips TSMC can manufacture with its current resources
        talent_factor = self.talent / self.company_data["TSMC"]["talent_range"][1] 
        max_quantity = min(self.resources['wafers']//2, self.resources['services'], quantity) 
        max_quantity = int(max_quantity * talent_factor)

        # If TSMC can't manufacture any chips, return None
        if max_quantity <= 0:
            return None

        # Subtract the used resources and add the manufactured chips
        self.resources['wafers'] -= max_quantity*2
        self.resources['services'] -= max_quantity
        self.resources['chips'] += max_quantity

        # Update the order in the order book or remove it if it's been completely fulfilled
        if max_quantity < quantity:
            self.order_book[0] = (ordering_agent, quantity - max_quantity)
        else:
            self.order_book.popleft()


        # Send the manufactured chips to the ordering agent
        self.send_chips_to(ordering_agent, max_quantity)
        # Return the details of the order that's just been processed
        return ordering_agent, max_quantity


    def send_chips_to(self, receiving_agent, quantity):
        # Subtract the chips from TSMC and add them to the receiving agent
        self.resources['chips'] -= quantity
        receiving_agent.receive_chips(quantity) 

 
     
    def step(self):
        # Find the ASMLAgent and SUMCOAgent in the model's schedule
        asml_agent = None
        sumco_agent = None
        for agent in self.model.schedule.agents:
            if isinstance(agent, ASMLAgent) and asml_agent is None:
                asml_agent = agent
            elif isinstance(agent, SumcoAgent) and sumco_agent is None:
                sumco_agent = agent

            # If we found both agents, we can break the loop
            if asml_agent is not None and sumco_agent is not None:
                break

        # Buy tools from the ASMLAgent
        self.buy_resources_from(asml_agent, 'services', 10)

        # Buy wafers from the SUMCOAgent
        self.buy_resources_from(sumco_agent, 'wafers', 10)

        # Manufacture chips and interact with ordering agents
        self.manufacture_chips()
        self.r_and_d()
        self.choose_action()
        self.prev_resources = self.resources.copy()
        self.update_trend_and_horizon()
   # Keep the chip price history within the lookback steps
        if len(self.chip_price_history) > self.lookback_steps:
            self.chip_price_history.pop(0)
        self.calculate_expenses()
        


class AMDAgent(CompanyAgent):
    def __init__(self, unique_id, model, country_agent, company_name):
        super().__init__(unique_id, model, country_agent, company_name)
        self.type = 'AMD'
        self.talent = random.randint(*self.company_data["AMD"]["talent_range"])
        self.resources = self.company_data["AMD"]["initial_resources"].copy()
        self.capabilities_score = 0
        #print(f"AMD {self.unique_id} instantiated.")
   
    def receive_payment(self, amount):
        self.resources['money'] += amount

    def receive_order(self, ordering_agent, quantity):
        self.order_book.append((ordering_agent, quantity))  # Append the new order to the order book

    def r_and_d(self):
        # Calculate the increase in capabilities score based on money and talent
        increase = self.resources["money"] * self.talent / 10
        self.capabilities_score += increase


    def order_chips_from_GlobalFoundries(self):
        # Find the GF agent in the model's schedule
        GF_agent = None
        for agent in self.model.schedule.agents:
            if isinstance(agent, GlobalFoundriesAgent):
                GF_agent = agent
                break

        if GF_agent is None:
            raise Exception("GF agent not found in the model's schedule.")

        # Calculate quantity of chips to order
        # We'll use 10% of the available money, and 5 chips per point of capabilities
        quantity = max(1, int(self.resources["money"] * 0.1) + self.capabilities_score * 2)

        # Calculate the cost of the chips (assuming 1 chip costs 10 money)
        cost = quantity * 10

        
        if self.resources["money"] >= cost:
            self.resources["money"] -= cost
            GF_agent.receive_payment(cost)
            GF_agent.receive_order(self, quantity)
    
    def receive_chips(self, quantity):
        self.chips_in_stock += quantity


    def step(self):
        self.order_chips_from_GlobalFoundries()
        self.r_and_d()
        self.choose_action()
        self.prev_resources = self.resources.copy()
        self.update_trend_and_horizon()
   # Keep the chip price history within the lookback steps
        if len(self.chip_price_history) > self.lookback_steps:
            self.chip_price_history.pop(0)
        self.calculate_expenses()

class GlobalFoundriesAgent(CompanyAgent):
    def __init__(self, unique_id, model, country_agent, company_name):
        super().__init__(unique_id, model, country_agent, company_name)
        self.type = 'GlobalFoundries'
        self.talent = random.randint(*self.company_data["GlobalFoundries"]["talent_range"])
        self.resources = self.company_data["GlobalFoundries"]["initial_resources"].copy()
        self.order_book = deque()  # Initialize the order book as an empty deque

    def r_and_d(self):
        # Calculate the increase in capabilities score based on money and talent
        increase = self.resources["money"] * self.talent / 10
        self.capabilities_score += increase

    def receive_order(self, ordering_agent, quantity):
        self.order_book.append((ordering_agent, quantity))  # Append the new order to the order book

    def receive_payment(self, amount):
        self.resources['money'] += amount

    def manufacture_chips(self):
        if len(self.order_book) == 0:  # If the order book is empty, there's nothing to manufacture
            return None
        
        ordering_agent, quantity = self.order_book[0]  # Get the oldest order from the order book

        # Check how many chips GlobalFoundries can manufacture with its current resources
        max_quantity = min(self.resources['wafers']//2, self.resources['services'], quantity) 
        
        # If TSMC can't manufacture any chips, return None
        if max_quantity <= 0:
            return None

        # Subtract the used resources and add the manufactured chips
        self.resources['wafers'] -= max_quantity*2
        self.resources['services'] -= max_quantity
        self.resources['chips'] += max_quantity

        # Update the order in the order book or remove it if it's been completely fulfilled
        if max_quantity < quantity:
            self.order_book[0] = (ordering_agent, quantity - max_quantity)
        else:
            self.order_book.popleft()


        # Send the manufactured chips to the ordering agent
        self.send_chips_to(ordering_agent, max_quantity)
        # Return the details of the order that's just been processed
        return ordering_agent, max_quantity


    def send_chips_to(self, receiving_agent, quantity):
        self.resources['chips'] -= quantity
        receiving_agent.receive_chips(quantity) 

 
     
    def step(self):
        # Find the ASMLAgent and SUMCOAgent in the model's schedule
        asml_agent = None
        sumco_agent = None
        for agent in self.model.schedule.agents:
            if isinstance(agent, ASMLAgent) and asml_agent is None:
                asml_agent = agent
            elif isinstance(agent, SumcoAgent) and sumco_agent is None:
                sumco_agent = agent

            # If we found both agents, we can break the loop
            if asml_agent is not None and sumco_agent is not None:
                break

        # Buy tools from the ASMLAgent
        self.buy_resources_from(asml_agent, 'services', 10)

        # Buy wafers from the SUMCOAgent
        self.buy_resources_from(sumco_agent, 'wafers', 10)

        # Manufacture chips and interact with ordering agents
        self.manufacture_chips()
        self.r_and_d()
        self.choose_action()
        self.prev_resources = self.resources.copy()
        self.update_trend_and_horizon()
   # Keep the chip price history within the lookback steps
        if len(self.chip_price_history) > self.lookback_steps:
            self.chip_price_history.pop(0)
        self.calculate_expenses()



class ASMLAgent(CompanyAgent):
    def __init__(self, unique_id, model, country_agent, company_name):
        super().__init__(unique_id, model, country_agent, company_name)
        self.type = 'ASML'
        self.talent = random.randint(*self.company_data["ASML"]["talent_range"])
        self.resources = self.company_data["ASML"]["initial_resources"].copy()

    def manufacture_services(self):
        if self.resources['money'] > 0:
            self.resources['money'] -= 1
            self.resources['services'] += 1


    def step(self):
        # Manufacture services
        self.manufacture_services()
        self.choose_action()
        self.prev_resources = self.resources.copy()
        self.update_trend_and_horizon()
   # Keep the chip price history within the lookback steps
        if len(self.chip_price_history) > self.lookback_steps:
            self.chip_price_history.pop(0)
        self.calculate_expenses()



class FujimiAgent(CompanyAgent):
    def __init__(self, unique_id, model, country_agent, company_name):
        super().__init__(unique_id, model, country_agent, company_name)
        self.type = 'Fujimi'
        self.talent = random.randint(*self.company_data["Fujimi"]["talent_range"])
        self.resources = self.company_data["Fujimi"]["initial_resources"].copy()

    def manufacture_services(self):
        if self.resources['money'] > 0:
            self.resources['money'] -= 1
            self.resources['services'] += 1


    def step(self):
        self.manufacture_services()
        self.choose_action()
        self.prev_resources = self.resources.copy()
        self.update_trend_and_horizon()
   # Keep the chip price history within the lookback steps
        if len(self.chip_price_history) > self.lookback_steps:
            self.chip_price_history.pop(0)
        self.calculate_expenses()

class SiltronicAgent(CompanyAgent):
    def __init__(self, unique_id, model, country_agent, company_name):
        super().__init__(unique_id, model, country_agent, company_name)
        self.type = 'Siltronic'
        self.talent = random.randint(*self.company_data["Siltronic"]["talent_range"])
        self.resources = self.company_data["Siltronic"]["initial_resources"].copy()

    def manufacture_wafers(self):
        if self.resources['money'] > 0:
            self.resources['money'] -= 1
            self.resources['wafers'] += 10

    def step(self):
        fujimi_agent = None
        for agent in self.model.schedule.agents:
            if isinstance(agent, FujimiAgent) and fujimi_agent is None:
                fujimi_agent = agent
            # If we found both agents, we can break the loop
            if fujimi_agent is not None:
                break
        # Buy tools from the fujimi Agent
        self.buy_resources_from(fujimi_agent, 'services', 10)
        self.choose_action()
        self.prev_resources = self.resources.copy()
        self.update_trend_and_horizon()
   # Keep the chip price history within the lookback steps
        if len(self.chip_price_history) > self.lookback_steps:
            self.chip_price_history.pop(0)
        self.calculate_expenses()





class SumcoAgent(CompanyAgent):
    def __init__(self, unique_id, model, country_agent, company_name):
        super().__init__(unique_id, model, country_agent, company_name)
        self.type = 'Sumco'
        self.talent = random.randint(*self.company_data["Sumco"]["talent_range"])
        self.resources = self.company_data["Sumco"]["initial_resources"].copy()

    def manufacture_wafers(self):
        if self.resources['money'] > 0:
            self.resources['money'] -= 1
            self.resources['wafers'] += 10

    def step(self):
        self.manufacture_wafers()
        self.choose_action()
        self.prev_resources = self.resources.copy()
        self.update_trend_and_horizon()
        if len(self.chip_price_history) > self.lookback_steps:
            self.chip_price_history.pop(0)
        self.calculate_expenses()


class SKSiltronAgent(CompanyAgent):
    def __init__(self, unique_id, model, country_agent, company_name):
        super().__init__(unique_id, model, country_agent, company_name)
        self.type = 'SKSiltron'
        self.talent = random.randint(*self.company_data["SKSiltron"]["talent_range"])
        self.resources = self.company_data["SKSiltron"]["initial_resources"].copy()

    def manufacture_wafers(self):
        if self.resources['money'] > 0 and self.resources['silicon'] > 0:
            self.resources['money'] -= 1
            self.resources['silicon'] -= 1
            self.resources['wafers'] += 10

    def step(self):
        self.manufacture_wafers()
        shinetsu_agent = None
        for agent in self.model.schedule.agents:
            if isinstance(agent, ShinEtsuAgent) and shinetsu_agent is None:
                shinetsu_agent = agent
            # If we found both agents, we can break the loop
            if shinetsu_agent is not None:
                break
        self.buy_resources_from(shinetsu_agent, 'silicon', 10)
        self.choose_action()
        self.prev_resources = self.resources.copy()
        self.update_trend_and_horizon()
   # Keep the chip price history within the lookback steps
        if len(self.chip_price_history) > self.lookback_steps:
            self.chip_price_history.pop(0)
        self.calculate_expenses()


class ShinEtsuAgent(CompanyAgent):
    def __init__(self, unique_id, model, country_agent, company_name):
        super().__init__(unique_id, model, country_agent, company_name)
        self.type = 'ShinEtsu'
        self.talent = random.randint(*self.company_data["ShinEtsu"]["talent_range"])
        self.resources = self.company_data["ShinEtsu"]["initial_resources"].copy()

    def process_silicon(self):
        if self.resources['money'] > 0:
            self.resources['money'] -= 1
            self.resources['silicon'] += 10

    def step(self):
        self.process_silicon()
        self.choose_action()
        self.prev_resources = self.resources.copy()
        self.update_trend_and_horizon()
   # Keep the chip price history within the lookback steps
        if len(self.chip_price_history) > self.lookback_steps:
            self.chip_price_history.pop(0)
        self.calculate_expenses()



class CustomerAgent(CompanyAgent):
    def __init__(self, unique_id, model, country_agent=None, company_name="general", **kwargs):
        super().__init__(unique_id, model, country_agent, company_name, **kwargs)
        self.type = 'Customer'
        # Add initial resources for CustomerAgent
        self.talent = random.randint(*self.company_data["CustomerAgent"]["talent_range"])
        self.resources = self.company_data["CustomerAgent"]["initial_resources"].copy()
        self.initial_money = self.resources['money']  


    def place_order(self, quantity, manufacturing_agents):
        chosen_agent = random.choice(manufacturing_agents)
        # Assuming each manufacturing agent has a receive_order method
        chosen_agent.receive_order(self, quantity)

    def receive_chips(self, quantity):
        self.resources['chips'] += quantity

    def pay_for_order(self, manufacturing_agent, amount):
        if self.resources['money'] >= amount:
            self.resources['money'] -= amount
            manufacturing_agent.receive_payment(amount)
        else:
            pass 

    def step(self):
        self.resources['money'] = self.initial_money  # Replenish money at the start of each step
        # Collect all manufacturing agents in the model's schedule
        manufacturing_agents = []
        for agent in self.model.schedule.agents:
            if isinstance(agent, (InfineonAgent, AMDAgent, TSMCAgent, NvidiaAgent, IntelAgent, TexasInstrumentsAgent, SMICAgent, MediaTekAgent, RenesasAgent, SonyAgent, HuaHongAgent)):  # Add other manufacturing agents here
                manufacturing_agents.append(agent)
        
        # Determine number of orders to place this step
        num_orders = random.randint(5, 20)

        # Randomly select a subset of manufacturing agents to place orders with
        selected_agents = random.sample(manufacturing_agents, min(num_orders, len(manufacturing_agents)))

        # Loop over selected agents and place an order with each
        for chosen_agent in selected_agents:
            # Place order and make payment to the chosen agent
            order_quantity = random.randint(*self.company_data["CustomerAgent"]["order_range"])
            self.place_order(order_quantity, [chosen_agent])  # Pass chosen agent as a list to the place_order function
            payment_amount = chosen_agent.set_price(order_quantity)  
            self.pay_for_order(chosen_agent, payment_amount)  # Pay the chosen agent


class SamsungAgent(CompanyAgent):
    def __init__(self, unique_id, model, country_agent, company_name):
        super().__init__(unique_id, model, country_agent, company_name)
        self.type = 'Samsung'
    def receive_payment(self, amount):
        self.resources['money'] += amount
        self.calculate_expenses()


class SamsungSub(SamsungAgent):
    def __init__(self, unique_id, model, country_agent, company_name):
        super().__init__(unique_id, model, country_agent, company_name)
        self.type = 'SamsungSub'
        self.talent = random.randint(*self.company_data["SamsungSub"]["talent_range"])
        self.resources = self.company_data["SamsungSub"]["initial_resources"].copy()
        self.order_book = deque()  # Initialize the order book as an empty deque

    def receive_order(self, ordering_agent, quantity):
        self.order_book.append((ordering_agent, quantity))
    
    def r_and_d(self):
        # Calculate the increase in capabilities score based on money and talent
        increase = self.resources["money"] * self.talent / 10
        self.capabilities_score += increase

    def receive_payment(self, amount):
        self.resources['money'] += amount

    def manufacture_chips(self):
        if len(self.order_book) == 0:  # If the order book is empty, there's nothing to manufacture
            return None
        
        ordering_agent, quantity = self.order_book[0]  # Get the oldest order from the order book

        # Check how many chips it can manufacture with its current resources
        max_quantity = min(self.resources['wafers']//2, self.resources['services'], quantity) 
        
        # If it can't manufacture any chips, return None
        if max_quantity <= 0:
            return None

        # Subtract the used resources and add the manufactured chips
        self.resources['wafers'] -= max_quantity*2
        self.resources['services'] -= max_quantity
        self.resources['chips'] += max_quantity

        # Update the order in the order book or remove it if it's been completely fulfilled
        if max_quantity < quantity:
            self.order_book[0] = (ordering_agent, quantity - max_quantity)
        else:
            self.order_book.popleft()


        # Send the manufactured chips to the ordering agent
        self.send_chips_to(ordering_agent, max_quantity)
        # Return the details of the order that's just been processed
        return ordering_agent, max_quantity

    def send_chips_to(self, receiving_agent, quantity):
        self.resources['chips'] -= quantity
        receiving_agent.receive_chips(quantity) 

    def step(self):
        asml_agent = None
        sksiltron_agent = None
        for agent in self.model.schedule.agents:
            if isinstance(agent, ASMLAgent) and asml_agent is None:
                asml_agent = agent
            elif isinstance(agent, SKSiltronAgent) and sksiltron_agent is None:
                sksiltron_agent = agent

            if asml_agent is not None and sksiltron_agent is not None:
                break
        # Buy tools from the ASMLAgent
        self.buy_resources_from(asml_agent, 'services', 10)

        # Buy wafers from the SUMCOAgent
        self.buy_resources_from(sksiltron_agent, 'wafers', 10)

        # At each step, the foundry receives a random order from a 'customer'
        self.manufacture_chips()
        self.r_and_d()
        self.choose_action()
        self.prev_resources = self.resources.copy()
        self.update_trend_and_horizon()
   # Keep the chip price history within the lookback steps
        if len(self.chip_price_history) > self.lookback_steps:
            self.chip_price_history.pop(0)
        self.calculate_expenses()

class AmazonAgent(CompanyAgent):
    def __init__(self, unique_id, model, country_agent, company_name):
        super().__init__(unique_id, model, country_agent, company_name)
        self.type = 'Amazon'
        self.talent = random.randint(*self.company_data["Amazon"]["talent_range"])
        self.resources = self.company_data["Amazon"]["initial_resources"].copy()
        self.resources["data"] = 0
        self.resources["AI_models"] = 0

    def r_and_d(self):
        # Calculate the increase in capabilities score based on money and talent
        increase = self.resources["money"] * self.talent / 10
        self.capabilities_score += increase

    def generate_revenue(self):
        # Define fixed e-commerce revenue
        ### I have issues with this because amazon's main revenue thing isn't ecommerce
        ecommerce_revenue = 5000
        # Define cloud revenue per AI model
        cloud_revenue_per_model = 1000
        # Calculate total revenue
        total_revenue = ecommerce_revenue + cloud_revenue_per_model * self.resources["AI_models"]
        # Add revenue to Amazon's resources
        self.resources["money"] += total_revenue

    def order_chips_from_TSMC(self):
        TSMC_agent = None
        for agent in self.model.schedule.agents:
            if isinstance(agent, TSMCAgent):
                TSMC_agent = agent
                break

        if TSMC_agent is None:
            raise Exception("TSMC agent not found in the model's schedule.")

        # Calculate quantity of chips to order
        # We'll use 10% of the available money, and 5 chips per point of capabilities
        #Amazon will always order at least one chip
        quantity = max(1, int(self.resources["money"] * 0.1) + self.capabilities_score * 2)

        # Calculate the cost of the chips (assuming 1 chip costs 10 money)
        cost = quantity * 10

        # Check if Amazon has enough money
        if self.resources["money"] >= cost:
            self.resources["money"] -= cost
        # Send the payment to TSMC
            TSMC_agent.receive_payment(cost)
        # Place the order with TSMC
            TSMC_agent.receive_order(self, quantity)
    
    def receive_chips(self, quantity):
        # Add the received chips to Amazon's resources
        self.chips_in_stock += quantity

    def gather_data(self):
        # Can modify this to model how much data is gathered, and from where

        people_agent = None
        for agent in self.model.schedule.agents:
            if isinstance(agent, PeopleAgent):
                people_agent = agent
                break

        if people_agent is None:
            raise Exception("People agent not found in the model's schedule.")
        self.resources["data"] += people_agent.provide_data()

    def build_AI_models(self):
        TALENT_BUILD_COST = 1
        TALENT_MAINTENANCE_COST = 0.1
        maintenance_cost = TALENT_MAINTENANCE_COST * self.resources["AI_models"]
        available_talent = self.talent - maintenance_cost

        while self.resources["data"] > 0 and self.resources["chips"] > 0 and available_talent >= TALENT_BUILD_COST:
            potential_models = min(self.resources["data"], self.resources["chips"], available_talent // TALENT_BUILD_COST)

            # Use math.log10() to apply a base-10 logarithm
            models_to_build = int(math.log10(potential_models + 1))

            models_to_build = min(models_to_build, potential_models)

            self.resources["data"] -= models_to_build
            self.resources["chips"] -= models_to_build
            available_talent -= models_to_build * TALENT_BUILD_COST

            self.resources["AI_models"] += models_to_build

            if models_to_build == 0:
                break

        self.resources["talent"] = available_talent + maintenance_cost

    def step(self):
        self.order_chips_from_TSMC()
        self.r_and_d()
        self.gather_data()
        self.build_AI_models()
        self.generate_revenue()
        self.choose_action()
        self.prev_resources = self.resources.copy()
        self.update_trend_and_horizon()
   # Keep the chip price history within the lookback steps
        if len(self.chip_price_history) > self.lookback_steps:
            self.chip_price_history.pop(0)
        self.calculate_expenses()

class GoogleAgent(CompanyAgent):
    def __init__(self, unique_id, model, country_agent, company_name):
        super().__init__(unique_id, model, country_agent, company_name)
        self.type = 'Google'
        self.talent = random.randint(*self.company_data["Google"]["talent_range"])
        self.resources = self.company_data["Google"]["initial_resources"].copy()
        self.resources["data"] = 0
        self.resources["AI_models"] = 0

    def r_and_d(self):
        # Calculate the increase in capabilities score based on money and talent
        increase = self.resources["money"] * self.talent / 10
        self.capabilities_score += increase
    
    def generate_ad_revenue(self):
        # Define the fixed amount of money generated by advertising per time step
        ad_revenue = 500
        self.resources["money"] += ad_revenue

    def order_chips_from_TSMC(self):
        TSMC_agent = None
        for agent in self.model.schedule.agents:
            if isinstance(agent, TSMCAgent):
                TSMC_agent = agent
                break

        if TSMC_agent is None:
            raise Exception("TSMC agent not found in the model's schedule.")

        # Calculate quantity of chips to order
        # We'll use 10% of the available money, and 5 chips per point of capabilities
        #Google will always order at least one chip
        quantity = max(1, int(self.resources["money"] * 0.1) + self.capabilities_score * 2)

        # Calculate the cost of the chips (assuming 1 chip costs 10 money)
        cost = quantity * 10

        if self.resources["money"] >= cost:
            self.resources["money"] -= cost
        # Send the payment to TSMC
            TSMC_agent.receive_payment(cost)
        # Place the order with TSMC
            TSMC_agent.receive_order(self, quantity)
    
    def receive_chips(self, quantity):
        # Add the received chips to Google's resources
        self.chips_in_stock += quantity


    def gather_data(self):
        # Extract data from the 'people' agent
        # Can modify this to model how much data is gathered, and from where

        people_agent = None
        for agent in self.model.schedule.agents:
            if isinstance(agent, PeopleAgent):
                people_agent = agent
                break

        if people_agent is None:
            raise Exception("People agent not found in the model's schedule.")
        self.resources["data"] += people_agent.provide_data()

    def build_AI_models(self):
        TALENT_BUILD_COST = 1
        TALENT_MAINTENANCE_COST = 0.1
        maintenance_cost = TALENT_MAINTENANCE_COST * self.resources["AI_models"]
        available_talent = self.talent - maintenance_cost

        while self.resources["data"] > 0 and self.resources["chips"] > 0 and available_talent >= TALENT_BUILD_COST:
            potential_models = min(self.resources["data"], self.resources["chips"], available_talent // TALENT_BUILD_COST)

            # Use math.log10() to apply a base-10 logarithm
            models_to_build = int(math.log10(potential_models + 1))

            models_to_build = min(models_to_build, potential_models)

            self.resources["data"] -= models_to_build
            self.resources["chips"] -= models_to_build
            available_talent -= models_to_build * TALENT_BUILD_COST

            self.resources["AI_models"] += models_to_build

            if models_to_build == 0:
                break

        self.resources["talent"] = available_talent + maintenance_cost

    def step(self):
        self.order_chips_from_TSMC()
        self.r_and_d()
        self.gather_data()
        self.build_AI_models()
        self.generate_ad_revenue()
        self.choose_action()
        self.prev_resources = self.resources.copy()
        self.update_trend_and_horizon()
   # Keep the chip price history within the lookback steps
        if len(self.chip_price_history) > self.lookback_steps:
            self.chip_price_history.pop(0)
        self.calculate_expenses()

class AppleAgent(CompanyAgent):
    def __init__(self, unique_id, model, country_agent, company_name):
        super().__init__(unique_id, model, country_agent, company_name)
        self.type = 'Apple'
        self.talent = random.randint(*self.company_data["Apple"]["talent_range"])
        self.resources = self.company_data["Apple"]["initial_resources"].copy()
        self.resources["data"] = 0
        self.resources["AI_models"] = 0

    def r_and_d(self):
        # Calculate the increase in capabilities score based on money and talent
        increase = self.resources["money"] * self.talent / 10
        self.capabilities_score += increase

    def generate_revenue(self):
        # Define fixed hardware sales revenue
        hardware_revenue = 5000
        # Add revenue to Apple's resources
        self.resources["money"] += hardware_revenue

    
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
        #Qualcomm will always order at least one chip
        quantity = max(1, int(self.resources["money"] * 0.1) + self.capabilities_score * 2)

        # Calculate the cost of the chips (assuming 1 chip costs 10 money)
        cost = quantity * 10

        if self.resources["money"] >= cost:
            self.resources["money"] -= cost
        # Send the payment to TSMC
            TSMC_agent.receive_payment(cost)
        # Place the order with TSMC
            TSMC_agent.receive_order(self, quantity)


    
    def receive_chips(self, quantity):
        # Add the received chips to Apple's resources
        self.chips_in_stock += quantity


    def gather_data(self):
        # Extract data from the 'people' agent
        # Can modify this to model how much data is gathered, and from where

        people_agent = None
        for agent in self.model.schedule.agents:
            if isinstance(agent, PeopleAgent):
                people_agent = agent
                break

        if people_agent is None:
            raise Exception("People agent not found in the model's schedule.")
        self.resources["data"] += people_agent.provide_data()

    def build_AI_models(self):
        TALENT_BUILD_COST = 1
        TALENT_MAINTENANCE_COST = 0.1
        maintenance_cost = TALENT_MAINTENANCE_COST * self.resources["AI_models"]
        available_talent = self.talent - maintenance_cost

        while self.resources["data"] > 0 and self.resources["chips"] > 0 and available_talent >= TALENT_BUILD_COST:
            potential_models = min(self.resources["data"], self.resources["chips"], available_talent // TALENT_BUILD_COST)

            # Use math.log10() to apply a base-10 logarithm
            models_to_build = int(math.log10(potential_models + 1))

            models_to_build = min(models_to_build, potential_models)

            self.resources["data"] -= models_to_build
            self.resources["chips"] -= models_to_build
            available_talent -= models_to_build * TALENT_BUILD_COST

            self.resources["AI_models"] += models_to_build

            if models_to_build == 0:
                break

        self.resources["talent"] = available_talent + maintenance_cost

    def step(self):
        self.order_chips_from_TSMC()
        self.r_and_d()
        self.gather_data()
        self.build_AI_models()
        self.generate_revenue()
        self.choose_action()
        self.prev_resources = self.resources.copy()
        self.update_trend_and_horizon()
   # Keep the chip price history within the lookback steps
        if len(self.chip_price_history) > self.lookback_steps:
            self.chip_price_history.pop(0)
        self.calculate_expenses()


class MetaAgent(CompanyAgent):
    def __init__(self, unique_id, model, country_agent, company_name):
        super().__init__(unique_id, model, country_agent, company_name)
        self.type = 'Meta'
        self.talent = random.randint(*self.company_data["Meta"]["talent_range"])
        self.resources = self.company_data["Meta"]["initial_resources"].copy()
        self.resources["data"] = 0
        self.resources["AI_models"] = 0

    def r_and_d(self):
        # Calculate the increase in capabilities score based on money and talent
        increase = self.resources["money"] * self.talent / 10
        self.capabilities_score += increase

    def generate_ad_revenue(self):
        # Define the fixed amount of money generated by advertising per time step
        ad_revenue = 500
        # Add the revenue to Meta's money resources
        self.resources["money"] += ad_revenue

    def order_chips(self):
        Qualcomm_agent = None
        for agent in self.model.schedule.agents:
            if isinstance(agent, QualcommAgent):
                Qualcomm_agent = agent
                break

        if Qualcomm_agent is None:
            raise Exception("Qualcomm agent not found in the model's schedule.")

        # Calculate quantity of chips to order
        quantity = max(1, int(self.resources["money"] * 0.1) + self.capabilities_score * 2)

        # Calculate the cost of the chips (assuming 1 chip costs 10 money)
        cost = quantity * 10

        # Check if Meta has enough money
        if self.resources["money"] >= cost:
            self.resources["money"] -= cost
            # Send the payment to Qualcomm
            Qualcomm_agent.receive_payment(cost)
            # Place the order with Qualcomm
            Qualcomm_agent.receive_order(self, quantity)

    
    def receive_chips(self, quantity):
        # Add the received chips to Meta's resources
        self.chips_in_stock += quantity


    def gather_data(self):
        # Extract data from the 'people' agent
        # Can modify this to model how much data is gathered, and from where

        people_agent = None
        for agent in self.model.schedule.agents:
            if isinstance(agent, PeopleAgent):
                people_agent = agent
                break

        if people_agent is None:
            raise Exception("People agent not found in the model's schedule.")
        self.resources["data"] += people_agent.provide_data()

    def build_AI_models(self):
        TALENT_BUILD_COST = 1
        TALENT_MAINTENANCE_COST = 0.1
        maintenance_cost = TALENT_MAINTENANCE_COST * self.resources["AI_models"]
        available_talent = self.talent - maintenance_cost

        while self.resources["data"] > 0 and self.resources["chips"] > 0 and available_talent >= TALENT_BUILD_COST:
            potential_models = min(self.resources["data"], self.resources["chips"], available_talent // TALENT_BUILD_COST)

            # Use math.log10() to apply a base-10 logarithm
            models_to_build = int(math.log10(potential_models + 1))

            models_to_build = min(models_to_build, potential_models)

            self.resources["data"] -= models_to_build
            self.resources["chips"] -= models_to_build
            available_talent -= models_to_build * TALENT_BUILD_COST

            self.resources["AI_models"] += models_to_build

            if models_to_build == 0:
                break

        self.resources["talent"] = available_talent + maintenance_cost

    def step(self):
        self.r_and_d()
        self.gather_data()
        self.build_AI_models()
        self.order_chips()
        self.generate_ad_revenue()
        self.choose_action()
        self.prev_resources = self.resources.copy()
        self.update_trend_and_horizon()
   # Keep the chip price history within the lookback steps
        if len(self.chip_price_history) > self.lookback_steps:
            self.chip_price_history.pop(0)
        self.calculate_expenses()



class QualcommAgent(CompanyAgent):
    def __init__(self, unique_id, model, country_agent, company_name):
        super().__init__(unique_id, model, country_agent, company_name)
        self.type = 'Qualcomm'
        self.talent = random.randint(*self.company_data["Qualcomm"]["talent_range"])
        self.resources = self.company_data["Qualcomm"]["initial_resources"].copy()
        self.capabilities_score = 0
        self.order_book = deque()


    def receive_order(self, ordering_agent, quantity):
        self.order_book.append((ordering_agent, quantity))  # Append the new order to the order book


    def r_and_d(self):
        # Calculate the increase in capabilities score based on money and talent
        increase = self.resources["money"] * self.talent / 10
        self.capabilities_score += increase


    def order_chips(self):
        TSMC_agent = None
        SamsungSub_agent = None
        GlobalFoundries_agent = None

        for agent in self.model.schedule.agents:
            if isinstance(agent, TSMCAgent):
                TSMC_agent = agent
            elif isinstance(agent, SamsungSub):
                SamsungSub_agent = agent
            elif isinstance(agent, GlobalFoundriesAgent):
                GlobalFoundries_agent = agent

        if TSMC_agent is None:
            raise Exception("TSMC agent not found in the model's schedule.")
        if SamsungSub_agent is None:
            raise Exception("SamsungSub agent not found in the model's schedule.")
        if GlobalFoundries_agent is None:
            raise Exception("GlobalFoundries agent not found in the model's schedule.")

        # Calculate quantity of chips to order
        # We'll use 10% of the available money, and 5 chips per point of capabilities
        # Apple will always order at least one chip
        quantity = max(1, int(self.resources["money"] * 0.1) + self.capabilities_score * 2)

        # Calculate the cost of the chips (assuming 1 chip costs 10 money)
        cost = quantity * 10


        if self.resources["money"] >= cost:
            self.resources["money"] -= cost
            # Send the payment and place the order
            if TSMC_agent is not None:
                TSMC_agent.receive_payment(cost)
                TSMC_agent.receive_order(self, quantity)
            if SamsungSub_agent is not None:
                SamsungSub_agent.receive_payment(cost)
                SamsungSub_agent.receive_order(self, quantity)
            if GlobalFoundries_agent is not None:
                GlobalFoundries_agent.receive_payment(cost)
                GlobalFoundries_agent.receive_order(self, quantity)

    def receive_payment(self, amount):
        self.resources['money'] += amount
    
    def receive_chips(self, quantity):
        # Add the received chips to Qualcomm's resources
        self.chips_in_stock += quantity

    def step(self):
        self.order_chips()
        self.r_and_d()
        self.choose_action()
        self.prev_resources = self.resources.copy()
        self.update_trend_and_horizon()
   # Keep the chip price history within the lookback steps
        if len(self.chip_price_history) > self.lookback_steps:
            self.chip_price_history.pop(0)
        self.calculate_expenses()

class OpenAIAgent(CompanyAgent):
    def __init__(self, unique_id, model, country_agent, company_name):
        super().__init__(unique_id, model, country_agent, company_name)
        self.type = 'OpenAI'
        self.talent = random.randint(*self.company_data["OpenAI"]["talent_range"])
        self.resources = self.company_data["OpenAI"]["initial_resources"].copy()
        self.resources["data"] = 0
        self.resources["AI_models"] = 0

    def r_and_d(self):
        # Calculate the increase in capabilities score based on money and talent
        increase = self.resources["money"] * self.talent / 10
        self.capabilities_score += increase

    def generate_revenue(self):
        # Define licensing revenue per AI model
        ###they have a lot of investor $$$, notably from Microsoft
        licensing_revenue_per_model = 500
        # Calculate total revenue
        total_revenue = licensing_revenue_per_model * self.resources["AI_models"]
        # Add revenue to OpenAI's resources
        self.resources["money"] += total_revenue


    def order_chips(self):
        Nvidia_agent = None
        for agent in self.model.schedule.agents:
            if isinstance(agent, NvidiaAgent):
                Nvidia_agent = agent
                break

        if Nvidia_agent is None:
            raise Exception("Nvidia agent not found in the model's schedule.")

        # Calculate quantity of chips to order
        quantity = max(1, int(self.resources["money"] * 0.1) + self.capabilities_score * 2)

        # Calculate the cost of the chips (assuming 1 chip costs 10 money)
        cost = quantity * 10

        # Check if Openai has enough money
        if self.resources["money"] >= cost:
            self.resources["money"] -= cost
            # Send the payment to Nvidia
            Nvidia_agent.receive_payment(cost)
            # Place the order with Nvidia
            Nvidia_agent.receive_order(self, quantity)
    
    def receive_chips(self, quantity):
        # Add the received chips to OpenAI's resources
        self.chips_in_stock += quantity

    def gather_data(self):
        # Extract data from the 'people' agent
        # Can modify this to model how much data is gathered, and from where

        people_agent = None
        for agent in self.model.schedule.agents:
            if isinstance(agent, PeopleAgent):
                people_agent = agent
                break

        if people_agent is None:
            raise Exception("People agent not found in the model's schedule.")
        self.resources["data"] += people_agent.provide_data()

    def build_AI_models(self):
        TALENT_BUILD_COST = 1
        TALENT_MAINTENANCE_COST = 0.1
        maintenance_cost = TALENT_MAINTENANCE_COST * self.resources["AI_models"]
        available_talent = self.talent - maintenance_cost

        while self.resources["data"] > 0 and self.resources["chips"] > 0 and available_talent >= TALENT_BUILD_COST:
            potential_models = min(self.resources["data"], self.resources["chips"], available_talent // TALENT_BUILD_COST)

            # Use math.log10() to apply a base-10 logarithm
            models_to_build = int(math.log10(potential_models + 1))

            models_to_build = min(models_to_build, potential_models)

            self.resources["data"] -= models_to_build
            self.resources["chips"] -= models_to_build
            available_talent -= models_to_build * TALENT_BUILD_COST

            self.resources["AI_models"] += models_to_build

            if models_to_build == 0:
                break

        self.resources["talent"] = available_talent + maintenance_cost

    def step(self):
        self.r_and_d()
        self.gather_data()
        self.build_AI_models()
        self.order_chips()
        self.generate_revenue()
        self.choose_action()
        self.prev_resources = self.resources.copy()
        self.update_trend_and_horizon()
   # Keep the chip price history within the lookback steps
        if len(self.chip_price_history) > self.lookback_steps:
            self.chip_price_history.pop(0)
        self.calculate_expenses()

class MediaTekAgent(CompanyAgent):
    def __init__(self, unique_id, model, country_agent, company_name):
        super().__init__(unique_id, model, country_agent, company_name)
        self.type = 'MediaTek'
        self.talent = random.randint(*self.company_data["MediaTek"]["talent_range"])
        self.resources = self.company_data["MediaTek"]["initial_resources"].copy()
        self.capabilities_score = 0
        self.order_book = deque()

    def receive_payment(self, amount):
        self.resources['money'] += amount

    def receive_order(self, ordering_agent, quantity):
        self.order_book.append((ordering_agent, quantity))  # Append the new order to the order book


    def r_and_d(self):
        # Calculate the increase in capabilities score based on money and talent
        increase = self.resources["money"] * self.talent / 10
        self.capabilities_score += increase


    def order_chips_from_TSMC(self):
        # Find the TSMC agent in the model's schedule
        TSMC_agent = None
        for agent in self.model.schedule.agents:
            if isinstance(agent, TSMCAgent):
                TSMC_agent = agent
                break

        if TSMC_agent is None:
            raise Exception("TSMC agent not found in the model's schedule.")

        quantity = max(1, int(self.resources["money"] * 0.1) + self.capabilities_score * 2)

        # Calculate the cost of the chips (assuming 1 chip costs 10 money)
        cost = quantity * 10

        if self.resources["money"] >= cost:
            self.resources["money"] -= cost
        # Send the payment to TSMC
            TSMC_agent.receive_payment(cost)
        # Place the order with TSMC
            TSMC_agent.receive_order(self, quantity)
    
    def receive_chips(self, quantity):
        self.chips_in_stock += quantity
 

    def step(self):
        self.order_chips_from_TSMC()
        self.r_and_d()
        self.choose_action()
        self.prev_resources = self.resources.copy()
        self.update_trend_and_horizon()
   # Keep the chip price history within the lookback steps
        if len(self.chip_price_history) > self.lookback_steps:
            self.chip_price_history.pop(0)
        self.calculate_expenses()

class SMICAgent(CompanyAgent):
    def __init__(self, unique_id, model, country_agent, company_name):
        super().__init__(unique_id, model, country_agent, company_name)
        self.type = 'SMIC'
        self.talent = random.randint(*self.company_data["SMIC"]["talent_range"])
        self.resources = self.company_data["SMIC"]["initial_resources"].copy()
        self.order_book = deque()  # Initialize the order book as an empty deque

    def r_and_d(self):
        # Calculate the increase in capabilities score based on money and talent
        increase = self.resources["money"] * self.talent / 10
        self.capabilities_score += increase

    def receive_order(self, ordering_agent, quantity):
        self.order_book.append((ordering_agent, quantity))  # Append the new order to the order book


    def receive_payment(self, amount):
        self.resources['money'] += amount


    def manufacture_chips(self):
        if len(self.order_book) == 0:  # If the order book is empty, there's nothing to manufacture
            return None
        
        ordering_agent, quantity = self.order_book[0]  # Get the oldest order from the order book

        max_quantity = min(self.resources['wafers']//2, self.resources['services'], quantity) 
        
        # If SMIC can't manufacture any chips, return None
        if max_quantity <= 0:
            return None

        # Subtract the used resources and add the manufactured chips
        self.resources['wafers'] -= max_quantity*2
        self.resources['services'] -= max_quantity
        self.resources['chips'] += max_quantity

        # Update the order in the order book or remove it if it's been completely fulfilled
        if max_quantity < quantity:
            self.order_book[0] = (ordering_agent, quantity - max_quantity)
        else:
            self.order_book.popleft()


        # Send the manufactured chips to the ordering agent
        self.send_chips_to(ordering_agent, max_quantity)
        # Return the details of the order that's just been processed
        return ordering_agent, max_quantity


    def send_chips_to(self, receiving_agent, quantity):
        # Subtract the chips from SMIC and add them to the receiving agent
        self.resources['chips'] -= quantity
        receiving_agent.receive_chips(quantity) 
 

 
     
    def step(self):
        # Find the ASMLAgent and SUMCOAgent in the model's schedule
        asml_agent = None
        sumco_agent = None
        for agent in self.model.schedule.agents:
            if isinstance(agent, ASMLAgent) and asml_agent is None:
                asml_agent = agent
            elif isinstance(agent, SumcoAgent) and sumco_agent is None:
                sumco_agent = agent

            # If we found both agents, we can break the loop
            if asml_agent is not None and sumco_agent is not None:
                break

        # Buy tools from the ASMLAgent
        self.buy_resources_from(asml_agent, 'services', 10)

        # Buy wafers from the SUMCOAgent
        self.buy_resources_from(sumco_agent, 'wafers', 10)

        # Manufacture chips and interact with ordering agents
        self.manufacture_chips()
        self.r_and_d()
        self.calculate_expenses()
        self.choose_action()
        self.prev_resources = self.resources.copy()
        self.update_trend_and_horizon()
   # Keep the chip price history within the lookback steps
        if len(self.chip_price_history) > self.lookback_steps:
            self.chip_price_history.pop(0)
        self.calculate_expenses()

class HuaHongAgent(CompanyAgent):
    def __init__(self, unique_id, model, country_agent, company_name):
        super().__init__(unique_id, model, country_agent, company_name)
        self.type = 'HuaHong'
        self.talent = random.randint(*self.company_data["HuaHong"]["talent_range"])
        self.resources = self.company_data["HuaHong"]["initial_resources"].copy()
        self.order_book = deque()  # Initialize the order book as an empty deque

    def r_and_d(self):
        # Calculate the increase in capabilities score based on money and talent
        increase = self.resources["money"] * self.talent / 10
        self.capabilities_score += increase

    def receive_order(self, ordering_agent, quantity):
        self.order_book.append((ordering_agent, quantity))  # Append the new order to the order book

    def receive_payment(self, amount):
        # Add the received money to HuaHong's resources
        self.resources['money'] += amount


    def manufacture_chips(self):
        if len(self.order_book) == 0:  # If the order book is empty, there's nothing to manufacture
            return None
        
        ordering_agent, quantity = self.order_book[0]  # Get the oldest order from the order book

        # Check how many chips HuaHong can manufacture with its current resources
        max_quantity = min(self.resources['wafers']//2, self.resources['services'], quantity) 
        
        # If HuaHong can't manufacture any chips, return None
        if max_quantity <= 0:
            return None

        # Subtract the used resources and add the manufactured chips
        self.resources['wafers'] -= max_quantity*2
        self.resources['services'] -= max_quantity
        self.resources['chips'] += max_quantity

        # Update the order in the order book or remove it if it's been completely fulfilled
        if max_quantity < quantity:
            self.order_book[0] = (ordering_agent, quantity - max_quantity)
        else:
            self.order_book.popleft()


        # Send the manufactured chips to the ordering agent
        self.send_chips_to(ordering_agent, max_quantity)
        return ordering_agent, max_quantity


    def send_chips_to(self, receiving_agent, quantity):
        # Subtract the chips from HuaHong and add them to the receiving agent
        self.resources['chips'] -= quantity
        receiving_agent.receive_chips(quantity) 


 
     
    def step(self):
        # Find the ASMLAgent and SUMCOAgent in the model's schedule
        asml_agent = None
        sumco_agent = None
        for agent in self.model.schedule.agents:
            if isinstance(agent, ASMLAgent) and asml_agent is None:
                asml_agent = agent
            elif isinstance(agent, SumcoAgent) and sumco_agent is None:
                sumco_agent = agent

            # If we found both agents, we can break the loop
            if asml_agent is not None and sumco_agent is not None:
                break

        # Buy tools from the ASMLAgent
        self.buy_resources_from(asml_agent, 'services', 10)

        # Buy wafers from the SUMCOAgent
        self.buy_resources_from(sumco_agent, 'wafers', 10)

        # Manufacture chips and interact with ordering agents
        self.manufacture_chips()
        self.r_and_d()
        self.choose_action()
        self.prev_resources = self.resources.copy()
        self.update_trend_and_horizon()
   # Keep the chip price history within the lookback steps
        if len(self.chip_price_history) > self.lookback_steps:
            self.chip_price_history.pop(0)
        self.calculate_expenses()


class InfineonAgent(CompanyAgent):
    def __init__(self, unique_id, model, country_agent, company_name):
        super().__init__(unique_id, model, country_agent, company_name)
        self.type = 'Infineon'
        self.talent = random.randint(*self.company_data["Infineon"]["talent_range"])
        self.resources = self.company_data["Infineon"]["initial_resources"].copy()
        self.order_book = deque()  # Initialize the order book as an empty deque

    def r_and_d(self):
        # Calculate the increase in capabilities score based on money and talent
        increase = self.resources["money"] * self.talent / 10
        self.capabilities_score += increase

    def receive_order(self, ordering_agent, quantity):
        self.order_book.append((ordering_agent, quantity))  # Append the new order to the order book

    def receive_payment(self, amount):
        # Add the received money to Infineon's resources
        self.resources['money'] += amount

    def manufacture_chips(self):
        if len(self.order_book) == 0:  # If the order book is empty, there's nothing to manufacture
            return None
        
        ordering_agent, quantity = self.order_book[0]  # Get the oldest order from the order book

        # Check how many chips Infineon can manufacture with its current resources
        max_quantity = min(self.resources['wafers']//2, self.resources['services'], quantity) 
        
        # If Infineon can't manufacture any chips, return None
        if max_quantity <= 0:
            return None

        # Subtract the used resources and add the manufactured chips
        self.resources['wafers'] -= max_quantity*2
        self.resources['services'] -= max_quantity
        self.resources['chips'] += max_quantity

        # Update the order in the order book or remove it if it's been completely fulfilled
        if max_quantity < quantity:
            self.order_book[0] = (ordering_agent, quantity - max_quantity)
        else:
            self.order_book.popleft()


        # Send the manufactured chips to the ordering agent
        self.send_chips_to(ordering_agent, max_quantity)
        # Return the details of the order that's just been processed
        return ordering_agent, max_quantity


    def send_chips_to(self, receiving_agent, quantity):
        # Subtract the chips from Infineon and add them to the receiving agent
        self.resources['chips'] -= quantity
        receiving_agent.receive_chips(quantity) 


 
     
    def step(self):
        # Find the ASMLAgent and SUMCOAgent in the model's schedule
        asml_agent = None
        sumco_agent = None
        for agent in self.model.schedule.agents:
            if isinstance(agent, ASMLAgent) and asml_agent is None:
                asml_agent = agent
            elif isinstance(agent, SumcoAgent) and sumco_agent is None:
                sumco_agent = agent

            # If we found both agents, we can break the loop
            if asml_agent is not None and sumco_agent is not None:
                break

        # Buy tools from the ASMLAgent
        self.buy_resources_from(asml_agent, 'services', 10)

        # Buy wafers from the SUMCOAgent
        self.buy_resources_from(sumco_agent, 'wafers', 10)

        # Manufacture chips and interact with ordering agents
        self.manufacture_chips()
        self.r_and_d()
        self.choose_action()
        self.prev_resources = self.resources.copy()
        self.update_trend_and_horizon()
   # Keep the chip price history within the lookback steps
        if len(self.chip_price_history) > self.lookback_steps:
            self.chip_price_history.pop(0)
        self.calculate_expenses()



class STMicroelectronicsAgent(CompanyAgent):
    def __init__(self, unique_id, model, country_agent, company_name):
        super().__init__(unique_id, model, country_agent, company_name)
        self.type = 'STMicroelectronics'
        self.talent = random.randint(*self.company_data["STMicroelectronics"]["talent_range"])
        self.resources = self.company_data["STMicroelectronics"]["initial_resources"].copy()
        self.order_book = deque()  # Initialize the order book as an empty deque

    def r_and_d(self):
        # Calculate the increase in capabilities score based on money and talent
        increase = self.resources["money"] * self.talent / 10
        self.capabilities_score += increase

    def receive_order(self, ordering_agent, quantity):
        self.order_book.append((ordering_agent, quantity))  # Append the new order to the order book


    def receive_payment(self, amount):
        # Add the received money to STMicroelectronics's resources
        self.resources['money'] += amount


    def manufacture_chips(self):
        if len(self.order_book) == 0:  # If the order book is empty, there's nothing to manufacture
            return None
        
        ordering_agent, quantity = self.order_book[0]  # Get the oldest order from the order book

        # Check how many chips STMicroelectronics can manufacture with its current resources
        max_quantity = min(self.resources['wafers']//2, self.resources['services'], quantity) 
        
        # If STMicroelectronics can't manufacture any chips, return None
        if max_quantity <= 0:
            return None

        # Subtract the used resources and add the manufactured chips
        self.resources['wafers'] -= max_quantity*2
        self.resources['services'] -= max_quantity
        self.resources['chips'] += max_quantity

        # Update the order in the order book or remove it if it's been completely fulfilled
        if max_quantity < quantity:
            self.order_book[0] = (ordering_agent, quantity - max_quantity)
        else:
            self.order_book.popleft()


        # Send the manufactured chips to the ordering agent
        self.send_chips_to(ordering_agent, max_quantity)
        # Return the details of the order that's just been processed
        return ordering_agent, max_quantity


    def send_chips_to(self, receiving_agent, quantity):
        # Subtract the chips from STMicroelectronics and add them to the receiving agent
        self.resources['chips'] -= quantity
        receiving_agent.receive_chips(quantity) 


 
     
    def step(self):
        # Find the ASMLAgent and SUMCOAgent in the model's schedule
        asml_agent = None
        sumco_agent = None
        for agent in self.model.schedule.agents:
            if isinstance(agent, ASMLAgent) and asml_agent is None:
                asml_agent = agent
            elif isinstance(agent, SumcoAgent) and sumco_agent is None:
                sumco_agent = agent

            # If we found both agents, we can break the loop
            if asml_agent is not None and sumco_agent is not None:
                break

        # Buy tools from the ASMLAgent
        self.buy_resources_from(asml_agent, 'services', 10)

        # Buy wafers from the SUMCOAgent
        self.buy_resources_from(sumco_agent, 'wafers', 10)

        # Manufacture chips and interact with ordering agents
        self.manufacture_chips()
        self.r_and_d()
        self.choose_action()
        self.prev_resources = self.resources.copy()
        self.update_trend_and_horizon()
   # Keep the chip price history within the lookback steps
        if len(self.chip_price_history) > self.lookback_steps:
            self.chip_price_history.pop(0)
        self.calculate_expenses()


class RenesasAgent(CompanyAgent):
    def __init__(self, unique_id, model, country_agent, company_name):
        super().__init__(unique_id, model, country_agent, company_name)
        self.type = 'Renesas'
        self.talent = random.randint(*self.company_data["Renesas"]["talent_range"])
        self.resources = self.company_data["Renesas"]["initial_resources"].copy()
        self.order_book = deque()

    def receive_payment(self, amount):
        # Add the received money to Renesas's resources
        self.resources['money'] += amount

    def r_and_d(self):
        # Calculate the increase in capabilities score based on money and talent
        increase = self.resources["money"] * self.talent / 10
        self.capabilities_score += increase

   
    def receive_order(self, ordering_agent, quantity):
        self.order_book.append((ordering_agent, quantity))  # Append the new order to the order book



    def manufacture_chips(self):
        if len(self.order_book) == 0:  # If the order book is empty, there's nothing to manufacture
            return None
        
        ordering_agent, quantity = self.order_book[0]  # Get the oldest order from the order book

        max_quantity = min(self.resources['wafers']//2, self.resources['services'], quantity) 
        
        if max_quantity <= 0:
            return None

        # Subtract the used resources and add the manufactured chips
        self.resources['wafers'] -= max_quantity*2
        self.resources['services'] -= max_quantity
        self.resources['chips'] += max_quantity

        # Update the order in the order book or remove it if it's been completely fulfilled
        if max_quantity < quantity:
            self.order_book[0] = (ordering_agent, quantity - max_quantity)
        else:
            self.order_book.popleft()


        # Send the manufactured chips to the ordering agent
        self.send_chips_to(ordering_agent, max_quantity)
        # Return the details of the order that's just been processed
        return ordering_agent, max_quantity

    def send_chips_to(self, receiving_agent, quantity):
        # Subtract the chips from Renesas and add them to the receiving agent
        self.resources['chips'] -= quantity
        receiving_agent.receive_chips(quantity) 

    def step(self):
        # Find the ASMLAgent and SUMCOAgent in the model's schedule
        asml_agent = None
        siltronic_agent = None
        for agent in self.model.schedule.agents:
            if isinstance(agent, ASMLAgent) and asml_agent is None:
                asml_agent = agent
            elif isinstance(agent, SiltronicAgent) and siltronic_agent is None:
                siltronic_agent = agent

            # If we found both agents, we can break the loop
            if asml_agent is not None and siltronic_agent is not None:
                break

        self.buy_resources_from(asml_agent, 'services', 10)
        self.buy_resources_from(siltronic_agent, 'wafers', 10)
        self.manufacture_chips()
        self.r_and_d()
        self.choose_action()
        self.prev_resources = self.resources.copy()
        self.update_trend_and_horizon()
   # Keep the chip price history within the lookback steps
        if len(self.chip_price_history) > self.lookback_steps:
            self.chip_price_history.pop(0)
        self.calculate_expenses()

class SonyAgent(CompanyAgent):
    def __init__(self, unique_id, model, country_agent, company_name):
        super().__init__(unique_id, model, country_agent, company_name)
        self.type = 'Sony'
        self.talent = random.randint(*self.company_data["Sony"]["talent_range"])
        self.resources = self.company_data["Sony"]["initial_resources"].copy()
        self.order_book = deque()

    def receive_payment(self, amount):
        # Add the received money to Sony's resources
        self.resources['money'] += amount

    def r_and_d(self):
        # Calculate the increase in capabilities score based on money and talent
        increase = self.resources["money"] * self.talent / 10
        self.capabilities_score += increase

   
    def receive_order(self, ordering_agent, quantity):
        self.order_book.append((ordering_agent, quantity))  # Append the new order to the order book



    def manufacture_chips(self):
        if len(self.order_book) == 0:  # If the order book is empty, there's nothing to manufacture
            return None
        
        ordering_agent, quantity = self.order_book[0]  # Get the oldest order from the order book

        # Check how many chips Sony can manufacture with its current resources
        max_quantity = min(self.resources['wafers']//2, self.resources['services'], quantity) 
        
        # If Sony can't manufacture any chips, return None
        if max_quantity <= 0:
            return None

        # Subtract the used resources and add the manufactured chips
        self.resources['wafers'] -= max_quantity*2
        self.resources['services'] -= max_quantity
        self.resources['chips'] += max_quantity

        # Update the order in the order book or remove it if it's been completely fulfilled
        if max_quantity < quantity:
            self.order_book[0] = (ordering_agent, quantity - max_quantity)
        else:
            self.order_book.popleft()


        # Send the manufactured chips to the ordering agent
        self.send_chips_to(ordering_agent, max_quantity)
        return ordering_agent, max_quantity

    def send_chips_to(self, receiving_agent, quantity):
        # Subtract the chips from Sony and add them to the receiving agent
        self.resources['chips'] -= quantity
        receiving_agent.receive_chips(quantity) 

    def step(self):
        # Find the ASMLAgent and SUMCOAgent in the model's schedule
        asml_agent = None
        siltronic_agent = None
        for agent in self.model.schedule.agents:
            if isinstance(agent, ASMLAgent) and asml_agent is None:
                asml_agent = agent
            elif isinstance(agent, SiltronicAgent) and siltronic_agent is None:
                siltronic_agent = agent

            # If we found both agents, we can break the loop
            if asml_agent is not None and siltronic_agent is not None:
                break

        self.buy_resources_from(asml_agent, 'services', 10)
        self.buy_resources_from(siltronic_agent, 'wafers', 10)
        self.manufacture_chips()
        self.r_and_d()
        self.choose_action()
        self.prev_resources = self.resources.copy()
        self.update_trend_and_horizon()
   # Keep the chip price history within the lookback steps
        if len(self.chip_price_history) > self.lookback_steps:
            self.chip_price_history.pop(0)
        self.calculate_expenses()

class TexasInstrumentsAgent(CompanyAgent):
    def __init__(self, unique_id, model, country_agent, company_name):
        super().__init__(unique_id, model, country_agent, company_name)
        self.type = 'TexasInstruments'
        self.talent = random.randint(*self.company_data["TexasInstruments"]["talent_range"])
        self.resources = self.company_data["TexasInstruments"]["initial_resources"].copy()
        self.capabilities_score = 0
        self.order_book = deque()

    def receive_payment(self, amount):
        # Add the received money to TexasInstruments's resources
        self.resources['money'] += amount

    def r_and_d(self):
        # Calculate the increase in capabilities score based on money and talent
        increase = self.resources["money"] * self.talent / 10
        self.capabilities_score += increase


   
    def receive_order(self, ordering_agent, quantity):
        self.order_book.append((ordering_agent, quantity))  # Append the new order to the order book
  


    def manufacture_chips(self):
        if len(self.order_book) == 0:  # If the order book is empty, there's nothing to manufacture
            return None
        
        ordering_agent, quantity = self.order_book[0]  # Get the oldest order from the order book

        # Check how many chips intel can manufacture with its current resources
        max_quantity = min(self.resources['wafers']//2, self.resources['services'], quantity) 
        
        # If intel can't manufacture any chips, return None
        if max_quantity <= 0:
            return None

        # Subtract the used resources and add the manufactured chips
        self.resources['wafers'] -= max_quantity*2
        self.resources['services'] -= max_quantity
        self.resources['chips'] += max_quantity

        # Update the order in the order book or remove it if it's been completely fulfilled
        if max_quantity < quantity:
            self.order_book[0] = (ordering_agent, quantity - max_quantity)
        else:
            self.order_book.popleft()


        # Send the manufactured chips to the ordering agent
        self.send_chips_to(ordering_agent, max_quantity)
        # Return the details of the order that's just been processed
        return ordering_agent, max_quantity

    def send_chips_to(self, receiving_agent, quantity):
        # Subtract the chips from TexasInstruments and add them to the receiving agent
        self.resources['chips'] -= quantity
        receiving_agent.receive_chips(quantity) 

    def step(self):
        # Find the ASMLAgent and SUMCOAgent in the model's schedule
        asml_agent = None
        siltronic_agent = None
        for agent in self.model.schedule.agents:
            if isinstance(agent, ASMLAgent) and asml_agent is None:
                asml_agent = agent
            elif isinstance(agent, SiltronicAgent) and siltronic_agent is None:
                siltronic_agent = agent

            # If we found both agents, we can break the loop
            if asml_agent is not None and siltronic_agent is not None:
                break

        self.buy_resources_from(asml_agent, 'services', 10)
        self.buy_resources_from(siltronic_agent, 'wafers', 10)
        self.manufacture_chips()
        self.r_and_d()
        self.choose_action()
        self.prev_resources = self.resources.copy()
        self.update_trend_and_horizon()
   # Keep the chip price history within the lookback steps
        if len(self.chip_price_history) > self.lookback_steps:
            self.chip_price_history.pop(0)
        self.calculate_expenses()
