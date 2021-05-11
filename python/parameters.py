from datetime import datetime

class MissionParameters():
    date_format = '%d %b %Y %H:%M:%S.%f'
    dt_mission_start = datetime.strptime('1 Mar 2023 00:00:00.000', date_format)
    dt_mission_end = datetime.strptime('1 Apr 2023 00:00:00.000', date_format)

class SolarCellParameters():
    p_EOL = 0.293
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
    charge_step = 0.05
    max_charge_rate = 0.5
    max_discharge_rate = 1
    efficiency = 0.85
    max_DOD = 0.15


class PayloadParameters():
    voltage = 12                        # V
    idle_power_consumption = 2          # W
    elaboration_power_consumption = 6   # W
    acquisition_power_consumption = 12  # W
    acquisition_datarate = 0.4          # GB/s
    elaboration_basetime = 4*60/10      # s
    elaboration_datarate = [-acquisition_datarate/elaboration_basetime , 0.0044/elaboration_basetime ]       # GB/s

class TTCParameters():
    voltage = 12                        # V
    idle_power_consumption = 1          # W
    download_power_consumption = 6      # W
    datarate = 12.5*10**-3/8            # GB/s

class ComponentParameters():
    name = 'placeholder'
    voltage = 5
    power = 6
    sunlight = False

# class Parameters():
#     name = ''
#     power_consumption = 0               # W
#     voltage = 0                         # V
#     current = 0                         # A