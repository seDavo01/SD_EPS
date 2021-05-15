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

        self.key = None
        self.results = dict()
        # self.values = {
        #     'input_power': [],
        #     'output_power': {
        #         'Vbat': 0,
        #         12: 0,
        #         5: 0,
        #         3.3: 0,
        #     },
        #     'batteries': {
        #         'input_power': 0,
        #         'output_power': 0,
        #         'SOC': 0
        #     },
        #     'diss_power': 0,
        # }

        self.output_folder = output_folder

    def reset(self):
        comps = list()
        comps += self.solar_panels + self.components + self.ttcs + self.heaters + self.battery_packs + [self.payload]
        for comp in comps:
            comp.reset()

    def skiptime(self, value):
        comps = list()
        comps += self.solar_panels + self.components + self.ttcs + self.heaters + [self.payload]
        for comp in comps:
            comp.step(value)

    def day(self,
            key: str,
            schedule: list,
            absolute_time: int = 0):
        self.key = key
        self.results[self.key] = {
            'input_power': [],
            'output_power': [],
            'heaters_power': [],
            'batteries': [],
            'diss_power': [],
            'payload_status': [],
            'batteries_status': [],
            'S-band_status': [],
            'heaters_status': [],
        }

        time = 0
        for task in schedule:
            if task == 'acquisition':
                self.payload.next_status = 'acquisition'
                while self.payload.status != 'elaboration' and time < 3600 * 24:
                    time += 1
                    self.step()
                while self.payload.raw_data > 0 and time < 3600 * 24:
                    time += 1
                    self.step()
            elif task == 'transfer':
                self.payload.next_status = 'transfer'
                while self.payload.processed_data > 0 and time < 3600 * 24:
                    time += 1
                    self.step()
            elif task == 'download':
                ttc_idx = 0
                for i, ttc in enumerate(self.ttcs):
                    if ttc.mode == 'S-band':
                        ttc.next_status = 'tx'
                        ttc_idx = i
                while self.ttcs[ttc_idx].data > 0 and time < 3600 * 24:
                    time += 1
                    self.step()

        while time < 3600 * 24:
            time += 1
            self.step()

        return time + absolute_time

    def plot(self):

        timeline = [t for t in range(len(self.results[self.key]['input_power']))]
        fig, axarr = plt.subplots(2, 3, figsize=(50, 20))

        _ = axarr[0,0].set_title('Input Power')
        _ = axarr[0,0].set_xlabel('Time (s)')
        _ = axarr[0,0].set_ylabel('Power (W)')
        _ = axarr[0,0].set_ylim((0, 40))
        _ = axarr[0,0].plot(timeline, self.results[self.key]['input_power'])
        
        _ = axarr[0,1].set_title('Output Power')
        _ = axarr[0,1].set_xlabel('Time (s)')
        _ = axarr[0,1].set_ylabel('Power (W)')
        _ = axarr[0,1].set_ylim((0, 40))
        _ = axarr[0,1].plot(timeline, [sum(x.values()) for x in self.results[self.key]['output_power']])

        _ = axarr[0,2].set_title('Battery DOD')
        _ = axarr[0,2].plot(timeline, [1 - x['SOC'] for x in self.results[self.key]['batteries']])

        _ = axarr[1,0].set_title('Dissipated Power')
        _ = axarr[1,0].set_xlabel('Time (s)')
        _ = axarr[1,0].set_ylabel('Power (W)')
        _ = axarr[1,0].set_ylim((0, 40))
        _ = axarr[1,0].plot(timeline, self.results[self.key]['diss_power'])

        _ = axarr[1,1].set_title('Battery Input Power')
        _ = axarr[1,1].set_xlabel('Time (s)')
        _ = axarr[1,1].set_ylabel('Power (W)')
        _ = axarr[1,1].set_ylim((0, 40))
        _ = axarr[1,1].plot(timeline, [x['input_power'] for x in self.results[self.key]['batteries']])

        _ = axarr[1,2].set_title('Battery Output Power')
        _ = axarr[1,2].set_xlabel('Time (s)')
        _ = axarr[1,2].set_ylabel('Power (W)')
        _ = axarr[1,2].set_ylim((0, 40))
        _ = axarr[1,2].plot(timeline, [x['output_power'] for x in self.results[self.key]['batteries']])

        fig.show()
        plt.savefig(os.path.join('results/plots', self.key + '.jpg'))

    def csv_thermal(self):
        timeline = [t for t in range(len(self.results[self.key]['diss_power']))]
        if self.output_folder is not None:
            with open(os.path.join(self.output_folder, self.key + '.csv'), 'w') as f:
                f.write('time (s),dissipated power (W),solar power (W),payload status,batteries status,s-band status,heaters status\n')
                for t, v, s, p, b, sb, h in zip(timeline, 
                                                self.results[self.key]['diss_power'],
                                                self.results[self.key]['input_power'],
                                                self.results[self.key]['payload_status'],
                                                self.results[self.key]['batteries_status'],
                                                self.results[self.key]['S-band_status'],
                                                self.results[self.key]['heaters_status']):                           
                    values = [str(t), str(v), str(s), p, b, sb, h]
                    line = ','.join(values)
                    f.write(line + '\n')

    def plot_thermal(self):
        timeline = [t for t in range(len(self.results[self.key]['diss_power']))]
        plt.figure(figsize=(30, 10))
        # plt.plot(timeline, self.results[self.key]['input_power'], label = 'solar_power')
        # plt.plot(timeline, self.results[self.key]['heaters_power'], label = 'heaters_power')
        # plt.plot(timeline, [sum(x.values()) for x in self.results[self.key]['output_power']], label = 'loads_power')
        # plt.plot(timeline, [x['input_power'] for x in self.results[self.key]['batteries']], label = 'charging_power')
        # plt.plot(timeline, [sum(x.values()) + y['input_power'] for x, y in zip(self.results[self.key]['output_power'], self.results[self.key]['batteries'])], label = 'loads_power')
        plt.plot(timeline, self.results[self.key]['diss_power'], label = 'diss_power')
        plt.title('Dissipated Power')
        plt.xlabel('Time (s)')
        plt.ylabel('Power (W)')
        # plt.legend()
        plt.savefig(os.path.join(self.output_folder, self.key + '.jpg'))

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
            h_power = 0

            for solar_panel in self.solar_panels:
                solar_panel.step(timestep)
                input_power += solar_panel.output * params.solar_efficiency
            comps = list()
            comps += self.components + self.ttcs + self.heaters + [self.payload]
            for comp in comps:
                comp.step(timestep)
                output_power[comp.voltage] += comp.input * (2 - params.converters_efficiency) 
            for h in self.heaters:
                h_power += h.input * (2 - params.converters_efficiency)

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

            self.results[self.key]['input_power'].append(input_power)
            self.results[self.key]['output_power'].append(output_power)
            self.results[self.key]['batteries'].append(batteries)
            self.results[self.key]['diss_power'].append(diss_power)

            self.results[self.key]['payload_status'].append(self.payload.status)
            self.results[self.key]['batteries_status'].append(self.battery_packs[0].status)
            for ttc in self.ttcs:
                if ttc.mode == 'S-band':
                    self.results[self.key]['S-band_status'].append(ttc.status)
            if self.heaters[0].input > 0:
                heaters_status = 'active'
            else:
                heaters_status = 'inactive'
            self.results[self.key]['heaters_status'].append(heaters_status)

            self.results[self.key]['heaters_power'].append(h_power)