from model import *
import matplotlib.pyplot as plt
import pandas as pd

def main():
    # Simulate the model
    model = GameModel(100)  # Create a model with 100 agents
    for i in range(100):  # Simulate for 100 steps
        model.step()

    # Collect and save model data
    model_data = model.datacollector.get_model_vars_dataframe()
    model_data.to_csv('model_data.csv')

    # Collect and save agent data
    agent_data = model.datacollector.get_agent_vars_dataframe()
    agent_data.to_csv('agent_data.csv')

    # Plot model data
    model_data.plot()
    plt.show()

if __name__ == "__main__":
    main()