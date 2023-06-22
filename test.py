from Agents.companycountry import CountryAgent, CompanyAgent, NvidiaAgent, SMICAgent, InfineonAgent, RenesasAgent, TSMCAgent, IntelAgent, HuaHongAgent, STMicroelectronicsAgent, SonyAgent, MediaTekAgent, ASMLAgent 
from Agents.communication import CommunicationChannel
from Agents.resource import Resource
from Agents.mine import MineAgent
from Agents.plant import ProcessingPlantAgent
from model import *

import unittest

class TestChipTransaction(unittest.TestCase):
    def setUp(self):
        global agent_dict
        config_file = 'config.yaml'
        with open(config_file, 'r') as f:
            agent_dict = yaml.safe_load(f)

        model = GameModel(agent_dict)
        self.nvidia = NvidiaAgent(unique_id='nvidia1', model=model, country_agent= 'US', company_name='Nvidia')
        self.tsmc = TSMCAgent(unique_id='tsmc1', model=model, country_agent= 'Taiwan', company_name='TSMC')
        self.initial_money_nvidia = self.nvidia.resources["money"]
        self.initial_chips_nvidia = self.nvidia.resources["chips"]

    def test_transaction(self):
        self.nvidia.order_chips_from_TSMC()

        # Check that money has decreased for Nvidia
        self.assertLess(self.nvidia.resources["money"], self.initial_money_nvidia)

        # TSMC fulfills the order
        self.tsmc.manufacture_chips()
        self.tsmc.send_chips_to(self.nvidia, quantity=1)

        # Check that chips have increased for Nvidia
        self.assertGreater(self.nvidia.resources["chips"], self.initial_chips_nvidia)

if __name__ == "__main__":
    unittest.main()
