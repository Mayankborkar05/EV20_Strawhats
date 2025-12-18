import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from io import StringIO
import warnings
warnings.filterwarnings('ignore')

data = """States/UTs,Over-Speeding - Number of Accidents - Number,Over-Speeding - Number of Accidents - Rank,Over-Speeding - Persons Killed - Number,Over-Speeding - Persons Killed - Rank,Over-Speeding - Persons Injured - Greviously Injured,Over-Speeding - Persons Injured - Minor Injury,Over-Speeding - Persons Injured - Total Injured,Drunken Driving - Number of Accidents,Drunken Driving - Persons Killed,Drunken Driving - Persons Injured - Greviously Injured,Drunken Driving - Persons Injured - Minor Injury,Drunken Driving - Persons Injured - Total Injured,Driving on Wrong side - Number of Accidents,Driving on Wrong side - Persons Killed,Driving on Wrong side - Persons Injured - Greviously Injured,Driving on Wrong side - Persons Injured - Minor Injury,Driving on Wrong side - Persons Injured - Total Injured,Jumping Red Light - Number of Accidents,Jumping Red Light - Persons Killed,Jumping Red Light - Persons Injured - Greviously Injured,Jumping Red Light - Persons Injured - Minor Injury,Jumping Red Light - Persons Injured - Total Injured,Use of Mobile Phone - Number of Accidents,Use of Mobile Phone - Persons Killed,Use of Mobile Phone - Persons Injured - Greviously Injured,Use of Mobile Phone - Persons Injured - Minor Injury,Use of Mobile Phone - Persons Injured - Total Injured,Others - Number of Accidents,Others - Persons Killed,Others - Persons Injured - Greviously Injured,Others - Persons Injured - Minor Injury,Others - Persons Injured - Total Injured
Aurangabad,534,28,179,19,291,117,408,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,26,20,26,0,26
Mumbai,514,30,120,31,422,104,526,61,5,46,34,80,45,3,37,13,50,15,1,17,3,20,3,0,2,2,4,2234,318,1623,622,2245
Nagpur,469,34,132,29,289,203,492,39,6,28,17,45,90,14,51,45,96,0,0,0,0,0,54,2,36,18,54,355,96,208,147,355
Nashik,529,29,172,21,364,148,512,6,3,3,2,5,16,2,17,5,22,2,0,1,0,1,0,0,0,0,0,0,0,0,0,0
Pune,301,37,70,42,172,47,219,21,2,6,7,13,16,4,10,2,12,14,2,11,1,12,0,0,0,0,0,439,128,264,106,370
"""

df = pd.read_csv(StringIO(data))
df.fillna(0, inplace=True)
df[df.columns.drop('States/UTs')] = df[df.columns.drop('States/UTs')].astype(float)

causes = {
    'Over-Speeding': 'Over-Speeding - Number of Accidents - Number',
    'Drunken_Driving': 'Drunken Driving - Number of Accidents',
    'Wrong_Side': 'Driving on Wrong side - Number of Accidents',
    'Red_Light': 'Jumping Red Light - Number of Accidents',
    'Mobile_Phone': 'Use of Mobile Phone - Number of Accidents',
    'Others': 'Others - Number of Accidents'
}

for cause, col in causes.items():
    df[f'{cause}_accidents'] = df[col]

df['total_caused_accidents'] = df[list(causes.values())].sum(axis=1)

for cause in causes:
    df[f'{cause}_contribution_pct'] = (
        df[f'{cause}_accidents'] / df['total_caused_accidents'].replace(0, np.nan)
    ).fillna(0) * 100

for cause, col in causes.items():
    kill_col = col.replace('Number of Accidents', 'Persons Killed')
    inj_col = col.replace('Number of Accidents', 'Persons Injured - Total Injured')
    if kill_col in df.columns:
        df[f'{cause}_fatality_rate'] = (
            df[kill_col] / df[f'{cause}_accidents'].replace(0, np.nan)
        ).fillna(0)
    if inj_col in df.columns:
        df[f'{cause}_injury_rate'] = (
            df[inj_col] / df[f'{cause}_accidents'].replace(0, np.nan)
        ).fillna(0)

risk_multipliers = {
    'Over-Speeding': 1.8,
    'Drunken_Driving': 2.5,
    'Wrong_Side': 2.0,
    'Red_Light': 1.4,
    'Mobile_Phone': 1.3,
    'Others': 1.0
}

df['cause_weighted_risk'] = 0
for cause in causes:
    df['cause_weighted_risk'] += df[f'{cause}_accidents'] * risk_multipliers[cause]

df['reckless_index'] = (
    df['Drunken_Driving_accidents'] * 3 +
    df['Wrong_Side_accidents'] * 2 +
    df['Red_Light_accidents'] * 1.5 +
    df['Mobile_Phone_accidents'] * 1.2
)

df['hotspot_score'] = (
    df['total_caused_accidents'] * 0.4 +
    df['cause_weighted_risk'] * 0.3 +
    df['reckless_index'] * 0.3
)

df['risk_category'] = pd.cut(
    df['hotspot_score'],
    bins=[0, 500, 1500, 4000, np.inf],
    labels=['Low', 'Medium', 'High', 'Critical']
)

fig = px.imshow(
    df.set_index('States/UTs')[[f'{c}_contribution_pct' for c in causes]],
    color_continuous_scale='Reds',
    aspect='auto',
    title='CAUSE-WISE ACCIDENT CONTRIBUTION (%)'
)
fig.show()

fig = make_subplots(
    rows=2, cols=2,
    specs=[[{"type": "bar"}, {"type": "scatterpolar"}],
           [{"type": "bar"}, {"type": "pie"}]]
)

fig.add_trace(
    go.Bar(x=df['States/UTs'], y=df['hotspot_score'],
           marker_color=df['hotspot_score'], text=df['hotspot_score'].round(0)),
    row=1, col=1
)

city = df[df['States/UTs'] == 'Mumbai']
fig.add_trace(
    go.Scatterpolar(
        r=[city[f'{c}_accidents'].values[0] for c in causes],
        theta=list(causes.keys()),
        fill='toself',
        name='Mumbai'
    ),
    row=1, col=2
)

fig.add_trace(
    go.Bar(x=df['States/UTs'], y=df['Over-Speeding_fatality_rate'], name='Over-Speeding'),
    row=2, col=1
)

fig.add_trace(
    go.Bar(x=df['States/UTs'], y=df['Drunken_Driving_fatality_rate'], name='Drunken Driving'),
    row=2, col=1
)

risk_pie = df['risk_category'].value_counts()
fig.add_trace(
    go.Pie(labels=risk_pie.index, values=risk_pie.values),
    row=2, col=2
)

fig.update_layout(height=800, title='ACCIDENT CAUSE HOTSPOT ANALYSIS')
fig.show()

ranking = df[['States/UTs', 'hotspot_score', 'risk_category', 'total_caused_accidents']] \
    .sort_values('hotspot_score', ascending=False)

print(ranking.round(2))

feature_cols = ['States/UTs'] + [c for c in df.columns if any(x in c for x in ['contribution_pct','fatality_rate','risk','index','hotspot_score'])]
df[feature_cols].to_csv("accident_cause_hotspots_features.csv", index=False)

print("accident_cause_hotspots_features.csv saved")
