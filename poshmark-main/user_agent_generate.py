import json
import os
from random import random, uniform
from typing import Literal

user_agents = {
    "Chrome_Windows": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36"
    ],
    "Chrome_Mac": [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    ],
    "Chrome_Linux": [
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    ],
    "Firefox_Windows": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
    ],
    "Firefox_Mac": [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0"
    ],
    "Firefox_Linux": [
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0"
    ],
    "Safari_Mac": [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15"
    ],
    "Edge_Windows": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59"
    ],
    "Opera_Windows": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 OPR/77.0.4054.90"
    ],
    "Opera_Mac": [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 OPR/77.0.4054.90"
    ],
    "Opera_Linux": [
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 OPR/77.0.4054.90"
    ]
}

def get_user_agent(browser_name: Literal['Chrome', 'Firefox', 'Safari', 'Edge', 'Opera'],
                   os_name: Literal['Windows', 'Mac', 'Linux']):
    
    key = f"{browser_name}_{os_name}"

    if key in user_agents:
        return random.choice(user_agents[key])
    
    # Default user agent if none found
    return 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 OPR/77.0.4054.90'

# Example usage
print(get_user_agent('Chrome', 'Windows'))
print(get_user_agent('Firefox', 'Linux'))


def generange_agent(
          browser_name: Literal['Chrome', 'Firefox', 'Safari', 'Edge', 'Opera'],
          os_name: Literal['Windows', 'Mac', 'Linux'],
):
    # Диапазон широты и долготы для США и Канады
    lat_min, lat_max = 24.396308, 83.162102  # От Южного Техаса до Северной Канады
    lon_min, lon_max = -141.000000, -52.619400  # От Западного побережья до Восточного побережья
    latitude = uniform(lat_min, lat_max)
    longitude = uniform(lon_min, lon_max)

    agent = {
        'user_agent': get_user_agent(browser_name, os_name),
        # 'geolocation': {'latitude':latitude, 'longitude': longitude},  # New York, NY
        'locale': 'en-US',
        # 'permissions': ['geolocation'],
    }
    return agent
agents_dict = {}
systems = ['Windows', 'Mac', 'Linux']
ag = ['Chrome', 'Firefox', 'Safari', 'Edge', 'Opera']

for system in systems:
    agents_dict[system] = {}
    for agent in ag:
        if agent == 'Edge' and system != 'Windows':
            continue
        if agent == 'Safari' and system != 'Mac':
            continue
        agents = []
        for _ in range(10):
            agents.append(generange_agent(agent,system))
        agents_dict[system][agent] = agents

with open(os.path.join(os.getcwd(), 'user_agents.json'), 'w') as f:
    json.dump(agents_dict, f)
# print(generange_agent('Firefox','Linux'))
# print(generange_agent('Opera','Linux'))
# print(generange_agent('Chrome','Linux'))
