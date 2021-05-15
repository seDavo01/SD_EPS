import os 
import matplotlib.pyplot as plt

from .components import *
from .parameters import SystemParameters


class Experiment():

    def __init__(self,
                 payload: Payload,
                 solar_panels: list,
                 battery_packs: list,
                 ttcs: list,
                 components: list,
                 heaters: list,
                 output_folder = None):

        self.payload = payload
        self.solar_panels = solar_panels
        self.battery_packs = battery_packs
        self.ttcs = ttcs
        self.components = components
        self.heaters = heaters

        self.output_folder = output_folder

    def day(self,
            key: str,
            schedule: list,
            absolute_time: int = 0):
        time = 0
        input_power = list()
        output_power = list()
        batteries = list()
        diss_power = list()
        for task in schedule:
            if task == 'acquisition':
                self.payload.next_status = 'acquisition'
                while self.payload.status != 'elaboration' and time < 3600 * 24:
                    time += 1
                    ip, op, bat, dp = self.step()
                    input_power.append(ip)
                    output_power.append(op)
                    batteries.append(bat)
                    diss_power.append(dp)
            elif task == 'elaboration':
                while self.payload.raw_data > 0 and time < 3600 * 24:
                    time += 1
                    ip, op, bat, dp = self.step()
                    input_power.append(ip)
                    output_power.append(op)
                    batteries.append(bat)
                    diss_power.append(dp)
            elif task == 'transfer':
                self.payload.next_status = 'transfer'
                while self.payload.processed_data > 0 and time < 3600 * 24:
                    time += 1
                    ip, op, bat, dp = self.step()
                    input_power.append(ip)
                    output_power.append(op)
                    batteries.append(bat)
                    diss_power.append(dp)
            elif task == 'download':
                ttc_idx = 0
                for i, ttc in enumerate(self.ttcs):
                    if ttc.mode == 'S-band':
                        ttc.next_status = 'tx'
                        ttc_idx = i
                while self.ttcs[ttc_idx].data > 0 and time < 3600 * 24:
                    time += 1
                    ip, op, bat, dp = self.step()
                    input_power.append(ip)
                    output_power.append(op)
                    batteries.append(bat)
                    diss_power.append(dp)

        while time < 3600 * 24:
            time += 1
            ip, op, bat, dp = self.step()
            input_power.append(ip)
            output_power.append(op)
            batteries.append(bat)
            diss_power.append(dp)

        timeline = [t for t in range(time)]
        # fig, axarr = plt.subplots(2, 3, figsize=(50, 20))

        # _ = axarr[0,0].set_title('Input Power')
        # _ = axarr[0,0].set_xlabel('Time (s)')
        # _ = axarr[0,0].set_ylabel('Power (W)')
        # _ = axarr[0,0].plot(timeline, input_power)
        
        # _ = axarr[0,1].set_title('Output Power')
        # _ = axarr[0,1].plot(timeline, [sum(x.values()) for x in output_power])

        # _ = axarr[0,2].set_title('Battery DOD')
        # _ = axarr[0,2].plot(timeline, [1 - x['SOC'] for x in batteries])

        # _ = axarr[1,0].set_title('Dissipated Power')
        # _ = axarr[1,0].plot(timeline, diss_power)

        # _ = axarr[1,1].set_title('Battery Input Power')
        # _ = axarr[1,1].plot(timeline, [x['input_power'] for x in batteries])

        # fig.show()

        if self.output_folder is not None:
            with open(os.path.join(self.output_folder, key + '.csv'), 'w') as f:
                f.write('time,diss_power (W)\n')
                for t, v in zip(timeline, diss_power):
                    f.write(str(t) + ',' + str(v) + '\n')

            plt.figure(figsize=(30, 10))
            plt.plot(timeline, diss_power)
            plt.title('Dissipated Power')
            plt.xlabel('Time (s)')
            plt.ylabel('Power (W)')
            plt.savefig(os.path.join(self.output_folder, key + '.png'))

        return time + absolute_time

    def step(self, timestep=1):

            params = SystemParameters()

            input_power = 0
            output_power = {
                'Vbat': 0,
                12: 0,
                5: 0,
                3.3: 0,
            }
            diss_power = 0

            for solar_panel in self.solar_panels:
                solar_panel.step(timestep)
                input_power += solar_panel.output * params.solar_efficiency
            comps = list()
            comps += self.components + self.ttcs + self.heaters + [self.payload]
            for component in comps:
                component.step(timestep)
                output_power[component.voltage] += component.input * (2 - params.converters_efficiency) 

            if self.payload.status == 'transfer':
                for ttc in self.ttcs:
                    if ttc.mode == 'S-band':
                        ttc.data = self.payload.output_data      

            power = input_power - sum(output_power.values())
            n_packs = len(self.battery_packs)
            batteries = {
                'input_power': 0,
                'output_power': 0,
                'SOC': 0
            }
            for battery_pack in self.battery_packs:
                battery_pack.step(power/n_packs, timestep)
                batteries['input_power'] += battery_pack.input
                # output_power['Vbat'] += battery_pack.input
                batteries['output_power'] += battery_pack.output
                soc = battery_pack.soc

            batteries['SOC'] += soc 

            if power > 0:
                diss_power = input_power - sum(output_power.values()) - batteries['input_power']
            else:
                diss_power = 0

            return input_power, output_power, batteries, diss_power