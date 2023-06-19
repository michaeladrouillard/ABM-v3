from model import *
import matplotlib.pyplot as plt
import pandas as pd
from tqdm import tqdm
import cProfile


def run_model(agent_dict):
    model = GameModel(agent_dict)
    for _ in tqdm(range(100), desc="Running model"):
        model.step()
   

    # Collect and save model data
    model_data = model.datacollector.get_model_vars_dataframe()


    # Save the processed model data
    model_data.to_csv('model_data.csv')
    model_data.to_csv('model_data.csv')

    # Collect and save agent data
    agent_data = model.datacollector.get_agent_vars_dataframe()
    print(agent_data.head())

    # attribute_cols = ['unique_id', 'talent', 'resources', 'prev_resources', 'country_agent',
    #                   'company_name', 'capabilities_score', 'public_opinion', 'influence', 
    #                   'project_launch_threshold', 'government_lobby_money_threshold', 
    #                   'cooperation_thresholds', 'project_launch_cost', 
    #                   'government_lobby_talent_threshold', 'competition_percentage']
    
    # for col in attribute_cols:
    #     agent_data[col] = agent_data['Agent Attributes'].apply(lambda x: x.get(col))
    #     agent_data['money'] = agent_data['resources'].apply(lambda x: x.get('money'))
    #     agent_data['chips'] = agent_data['resources'].apply(lambda x: x.get('chips'))
    #     agent_data = agent_data.drop('Agent Attributes', axis=1)
    agent_data.to_csv('agent_data.csv')

 # Plot model data
    model_data.plot()
    plt.show()
def main():

    global agent_dict
    config_file = 'config.yaml'
    with open(config_file, 'r') as f:
        agent_dict = yaml.safe_load(f)

    cProfile.run('run_model(agent_dict)')

if __name__ == "__main__":
    main()