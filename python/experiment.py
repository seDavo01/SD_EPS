import os 
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size': 30})

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

        self.missionparameters = MissionParameters()

        self.key = None
        self.results = dict()

        self.output_folder = output_folder
        self.f = None

    def reset(self):
        comps = list()
        comps += self.solar_panels + self.components + self.ttcs + self.heaters + self.battery_packs + [self.payload]
        for comp in comps:
            comp.reset()

    def skiptime(self, value=1):
        comps = list()
        comps += self.solar_panels + self.components + self.ttcs + self.heaters + [self.payload]
        for comp in comps:
            comp.step(value)
        sun_check = sum([x.output for x in self.solar_panels])
        skip = True
        while skip:
            for comp in comps:
                comp.step()
            sun = sum([x.output for x in self.solar_panels])
            if sun_check > 0:
                if sun == 0:
                    skip = False
            else:
                if sun > 0:
                    skip = False

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
            'UHF_status': [],
            'heaters_status': [],
            'solar_energy': [],
            'load_energy': [],
            'battery_input_energy': [],
            'battery_output_energy': [],
        }

        orbit_period = self.missionparameters.orbit_period
        n_orbit = self.missionparameters.n_orbit
        max_time = n_orbit * orbit_period

        time = 0
        for task in schedule:
            if task == 'acquisition':
                self.payload.next_status = 'acquisition'
                while self.payload.status != 'elaboration' and time < max_time:
                    time += 1
                    self.step()
                while self.payload.raw_data > 0 and time < max_time:
                    time += 1
                    self.step()
            elif task == 'transfer':
                self.payload.next_status = 'transfer'
                while self.payload.processed_data > 0 and time < max_time:
                    time += 1
                    self.step()
            elif task == 'download':
                ttc_idx = 0
                for i, ttc in enumerate(self.ttcs):
                    if ttc.mode == 'S-band':
                        ttc.next_status = 'tx'
                        ttc_idx = i
                while self.ttcs[ttc_idx].data > 0 and time < max_time:
                    time += 1
                    self.step()

        while time < max_time:
            time += 1
            self.step()

        t = 0
        for _ in range(n_orbit):
            self.results[self.key]['solar_energy'].append(sum([x for x in self.results[self.key]['input_power'][t:t+orbit_period]])/3600)
            self.results[self.key]['load_energy'].append(sum([x for x in self.results[self.key]['total_load_power'][t:t+orbit_period]])/3600)
            self.results[self.key]['battery_input_energy'].append(sum([x['input_power'] for x in self.results[self.key]['batteries'][t:t+orbit_period]])/3600)
            self.results[self.key]['battery_output_energy'].append(sum([x['output_power'] for x in self.results[self.key]['batteries'][t:t+orbit_period]])/3600)
            t += orbit_period

        return time + absolute_time

    def energyplot(self):
        fontsize = 30
        timeline = [t for t in range(self.missionparameters.n_orbit)]

        fig, axarr = plt.subplots(1, 1, figsize=(20, 10), squeeze=False)
        
        axarr[0,0].plot(timeline, self.results[self.key]['solar_energy'], label='Solar')
        axarr[0,0].plot(timeline, self.results[self.key]['load_energy'], label='Loads')
        axarr[0,0].plot(timeline, self.results[self.key]['battery_input_energy'], label='Battery input')
        axarr[0,0].plot(timeline, self.results[self.key]['battery_output_energy'], label='Battery output')

        axarr[0,0].set_ylabel('Energy (Wh)', fontsize=fontsize)
        axarr[0,0].set_xlabel('Orbit n.', fontsize=fontsize)
        axarr[0,0].set_xlim((0, self.missionparameters.n_orbit-1))
        axarr[0,0].set_ylim((0, 40))
        axarr[0,0].legend(loc='lower right', fontsize=20)

        fig.show()
        plt.savefig(os.path.join(self.output_folder, self.key + '_energy' + '.jpg'), 
                    bbox_inches = 'tight',
                    pad_inches = 0.1)

    def __plot(self,
               loc: tuple,
               timeline: list,
               name: list,
               legend: bool = False
               ):

        fontsize = 30
        l_name = []
        if type(name) == str:
            # self.axarr[loc[0],loc[1]].set_title(name)
            l_name.append(name)
            # self.axarr[loc[0],loc[1]].set_xlabel('Time (h)', fontsize=fontsize)
            self.axarr[loc[0],loc[1]].set_ylabel('Power (W)', fontsize=fontsize)
            self.axarr[loc[0],loc[1]].set_ylim((0, 40))
            self.axarr[loc[0],loc[1]].plot(timeline, self.results[self.key][name])
        elif type(name) == list and len(name) == 2:
            c = name[0]
            n = name[1]
            l_name.append('_'.join(name))
            # self.axarr[loc[0],loc[1]].set_title(c + ' ' + str(n))
            # self.axarr[loc[0],loc[1]].set_xlabel('Time (h)', fontsize=fontsize)
            if 'power' in c:
                self.axarr[loc[0],loc[1]].set_ylabel('Power (W)', fontsize=fontsize)
                self.axarr[loc[0],loc[1]].set_ylim((0, 40))
            elif 'current' in c:
                self.axarr[loc[0],loc[1]].set_ylabel('Current (A)', fontsize=fontsize)
                self.axarr[loc[0],loc[1]].set_ylim((0, 2))
            elif c == 'batteries':
                if 'power' in n:
                    self.axarr[loc[0],loc[1]].set_ylabel('Power (W)', fontsize=fontsize)
                    self.axarr[loc[0],loc[1]].set_ylim((0, 40))
                elif n=='DOD':
                    self.axarr[loc[0],loc[1]].set_ylim((0.10, 0))
                elif n=='SOC':
                    self.axarr[loc[0],loc[1]].set_ylim((0.9, 1))
            self.axarr[loc[0],loc[1]].plot(timeline, [x[n] for x in self.results[self.key][c]])
        
        self.axarr[loc[0],loc[1]].set_xlabel('Time (h)', fontsize=fontsize)
        self.axarr[loc[0],loc[1]].set_xlim((0, self.missionparameters.orbit_period*15/3600))
        # self.axarr[loc[0],loc[1]].get_xticklabels().set_fontsize(fontsize)

        return l_name

    def plot(self,
             names: list,
             legend: bool = False,
             max_col: int = 3,
             ):

        timeline = [t/3600 for t in range(len(self.results[self.key]['input_power']))]

        # max_col = 3
        l = len(names)
        rc = math.ceil(l/max_col)
        n_x = rc
        n_y = l - max_col * (n_x - 1)
        figsize = (n_y*20, 10*n_x)
        self.fig, self.axarr = plt.subplots(n_x, n_y, figsize=figsize, squeeze=False)

        l_name = [self.key]
        r = 0
        c = 0
        for name in names:
            l_name += self.__plot((r, c), timeline, name, legend)

            c += 1
            if c >= max_col:
                r += 1
                c = 0

        f_name = '-'.join(l_name)
        self.fig.show()
        plt.savefig(os.path.join(self.output_folder, f_name + '.jpg'), 
                    bbox_inches = 'tight',
                    pad_inches = 0.1)

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
                elif ttc.mode == 'UHF':
                    self.results[self.key]['UHF_status'].append(ttc.status)
            if self.heaters[0].input > 0:
                heaters_status = 'active'
            else:
                heaters_status = 'inactive'
            self.results[self.key]['heaters_status'].append(heaters_status)

            self.results[self.key]['heaters_power'].append(h_power)
            self.results[self.key]['ttc_power'].append(ttc_power)