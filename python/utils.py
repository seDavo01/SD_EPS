import pandas as pd

from .parameters import ComponentParameters

def csvtoparameters(file_path):
    df = pd.read_csv(file_path)

    parameters_list = list()

    for name, voltage, power, sunlight in zip(df['name'], df['voltage'], df['power'], df['sunlight']):
        param = ComponentParameters()
        param.name = name
        param.voltage = float(voltage)
        param.power = float(power)
        param.sunlight = sunlight

        parameters_list.append(param)

    return parameters_list
