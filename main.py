from model import *
import matplotlib.pyplot as plt
import pandas as pd
from tqdm import tqdm
import cProfile



def run_model(agent_dict):
    model = GameModel(agent_dict)
    for _ in tqdm(range(10), desc="Running model"):
        model.step()
   

    # Collect and save model data
    model_data = model.datacollector.get_model_vars_dataframe()


    # Save the processed model data
    model_data.to_csv('model_data.csv')
    model_data.to_csv('model_data.csv')

    # Collect and save agent data
    agent_data = model.datacollector.get_agent_vars_dataframe()

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
    #model_data.plot()
    #plt.show()
    #model.visualize_network()
def main():

    global agent_dict
    config_file = 'config.yaml'
    with open(config_file, 'r') as f:
        agent_dict = yaml.safe_load(f)

    cProfile.run('run_model(agent_dict)', 'output.pstats')

if __name__ == "__main__":
    main()



def plot_sensitivity_analysis(modelclass, agent_dict, lookback_steps_values, run_steps):
    # model_class: your model class
    # agent_dict: agent configuration dictionary
    # lookback_steps_values: a list of lookback_steps values to test
    # run_steps: number of steps to run each model
    
    selected_companies = ["TSMC"]
    
    for value in lookback_steps_values:
        # Update the 'lookback_steps' value in the agent_dict
        agent_dict["lookback_steps"] = value

        model_instance = modelclass(agent_dict)  # Initialize your model with the new agent_dict

        for _ in range(run_steps):  # Run the model
            model_instance.step()

            # After each model step, update the 'money_history' of each company agent
            for company in model_instance.schedule.agents:
                if isinstance(company, CompanyAgent) and company.company_name in selected_companies:
                    company.money_history.append(company.resources["money"])

        # Plot the results
        for company in model_instance.schedule.agents:
            if isinstance(company, CompanyAgent) and company.company_name in selected_companies:
                plt.plot(company.money_history, label=f'{company.company_name}, lookback={value}')
    
    plt.xlabel('Time Steps')
    plt.ylabel('Money')
    plt.legend()
    plt.show()

lookback_steps_values = [5, 10, 15, 20]  # Or whatever values you're interested in
run_steps = 100  # Or however many steps you want to run the model for
plot_sensitivity_analysis(GameModel, agent_dict, lookback_steps_values, run_steps)
