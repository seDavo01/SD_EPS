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

        self.output_folder = output_folder
        self.f = None

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
            'total_load_power': [],
            'load_power': [],
            'load_current': [],
            'heaters_power': [],
            'ttc_power': [],
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

    def __plot(self,
               loc: tuple,
               timeline: list,
               name: list, 
               legend: bool = False
               ):

        if type(name) == str:
            self.axarr[loc[0],loc[1]].set_title(name)
            self.axarr[loc[0],loc[1]].set_xlabel('Time (s)')
            self.axarr[loc[0],loc[1]].set_ylabel('Power (W)')
            self.axarr[loc[0],loc[1]].set_ylim((0, 40))
            self.axarr[loc[0],loc[1]].plot(timeline, self.results[self.key][name])
        elif type(name) == list and len(name) == 2:
            c = name[0]
            n = name[1]
            self.axarr[loc[0],loc[1]].set_title(c + ' ' + str(n))
            self.axarr[loc[0],loc[1]].set_xlabel('Time (s)')
            if 'power' in c:
                self.axarr[loc[0],loc[1]].set_ylabel('Power (W)')
                self.axarr[loc[0],loc[1]].set_ylim((0, 40))
            elif 'current' in c:
                self.axarr[loc[0],loc[1]].set_ylabel('Current (A)')
                self.axarr[loc[0],loc[1]].set_ylim((0, 2))
            elif c == 'batteries' and 'power' in n:
                self.axarr[loc[0],loc[1]].set_ylabel('Power (W)')
                self.axarr[loc[0],loc[1]].set_ylim((0, 40))
            self.axarr[loc[0],loc[1]].plot(timeline, [x[n] for x in self.results[self.key][c]])

    def plot(self,
             names: list,
             legend: bool = False,
             ):

        timeline = [t for t in range(len(self.results[self.key]['input_power']))]

        max_col = 3
        l = len(names)
        rc = math.ceil(l/max_col)
        n_x = rc
        n_y = l - max_col * (n_x - 1)
        figsize = (n_y*20, 10*n_x)
        self.fig, self.axarr = plt.subplots(n_x, n_y, figsize=figsize, squeeze=False)

        r = 0
        c = 0
        for name in names:
            self.__plot((r, c), timeline, name, legend)

            c += 1
            if c >= max_col:
                r += 1
                c = 0

        self.fig.show()
        plt.savefig(os.path.join(self.output_folder, self.key + '.jpg'))

    def csv(self,
            names):
        
        timeline = [t for t in range(len(self.results[self.key]['input_power']))]
        if self.output_folder is not None:
            with open(os.path.join(self.output_folder, self.key + '.csv'), 'w') as f:

                f.write('time (s),')
                for name in names:
                    if type(name) == str:
                        if 'power' in name:
                            s = name + ' (W),'
                        elif 'current' in name:
                            s = name + ' (A),'
                        else:
                            s = name + ','
                    elif type(name) == list:
                        if name[0] == 'batteries':
                            if 'power' in name[1]:
                                s = name[0] + ' ' + name[1] + ' (W),'
                            elif 'current' in name[1]:
                                s = name[0] + ' ' + name[1] + ' (A),'
                            else:
                                s = name[0] + ' ' + name[1] + ','
                        else:
                            if 'power' in name[0]:
                                s = name[0] + ' ' + name[1] + ' (W),'
                            elif 'current' in name[0]:
                                s = name[0] + ' ' + name[1] + ' (A),'
                            else:
                                s = name[0] + ' ' + name[1] + ','
                    f.write(s)
                f.write('\n')

                for t in timeline:
                    values = list()
                    values.append(str(t))

                    for name in names:
                        if type(name) == str:
                            values.append(str(self.results[self.key][name][t]))
                        elif type(name) == list:
                            values.append(str(self.results[self.key][name[0]][t][name[1]]))
                    line = ','.join(values)
                    f.write(line + '\n')    



    #     plt.savefig(os.path.join('results/plots', self.key + '.jpg'))

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
        # plt.plot(timeline, [sum(x.values()) for x in self.results[self.key]['load_power']], label = 'loads_power')
        # plt.plot(timeline, [x['input_power'] for x in self.results[self.key]['batteries']], label = 'charging_power')
        # plt.plot(timeline, [sum(x.values()) + y['input_power'] for x, y in zip(self.results[self.key]['load_power'], self.results[self.key]['batteries'])], label = 'loads_power')
        plt.plot(timeline, self.results[self.key]['diss_power'], label = 'diss_power')
        plt.title('Dissipated Power')
        plt.xlabel('Time (s)')
        plt.ylabel('Power (W)')
        # plt.legend()
        plt.savefig(os.path.join(self.output_folder, self.key + '.jpg'))

    def step(self, timestep=1):

            params = SystemParameters()

            input_power = 0
            total_load_power = 0
            load_power = {
                'Vbat': 0,
                12: 0,
                5: 0,
                3.3: 0,
            }
            load_current = {
                'Vbat': 0,
                12: 0,
                5: 0,
                3.3: 0,
            }
            batteries = {
                'input_power': 0,
                'output_power': 0,
                'SOC': 0,
                'DOD': 0,
            }
            diss_power = 0
            h_power = 0
            ttc_power = 0

            for solar_panel in self.solar_panels:
                solar_panel.step(timestep)
                input_power += solar_panel.output * params.solar_efficiency
            comps = list()
            comps += self.components + self.ttcs + self.heaters + [self.payload]
            for comp in comps:
                comp.step(timestep)
                load_power[comp.voltage] += comp.input * (2 - params.converters_efficiency)
            for key, value in load_power.items():
                if type(key) == int or type(key) == float:
                    load_current[key] = value / key 
            for h in self.heaters:
                h_power += h.input * (2 - params.converters_efficiency)
            for ttc in self.ttcs:
                ttc_power += ttc.input * (2 - params.converters_efficiency)

            if self.payload.status == 'transfer':
                for ttc in self.ttcs:
                    if ttc.mode == 'S-band':
                        ttc.data = self.payload.output_data      

            power = input_power - sum(load_power.values())
            n_packs = len(self.battery_packs)
            
            for battery_pack in self.battery_packs:
                battery_pack.step(power/n_packs, timestep)
                batteries['input_power'] += battery_pack.input
                batteries['output_power'] += battery_pack.output
                soc = battery_pack.soc

            batteries['SOC'] += soc
            batteries['DOD'] = 1 - batteries['SOC'] 

            if power > 0:
                diss_power = input_power - sum(load_power.values()) - batteries['input_power']
            else:
                diss_power = 0

            self.results[self.key]['input_power'].append(input_power)
            self.results[self.key]['total_load_power'].append(sum(load_power.values()))
            self.results[self.key]['load_power'].append(load_power)
            self.results[self.key]['load_current'].append(load_current)
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
            self.results[self.key]['ttc_power'].append(ttc_power)