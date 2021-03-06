from datetime import datetime

import math
import pandas as pd
import numpy as np

from .parameters import *

class SolarPanel():

    def __init__(self,
                 cell_parameters: SolarCellParameters,
                 eclipse_data: pd.DataFrame,
                 n_series: int = 1,
                 n_parallel: int = 1,
                 face: str = 'track',
                 angle_data: pd.DataFrame = None,
                 EOL: bool = False
                 ):
        
        self.__parameters = cell_parameters
        self.__voltage = n_series * cell_parameters.voltage
        self.__n_cells = n_series * n_parallel
        self.__current = n_parallel * cell_parameters.current
        # self.__power = self.__voltage * self.__current
        self.__face = face
        if EOL:
            self.__p = cell_parameters.p_EOL
        else:
            self.__p = cell_parameters.p_BOL

        self.__initdata(eclipse_data, angle_data)
        self.reset()

    @property
    def voltage(self):
        return self.__voltage

    @property
    def current(self):
        return self.__current

    @property
    def power(self):
        constant = self.__n_cells * self.__p * self.__parameters.cell_area * self.__parameters.phi
        if self.__face != 'track':
            angle = self.__anglevec[self.time]
            if self.__face == 'z':
                return constant * np.sin(angle)
            if self.__face == 'x':
                if angle < np.pi/2:
                    return  constant * np.cos(angle)
                return constant * np.cos(angle + np.pi)
        return constant
            
    @property
    def time(self):
        return self.__time

    @time.setter
    def time(self, value):
        self.__time = value

    @property
    def active(self):
        return self.__active == 1

    @active.setter
    def active(self, value):
        if value:
            self.__active = 1
        else:
            self.__active = 0

    @property
    def timevec(self):
        return self.__timevec

    @property
    def datalen(self):
        return len(self.__timevec)

    @property
    def output(self):
        if self.active:
            return self.timevec[self.time] * self.power
        return 0

    def reset(self):
        self.__time = -1
        self.active = True
        self.step()

    def __initdata(self, eclipse_data, angle_data):
        missionparameters = MissionParameters()
        date_format = missionparameters.date_format
        dt_mission_end = missionparameters.dt_mission_end

        last_dt = missionparameters.dt_mission_start
        vecs = list()
        for start_time, stop_time in zip(eclipse_data['Start Time (UTCG)'], eclipse_data['Stop Time (UTCG)']):

            dt_start = datetime.strptime(start_time, date_format)
            dt_stop = datetime.strptime(stop_time, date_format)

            if last_dt != dt_start:
                vecs.append(np.ones((dt_start - last_dt).seconds))
            vecs.append(np.zeros((dt_stop - dt_start).seconds))

            last_dt = dt_stop
        vecs.append(np.zeros((dt_mission_end - last_dt).seconds))
        self.__timevec = np.hstack(vecs).tolist()

        if angle_data is not None:
            angles = [np.deg2rad(x) for x in angle_data['DirectionAngle x (deg)']]
            self.__anglevec = angles

    def step(self, timestep = 1):
        
        log = list()
        temp_time = self.__time + timestep
        if temp_time >= self.datalen:
            log.append(['WARNING: no solar data'])
            self.active = False
            return log

        self.__time = temp_time

        return log


class Payload():

    def __init__(self,
                 parameters: PayloadParameters,
                 target_data: pd.DataFrame,
                 eclipse_data: pd.DataFrame,
                 elaboration = 'sunlight'
                 ):

        self.__parameters = parameters
        self.__voltage = parameters.voltage

        self.__power = {
            'idle': parameters.idle_power_consumption,
            'transfer': parameters.idle_power_consumption,
            'elaboration': parameters.elaboration_power_consumption,
            'acquisition': parameters.acquisition_power_consumption
        }   

        self.__elaboration = elaboration

        self.__initdata(target_data, eclipse_data)
        self.reset()

    @property
    def voltage(self):
        return self.__voltage

    @property
    def current(self):
        return self.input/self.__voltage

    @property
    def time(self):
        return self.__time

    @time.setter
    def time(self, value):
        self.__time = value

    @property
    def active(self):
        return self.__active == 1

    @active.setter
    def active(self, value):
        if value:
            self.__active = 1
        else:
            self.__active = 0

    @property
    def start(self):
        return self.__start

    @start.setter
    def start(self, value):
        self.__start = value

    @property
    def raw_data(self):
        return self.__raw_data

    @property
    def processed_data(self):
        return self.__processed_data

    @property
    def output_data(self):
        return self.__output_data

    @property
    def status(self):
        return self.__status

    @property
    def next_status(self):
        return self.__next_status

    @next_status.setter
    def next_status(self, value: str):
        if value in ['idle', 'transfer', 'elaboration', 'acquisition']:
            self.__next_status = value
        else:
            print('invalid status for Payload')

    @property
    def input(self):
        if self.active:
            return self.__power[self.status]
        return 0

    @property
    def timevec(self):
        return self.__timevec

    @property
    def datalen(self):
        return len(self.__timevec)

    @property
    def window(self):
        return self.timevec[self.time] == 1 and self.__sunvec[self.time] == 1

    @property
    def next_window(self):
        for i, (v, s) in enumerate(zip(self.timevec[self.time:], self.__sunvec[self.time:])):
            if v == 1 and s == 1:
                return i
        return 0

    def reset(self):
        self.time = -1
        self.active = True
        self.start = False
        self.__status = 'idle'
        self.__next_status = 'idle'
        self.__raw_data = 0
        self.__processed_data = 0
        self.__output_data = 0
        self.step()

    def __initdata(self, target_data, eclipse_data):
        missionparameters = MissionParameters()
        date_format = missionparameters.date_format
        dt_mission_end = missionparameters.dt_mission_end

        last_dt = missionparameters.dt_mission_start
        vecs = list()
        for start_time, stop_time in zip(target_data['Start Time (UTCG)'], target_data['Stop Time (UTCG)']):
            
            dt_start = datetime.strptime(start_time, date_format)
            dt_stop = datetime.strptime(stop_time, date_format)

            if last_dt != dt_start:
                vecs.append(np.zeros((dt_start - last_dt).seconds))
            vecs.append(np.ones((dt_stop - dt_start).seconds))

            last_dt = dt_stop
        vecs.append(np.zeros((dt_mission_end - last_dt).seconds))
        self.__timevec = np.concatenate(vecs).tolist()
        
        last_dt = missionparameters.dt_mission_start
        vecs = list()
        for start_time, stop_time in zip(eclipse_data['Start Time (UTCG)'], eclipse_data['Stop Time (UTCG)']):

            dt_start = datetime.strptime(start_time, date_format)
            dt_stop = datetime.strptime(stop_time, date_format)

            if last_dt != dt_start:
                vecs.append(np.ones((dt_start - last_dt).seconds))
            vecs.append(np.zeros((dt_stop - dt_start).seconds))

            last_dt = dt_stop
        vecs.append(np.zeros((dt_mission_end - last_dt).seconds))
        self.__sunvec = np.hstack(vecs).tolist()

    def step(self, timestep = 1):
        log = list()
        temp_time = self.time + timestep
        if temp_time >= self.datalen:
            log.append(['WARNING: no payload access data'])
            self.active = False
            return log

        self.time = temp_time

        if self.window and self.status == 'idle' and self.next_status == 'acquisition':
            self.__status = 'acquisition'
            # self.start = False
        if not self.window and self.status == 'acquisition':
            if self.next_window < 6000:
                self.__status = 'idle'
                self.next_status == 'acquisition'
            else:
                self.__status = 'elaboration'
                self.next_status = 'idle'

        if self.__elaboration == 'sunlight':
            if self.status == 'elaboration' and self.__sunvec[self.time] == 0:
                self.__status = 'idle'
                self.next_status = 'elaboration'
            elif self.status == 'idle' and self.next_status == 'elaboration' and self.__sunvec[self.time] == 1:
                self.__status = 'elaboration'
                self.next_status = 'idle'
        else:
            if self.status == 'idle' and self.next_status == 'elaboration':
                self.__status = 'elaboration'
                self.next_status = 'idle'

        if self.status == 'idle' and self.next_status == 'transfer':
            self.__status = 'transfer'
            self.next_status = 'idle'

        if self.status == 'acquisition':
            self.__raw_data += self.__parameters.acquisition_datarate * timestep
        elif self.status == 'elaboration':
            self.__raw_data += self.__parameters.elaboration_datarate[0] * timestep
            self.__processed_data += self.__parameters.elaboration_datarate[1] * timestep
            if self.__raw_data < 0:
                self.__status = 'idle'
                self.next_status = 'idle'
                self.__raw_data = 0
        elif self.status == 'transfer':
            self.__processed_data -= self.__parameters.transfer_datarate * timestep
            self.__output_data = self.__parameters.transfer_datarate * timestep
            if self.__processed_data < 0:
                self.__status = 'idle'
                self.next_status = 'idle'
                self.__processed_data = 0
                self.__output_data = 0

                # print(self.__processed_data)
                # self.__processed_data = 0

        return log


class TTC():

    def __init__(self,
                 parameters: TTCParameters,
                 mode: str = 'S-band',
                 sunlight: bool = False,
                 target: bool = False,
                 GS_data: list = None,
                 eclipse_data: pd.DataFrame = None,
                 target_data: pd.DataFrame = None,
                 ):
        
        if mode not in ['S-band', 'UHF']:
            raise ValueError('mode need to be S-band or UHF')
        else:
            if sunlight and type(eclipse_data) != pd.core.frame.DataFrame:
                raise ValueError('missing eclipse data')
            if target and type(target_data) != pd.core.frame.DataFrame:
                raise ValueError('missing target data')
            if mode == 'S-band' and GS_data == None:
                raise ValueError('while using S-band, it is needed to have GS_data')
        self.__mode = mode

        self.__parameters = parameters
        self.__voltage = parameters.voltage

        self.__power = {
            'idle': parameters.idle_power_consumption[mode],
            'rx': parameters.rx_power_consumption[mode],
            'tx': parameters.tx_power_consumption[mode],
            'rx/tx': parameters.average_power_consumption[mode]
        }   

        self.__initdata(GS_data, sunlight, eclipse_data, target, target_data)
        self.reset()

    @property
    def voltage(self):
        return self.__voltage

    # @property
    # def current(self):
    #     return self.__current

    @property
    def mode(self):
        return self.__mode

    @property
    def time(self):
        return self.__time

    @time.setter
    def time(self, value):
        self.__time = value

    @property
    def active(self):
        return self.__active == 1

    @active.setter
    def active(self, value):
        if value:
            self.__active = 1
        else:
            self.__active = 0

    @property
    def data(self):
        return self.__data

    @data.setter
    def data(self, value):
        self.__data += value

    @property
    def total_downloaded(self):
        return self.__total_downloaded

    @property
    def status(self):
        return self.__status

    @property
    def next_status(self):
        return self.__next_status

    @next_status.setter
    def next_status(self, value: str):
        if value in ['idle', 'rx', 'tx', 'rx/tx']:
            self.__next_status = value
        else:
            print('invalid status for TTC')

    @property
    def input(self):
        if self.active:
            return self.__power[self.status]
        return 0

    @property
    def timevec(self):
        return self.__timevec

    @property
    def datalen(self):
        return len(self.__timevec)

    @property
    def window(self):
        # if self.timevec == None and self.__sunvec == None and self.__targetvec == None:
        #     return True
        result = True
        if self.timevec is not None:
            result = self.timevec[self.time] == 1
        if self.__sunvec is not None:
            if result:
                result = self.__sunvec[self.time] == 1
        if self.__targetvec is not None:
            if result:
                result = self.__targetvec[self.time] == 1
        return result

    # @property
    # def next_window(self):
    #     if self.timevec is not None:
    #         for i, v in enumerate(self.timevec[self.time:]):
    #             if v == 1:
    #                 return i
    #     return 0

    def reset(self):
        self.time = -1
        self.active = True
        self.__status = 'idle'
        if self.__mode == 'UHF':
            self.next_status = 'rx/tx'
        else:
            self.next_status = 'idle'
        self.__data = 0
        self.__total_downloaded = 0
        self.step()

    def __initdata(self, GS_data, sunlight, eclipse_data, target, target_data):
        missionparameters = MissionParameters()
        date_format = missionparameters.date_format
        last_dt = missionparameters.dt_mission_start
        dt_mission_end = missionparameters.dt_mission_end

        if GS_data is not None:
            timevecs = list()
            for data in GS_data:
                last_dt = missionparameters.dt_mission_start
                vecs = list()
                for start_time, stop_time in zip(data['Start Time (UTCG)'], data['Stop Time (UTCG)']):
                    
                    dt_start = datetime.strptime(start_time, date_format)
                    dt_stop = datetime.strptime(stop_time, date_format)

                    if last_dt != dt_start:
                        vecs.append(np.zeros((dt_start - last_dt).seconds))
                    vecs.append(np.ones((dt_stop - dt_start).seconds))

                    last_dt = dt_stop
                vecs.append(np.zeros((dt_mission_end - last_dt).seconds))
                timevecs.append(np.concatenate(vecs))

            max_len = 0
            for timevec in timevecs:
                if len(timevec) > max_len:
                    max_len = len(timevec)
            for i, timevec in enumerate(timevecs):
                if len(timevec) < max_len:
                    timevecs[i] = np.concatenate((timevec, np.zeros((max_len - len(timevec)))))

            timevec = np.sum(timevecs, 0)
            access = timevec > 0
            self.__timevec = [1 if t else 0 for t in access]
        else:
            self.__timevec = None

        if sunlight:
            last_dt = missionparameters.dt_mission_start
            vecs = list()
            for start_time, stop_time in zip(eclipse_data['Start Time (UTCG)'], eclipse_data['Stop Time (UTCG)']):

                dt_start = datetime.strptime(start_time, date_format)
                dt_stop = datetime.strptime(stop_time, date_format)

                if last_dt != dt_start:
                    vecs.append(np.ones((dt_start - last_dt).seconds))
                vecs.append(np.zeros((dt_stop - dt_start).seconds))

                last_dt = dt_stop
            vecs.append(np.zeros((dt_mission_end - last_dt).seconds))
            self.__sunvec = np.hstack(vecs).tolist()
        else:
            self.__sunvec = None

        if target:
            last_dt = missionparameters.dt_mission_start
            vecs = list()
            for start_time, stop_time in zip(target_data['Start Time (UTCG)'], target_data['Stop Time (UTCG)']):
                
                dt_start = datetime.strptime(start_time, date_format)
                dt_stop = datetime.strptime(stop_time, date_format)

                if last_dt != dt_start:
                    vecs.append(np.zeros((dt_start - last_dt).seconds))
                vecs.append(np.ones((dt_stop - dt_start).seconds))

                last_dt = dt_stop
            vecs.append(np.zeros((dt_mission_end - last_dt).seconds))
            self.__targetvec = np.concatenate(vecs).tolist()
        else:
            self.__targetvec = None
    
    def step(self, timestep = 1):
        
        log = list()
        temp_time = self.time + timestep
        # if temp_time >= self.datalen:
        #     log.append(['WARNING: no TTC data'])
        #     self.active = False
        #     return log

        self.time = temp_time

        if self.__mode == 'S-band':
            if self.window and self.status == 'idle' and self.next_status == 'tx':
                self.__status = 'tx'
            if not self.window and self.status == 'tx':
                self.__status = 'idle'

            if self.status == 'tx':
                self.__data -= self.__parameters.datarate * timestep
                self.__total_downloaded += self.__parameters.datarate * timestep
            elif self.status == 'idle':
                if self.__data < 0:
                    self.next_status = 'idle'
                    self.__data = 0
        elif self.__mode == 'UHF':
            if self.window and self.status == 'idle' and self.next_status == 'rx/tx':
                self.__status = 'rx/tx'
            elif not self.window and self.status == 'rx/tx':
                self.__status = 'idle'

        return log


class BatteryPack():

    def __init__(self,
                 parameters: BatteryCellParameters,
                 n_series: int = 1,
                 n_parallel: int = 1,
                 starting_SOC: float = 0.8,
                 EOL: bool = False,
                 ):

        self.__parameters = parameters
        self.__voltage = n_series * parameters.voltage
        self.__nominal_capacity = n_parallel * parameters.nominal_capacity
        if EOL:
            self.__capacity = parameters.efficiency * self.__nominal_capacity
        else:
            self.__capacity = self.__nominal_capacity
        self.__starting_SOC = starting_SOC
        self.__SOC = starting_SOC

        self.reset()

    @property
    def voltage(self):
        return self.__voltage

    @property
    def soc(self):
        return self.__SOC

    @property
    def active(self):
        return self.__active == 1

    @active.setter
    def active(self, value):
        if value:
            self.__active = 1
        else:
            self.__active = 0

    @property
    def status(self):
        return self.__status

    @property
    def input(self):
        if self.active:
            return self.__input

    @property
    def output(self):
        if self.active:
            return self.__output

    def reset(self):
        self.__status = 'idle'
        self.active = True
        self.__SOC = self.__starting_SOC
        self.__input = 0
        self.__output = 0

    def step(self, power, timestep = 1):
        log = list()
        if power > 0:
            self.__output = 0
            base = self.__parameters.min_charge_rate * self.__capacity * self.voltage
            cstep = self.__parameters.charge_step * self.__capacity * self.voltage
            cap = self.__parameters.max_charge_rate * self.__capacity * self.voltage
            if self.__SOC >= 1:
                self.__SOC = 1
                self.__input = 0
            elif power > cap:
                    # while power > (base + cstep) and base < cap:
                    #     base += base + cstep
                self.__input = cap
            elif power > base:
                r = (power - base) / cstep
                self.__input = base + math.floor(r) * cstep 
            else:
                self.__input = 0
            
            if self.input > 0:
                self.__SOC += self.input / (self.__capacity * self.voltage) * timestep / 3600
                self.__status = 'charging'
            else:
                self.__status = 'idle'
        elif power < 0:
            self.__input = 0
            if self.__SOC <= 0:
                self.__SOC = 0
                self.__output = 0
                self.__status = 'dead'
                log.append('Battery failure')
            elif abs(power) < self.__parameters.max_discharge_rate * self.__capacity * self.voltage:
                self.__output = abs(power)
                self.__SOC -= (self.__output / (self.__capacity * self.voltage)) * timestep / 3600
                self.__status = 'discharging'
            else:
                self.__status = 'failure'
                log.append('Battery failure')
        
        return log


class Component():

    def __init__(self,
                 parameters: ComponentParameters,
                 eclipse_data: pd.DataFrame = None,
                 ):
        
        if parameters.sunlight and type(eclipse_data) != pd.core.frame.DataFrame:
            raise ValueError('missing eclipse data')

        self.__parameters = parameters
        self.__voltage = parameters.voltage 
        self.__power = parameters.power

        if parameters.sunlight:
            self.__initdata(eclipse_data)
        else:
            self.__sunvec = None
        self.reset()

    @property
    def voltage(self):
        return self.__voltage

    # @property
    # def current(self):
    #     return self.__current

    @property
    def time(self):
        return self.__time

    @time.setter
    def time(self, value):
        self.__time = value

    @property
    def active(self):
        return self.__active == 1

    @active.setter
    def active(self, value):
        if value:
            self.__active = 1
        else:
            self.__active = 0

    @property
    def input(self):
        if self.active:
            if self.__sunvec is not None:
                return self.__power * self.__sunvec[self.time]
            return self.__power
        return 0

    def reset(self):
        self.time = -1
        self.active = True
        self.step()

    def __initdata(self, eclipse_data):
        missionparameters = MissionParameters()
        date_format = missionparameters.date_format
        last_dt = missionparameters.dt_mission_start
        dt_mission_end = missionparameters.dt_mission_end

        last_dt = missionparameters.dt_mission_start
        vecs = list()
        for start_time, stop_time in zip(eclipse_data['Start Time (UTCG)'], eclipse_data['Stop Time (UTCG)']):

            dt_start = datetime.strptime(start_time, date_format)
            dt_stop = datetime.strptime(stop_time, date_format)

            if last_dt != dt_start:
                vecs.append(np.ones((dt_start - last_dt).seconds))
            vecs.append(np.zeros((dt_stop - dt_start).seconds))

            last_dt = dt_stop
        vecs.append(np.zeros((dt_mission_end - last_dt).seconds))
        self.__sunvec = np.hstack(vecs).tolist()

    def step(self, timestep = 1):
        
        log = list()
        temp_time = self.time + timestep
        if self.__sunvec is not None:
            if temp_time >= len(self.__sunvec):
                log.append(['WARNING: no {} data'.format(self.__parameters.name)])
                self.active = False
                return log

        self.time = temp_time

        return log


class Heater():

    def __init__(self,
                 parameters: HeaterParameters,
                 eclipse_data: pd.DataFrame = None,
                 ):
        
        if type(eclipse_data) != pd.core.frame.DataFrame:
            raise ValueError('missing eclipse data')

        self.__parameters = parameters
        self.__voltage = parameters.voltage 
        self.__power = parameters.power_consumption

        self.__initdata(eclipse_data)
        self.reset()

    @property
    def voltage(self):
        return self.__voltage

    # @property
    # def current(self):
    #     return self.__current

    @property
    def time(self):
        return self.__time

    @time.setter
    def time(self, value):
        self.__time = value

    @property
    def active(self):
        return self.__active == 1

    @active.setter
    def active(self, value):
        if value:
            self.__active = 1
        else:
            self.__active = 0

    @property
    def input(self):
        if self.active:
            if self.__heatvec is not None:
                return self.__power * self.__heatvec[self.time]
            return self.__power
        return 0

    def reset(self):
        self.time = -1
        self.active = True
        self.step()

    def __initdata(self, eclipse_data):
        missionparameters = MissionParameters()
        date_format = missionparameters.date_format
        dt_mission_end = missionparameters.dt_mission_end

        last_dt = missionparameters.dt_mission_start
        vecs = list()
        for start_time, stop_time in zip(eclipse_data['Start Time (UTCG)'], eclipse_data['Stop Time (UTCG)']):

            dt_start = datetime.strptime(start_time, date_format)
            dt_stop = datetime.strptime(stop_time, date_format)

            if last_dt != dt_start:
                sun = (dt_start - last_dt).seconds
                if self.__parameters.sun_duration > 0:
                    act = math.floor(sun * self.__parameters.sun_duration)
                    vecs.append(np.ones(act))
                    vecs.append(np.zeros(sun - act))
                else:
                    vecs.append(np.zeros(sun))
            eclipse = (dt_stop - dt_start).seconds
            if self.__parameters.eclipse_duration > 0:
                if eclipse > 10:
                    act = math.floor(eclipse * self.__parameters.eclipse_duration)
                    vecs.append(np.zeros(eclipse - act))
                    vecs.append(np.ones(act))
                else:
                    if vecs[-1][-1] == 1:
                        vecs.append(np.ones(eclipse))
                    else:
                        vecs.append(np.zeros(eclipse))
            else:
                vecs.append(np.zeros(eclipse))

            last_dt = dt_stop
        vecs.append(np.zeros((dt_mission_end - last_dt).seconds))

        self.__heatvec = np.hstack(vecs).tolist()

    def step(self, timestep = 1):
        
        log = list()
        temp_time = self.time + timestep
        if self.__heatvec is not None:
            if temp_time >= len(self.__heatvec):
                log.append(['WARNING: no Heater data'])
                self.active = False
                return log

        self.time = temp_time

        return log