import matplotlib.pyplot as plt

from .components import *
from .parameters import SystemParameters

def day(schedule: list,
        payload: Payload,
        solar_panels: list,
        battery_packs: list,
        ttcs: list,
        components: list,
        absolute_time: int = 0):
    time = 0
    input_power = list()
    output_power = list()
    batteries = list()
    for task in schedule:
        if task == 'acquisition':
            payload.next_status = 'acquisition'
            while payload.status != 'elaboration' and time < 3600 * 24:
                time += 1
                ip, op, bat = step(payload, solar_panels, battery_packs, ttcs, components, timestep=1)
                input_power.append(ip)
                output_power.append(op)
                batteries.append(bat)
        elif task == 'elaboration':
            while payload.raw_data > 0 and time < 3600 * 24:
                time += 1
                ip, op, bat = step(payload, solar_panels, battery_packs, ttcs, components, timestep=1)
                input_power.append(ip)
                output_power.append(op)
                batteries.append(bat)
        elif task == 'transfer':
            payload.next_status = 'transfer'
            while payload.processed_data > 0 and time < 3600 * 24:
                time += 1
                ip, op, bat = step(payload, solar_panels, battery_packs, ttcs, components, timestep=1)
                input_power.append(ip)
                output_power.append(op)
                batteries.append(bat)
        elif task == 'download':
            ttc_idx = 0
            for i, ttc in enumerate(ttcs):
                if ttc.mode == 'S-band':
                    ttc.next_status = 'tx'
                    ttc_idx = i
            while ttcs[ttc_idx].data > 0 and time < 3600 * 24:
                time += 1
                ip, op, bat = step(payload, solar_panels, battery_packs, ttcs, components, timestep=1)
                input_power.append(ip)
                output_power.append(op)
                batteries.append(bat)

    while time < 3600 * 24:
        time += 1
        ip, op, bat = step(payload, solar_panels, battery_packs, ttcs, components, timestep=1)
        input_power.append(ip)
        output_power.append(op)
        batteries.append(bat)

    timeline = [t for t in range(time)]
    fig, axarr = plt.subplots(2, 3, figsize=(50, 20))

    _ = axarr[0,0].set_title('Input Power')
    _ = axarr[0,0].plot(timeline, input_power)
    
    _ = axarr[0,1].set_title('Output Power')
    _ = axarr[0,1].plot(timeline, [sum(x.values()) for x in output_power])

    _ = axarr[0,2].set_title('Battery DOD')
    _ = axarr[0,2].plot(timeline, [1 - x['SOC'] for x in batteries])

    fig.show()

    return time + absolute_time



def step(payload: Payload,
         solar_panels: list,
         battery_packs: list,
         ttcs: list,
         components: list,
         timestep=1):

        params = SystemParameters()

        input_power = 0
        output_power = {
            'Vbat': 0,
            12: 0,
            5: 0,
            3.3: 0,
        }
        for solar_panel in solar_panels:
            solar_panel.step(timestep)
            input_power += solar_panel.output * params.solar_efficiency
        comps = list()
        comps += components + ttcs + [payload]
        for component in comps:
            component.step(timestep)
            output_power[component.voltage] += component.input * params.converters_efficiency

        if payload.status == 'transfer':
            for ttc in ttcs:
                if ttc.mode == 'S-band':
                    ttc.data = payload.output_data      

        power = input_power - sum(output_power.values())
        n_packs = len(battery_packs)
        batteries = {
            'input_power': 0,
            'output_power': 0,
            'SOC': 0
        }
        for battery_pack in battery_packs:
            battery_pack.step(power/n_packs, timestep)
            batteries['input_power'] += battery_pack.input
            batteries['output_power'] += battery_pack.output
            batteries['SOC'] += battery_pack.soc

        return input_power, output_power, batteries