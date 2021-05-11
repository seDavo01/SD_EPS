from .components import *

def day(schedule: list,
        payload: Payload,
        solar_panels: list,
        battery_packs: list,
        ttcs: list,
        components: list):
    time = 0
    for task in schedule:
        if task == 'acquisition':
            payload.next_status = 'acquisition'
            while payload.status != 'elaboration':
                time += 1
                step(payload, solar_panels, battery_packs, ttcs, components, timestep=1)
        elif task == 'elaboration':
            while payload.raw_data > 0:
                time += 1
                step(payload, solar_panels, battery_packs, ttcs, components, timestep=1)
        elif task == 'download':
            ttc_idx = 0
            for i, ttc in enumerate(ttcs):
                if ttc.mode == 'S-band':
                    ttc.next_status = 'tx'
                    ttc_idx = i
            while ttc[ttc_idx].data > 0:
                time += 1
                step(payload, solar_panels, battery_packs, ttcs, components, timestep=1)
    while time < 3600 * 24:
        time += 1
        step(payload, solar_panels, battery_packs, ttcs, components, timestep=1)




def step(payload: Payload,
         solar_panels: list,
         battery_packs: list,
         ttcs: list,
         components: list,
         timestep=1):

        input_power = 0
        output_power = 0
        payload.step(timestep)
        output_power += payload.input
        for solar_panel in solar_panels:
            solar_panel.step(timestep)
            input_power += solar_panel.output
        for ttc in ttcs:
            ttc.step(timestep)
            output_power += ttc.input
        for component in components:
            component.step(timestep)
            output_power += component.input

        power = input_power - output_power
        n_packs = len(battery_packs)
        for battery_pack in battery_packs:
            battery_pack.step(power/n_packs, timestep)