import random
from mesa import Agent
from mesa.time import RandomActivation
import yaml
from Agents.companycountry import CompanyAgent

    

class Nvidia(CompanyAgent):
    def __init__(self, unique_id, model, country_agent, company_name = "Nvidia"):
        super().__init__(unique_id, model, country_agent, company_name)

                # Specific characteristics of Nvidia
        self.talent = random.randint(80, 100)  # Assume Nvidia has high talent
        self.resources = {"money": 100000, "GPUs": 50000, "R&D_budget": 20000}  # Nvidia starts with more resources

    def order_chip_production(self, chip_type, number_of_chips):
        # Order chip production from TSMC
        if hasattr(self, "partner_company") and isinstance(self.partner_company, tsmc):
            cost = self.partner_company.produce_chips(chip_type, number_of_chips)
            if self.resources["money"] >= cost:
                self.resources["money"] -= cost
                self.resources[chip_type] += number_of_chips

    def develop_new_technology(self):
        if self.resources["R&D_budget"] > 0:  # Check if there's budget for R&D
            # Use some of the R&D budget
            self.resources["R&D_budget"] -= 1000
            
            # Assume R&D increases the company's capabilities
            self.capabilities_score += 100

    # def form_partnership(self, other_company):
    #     # Forming a partnership with TSMC
    #     if isinstance(other_company, tsmc):
    #         self.resources["money"] -= 5000  # Assume forming a partnership costs some money
    #         self.partner_company = other_company  # Store the partner company

