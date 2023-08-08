from model import *
import matplotlib.pyplot as plt
import pandas as pd
from tqdm import tqdm
import cProfile



def run_model(agent_dict):
    model = GameModel(agent_dict)
    for _ in tqdm(range(1000), desc="Running model"):
        model.step()

    model.print_final_counts()
    # Collect and save model data
    model_data = model.datacollector.get_model_vars_dataframe()


    # Save the processed model data
    model_data.to_csv('model_data.csv')
    model_data.to_csv('model_data.csv')

    # Collect and save agent data
    agent_data = model.datacollector.get_agent_vars_dataframe()
    agent_data.to_csv('agent_data.csv')

    agent_data_reset = agent_data.reset_index()


    selected_company_data = agent_data_reset[agent_data_reset['CompanyName'] == 'Sumco']

    # # Plot the money over time
    plt.figure(figsize=(10,6))
    plt.plot(selected_company_data['Step'], selected_company_data['Money'])
    plt.xlabel('Time Step')
    plt.ylabel('Money')
    plt.title('Sumco Money')
    plt.grid(True)
    plt.show()

def main():

    global agent_dict
    config_file = 'config.yaml'
    with open(config_file, 'r') as f:
        agent_dict = yaml.safe_load(f)

    cProfile.run('run_model(agent_dict)', 'output.pstats')

if __name__ == "__main__":
    main()



# def plot_sensitivity_analysis(modelclass, agent_dict, lookback_steps_values, run_steps):

#      selected_companies = ["Infineon", "TSMC"]

#      for value in lookback_steps_values:
#          # Update the 'lookback_steps' value in the agent_dict
#         agent_dict["lookback_steps"] = value

#         model_instance = modelclass(agent_dict)  # Initialize your model with the new agent_dict

#         for _ in range(run_steps):  # Run the model
#              model_instance.step()

#             # After each model step, update the 'money_history' of each company agent
#         for company in model_instance.schedule.agents:
#             if isinstance(company, CompanyAgent) and company.company_name in selected_companies:
#                 company.money_history.append(company.resources["money"])

#          # Plot the results
#         for company in model_instance.schedule.agents:
#             if isinstance(company, CompanyAgent) and company.company_name in selected_companies:
#                 plt.plot(company.money_history, label=f'{company.company_name}, lookback={value}')

#         plt.xlabel('Time Steps')
#         plt.ylabel('Money')
#         plt.legend()
#         plt.show()

# lookback_steps_values = [5, 10, 15, 20]  # Or whatever values you're interested in
# run_steps = 100  # Or however many steps you want to run the model for
# plot_sensitivity_analysis(GameModel, agent_dict, lookback_steps_values, run_steps)



