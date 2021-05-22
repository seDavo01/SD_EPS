from datetime import datetime

class MissionParameters():
    date_format = '%d %b %Y %H:%M:%S.%f'
    dt_mission_start = datetime.strptime('1 Mar 2023 00:00:00.000', date_format)
    dt_mission_end = datetime.strptime('1 Apr 2023 00:00:00.000', date_format)

class SystemParameters():
    solar_efficiency = 0.8
    converters_efficiency = 0.9

class SolarCellParameters():
    p_BOL = 0.293
    p_EOL = 0.270
    phi = 1367
    cell_area = 0.003018
    voltage = 2.4                       # V
    current = 0.5                       # A
    power = voltage * current           # W

class BatteryCellParameters():
    nominal_capacity = 2.6              # Ah
    min_voltage = 2.75                  # V
    max_voltage = 4.0                   # V
    voltage = 3.6                       # V
    min_charge_rate = 0.1
    charge_step = 0.1
    max_charge_rate = 0.5
    max_discharge_rate = 1
    efficiency = 0.80
    max_DOD = 0.15


class PayloadParameters():
    voltage = 12                        # V
    idle_power_consumption = 1.2        # W
    elaboration_power_consumption = 6   # W
    acquisition_power_consumption = 12  # W
    acquisition_datarate = 0.4          # GB/s
    elaboration_basetime = 4*60/10      # s
    elaboration_datarate = [-acquisition_datarate/elaboration_basetime , 0.0044/elaboration_basetime ]       # GB/s
    transfer_datarate = 10*10**-3/8     # GB/s

class TTCParameters():
    voltage = 12                        # V
    idle_power_consumption = {          
        'S-band': 0.2,                  # W
        'UHF': 0.1                      # W
    }
    rx_power_consumption = {          
        'S-band': 0.2,                  # W
        'UHF': 0.18 + 0.16              # W
    }
    tx_power_consumption = {          
        'S-band': 9,                    # W
        'UHF': 2.64 + 0.16              # W
    }
    average_power_consumption = {          
        'S-band': (rx_power_consumption['S-band']+tx_power_consumption['S-band'])/2,
        'UHF': (rx_power_consumption['UHF']+tx_power_consumption['UHF']-0.16)/2
    }
    datarate = 12.5*10**-3/8            # GB/s

class HeaterParameters():
    voltage = 12                        # V
    power_consumption = 6               # W
    eclipse_duration = 0.6
    sun_duration = 0

class ComponentParameters():
    name = 'placeholder'
    voltage = 5
    power = 6
    sunlight = False