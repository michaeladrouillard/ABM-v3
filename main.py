from model import *
import matplotlib.pyplot as plt
import pandas as pd

def main():
    # Simulate the model
    model = GameModel(5)  # Create a model with 100 agents
    for i in range(100):  # Simulate for 100 steps
        model.step()

    # Collect and save model data
    model_data = model.datacollector.get_model_vars_dataframe()
    # Expand the GDP column into separate columns for each country
    gdp_data = model_data['GDP'].apply(pd.Series)

    # Prefix each GDP column with 'GDP_'
    gdp_data = gdp_data.add_prefix('GDP_')

    # Concatenate the expanded GDP data with the original model data
    model_data = pd.concat([model_data.drop('GDP', axis=1), gdp_data], axis=1)

    # Save the processed model data
    model_data.to_csv('model_data.csv')
    model_data.to_csv('model_data.csv')

    # Collect and save agent data
    agent_data = model.datacollector.get_agent_vars_dataframe()

    attribute_cols = ['unique_id', 'talent', 'resources', 'prev_resources', 'country_agent',
                      'company_name', 'capabilities_score', 'public_opinion', 'influence', 
                      'project_launch_threshold', 'government_lobby_money_threshold', 
                      'cooperation_thresholds', 'project_launch_cost', 
                      'government_lobby_talent_threshold', 'competition_percentage']
    
    for col in attribute_cols:
        agent_data[col] = agent_data['Agent Attributes'].apply(lambda x: x.get(col))
    agent_data['money'] = agent_data['resources'].apply(lambda x: x.get('money'))
    agent_data['chips'] = agent_data['resources'].apply(lambda x: x.get('chips'))
    agent_data = agent_data.drop('Agent Attributes', axis=1)
    agent_data.to_csv('agent_data.csv')

    # Plot model data
    model_data.plot()
    plt.show()

if __name__ == "__main__":
    main()