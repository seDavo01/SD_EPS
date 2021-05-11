import matplotlib.pyplot as plt

from .components import *

def day(schedule: list,
        payload: Payload,
        solar_panels: list,
        battery_packs: list,
        ttcs: list,
        components: list):
    time = 0
    input_power = list()
    output_power = list()
    batteries = list()
    for task in schedule:
        if task == 'acquisition':
            payload.next_status = 'acquisition'
            while payload.status != 'elaboration':
                time += 1
                ip, op, bat = step(payload, solar_panels, battery_packs, ttcs, components, timestep=1)
                input_power.append(ip)
                output_power.append(op)
                batteries.append(bat)
        elif task == 'elaboration':
            while payload.raw_data > 0:
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
            while ttc[ttc_idx].data > 0:
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

    _ = axarr[0,2].set_title('Battery SOC')
    _ = axarr[0,2].plot(timeline, [x['SOC'] for x in batteries])

    fig.show()




def step(payload: Payload,
         solar_panels: list,
         battery_packs: list,
         ttcs: list,
         components: list,
         timestep=1):

        input_power = 0
        output_power = {
            12: 0,
            5: 0,
            3.3: 0,
        }
        for solar_panel in solar_panels:
            solar_panel.step(timestep)
            input_power += solar_panel.output
        comps = list()
        comps += components + ttcs + [payload]
        for component in comps:
            component.step(timestep)
            output_power[component.voltage] += component.input

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