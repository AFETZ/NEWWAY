import pandas as pd
import matplotlib.pyplot as plt
import ast
import numpy as np

# Load data
data = pd.read_csv(
    'scenarios/scenario_serpantine/output_data/output250-300.csv',
    sep=' '
)
car_id = 12
all_data = []
frames = []
for i in range(len(data['Frame'])):
    s = data['PathLoss'][i]
    # row = ast.literal_eval(data['PathLoss'][i]).get(f'veh{car_id}')

    row_dict = eval(s, {"np": np})
    row = row_dict.get(f'veh{car_id}')
    if row:
        frames.append(data['Frame'][i])
        all_data.append(row)

df = pd.DataFrame(all_data)
df.fillna(-200, inplace=True)
df = df.loc[:, df.nunique() > 1]
# Create figure
fig, ax = plt.subplots(figsize=(10, 6))


for col in df.columns:
    ax.plot(
        frames,
        df[col],
        linewidth=3,        
        alpha=0.9,
        label=col
    )
# Axis labels
ax.set_xlabel("Frame",fontsize=12)
ax.set_ylabel("PathLoss(dBm)",fontsize=12)
ax.set_ylim(-200, 0)
ax.set_title(f"2D Mountain Pass Scenario signal loss for Veh. {car_id}", fontsize=15)
ax.spines['bottom'].set_linewidth(2)
ax.spines['left'].set_linewidth(2)
# Light grid (optional but acceptable in papers)
ax.grid(True)
ax.legend(title="Connection with:",
          loc='upper right')
    

# Legend (only if necessary)


plt.show()