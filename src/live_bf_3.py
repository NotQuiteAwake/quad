import os, time
import numpy as np

from datetime import datetime
from lib import ard, plotter, utils, drone
from dataclasses import asdict
from numbers import Number

from camera import *


def sanity_check(cam_height,ultrasound_height):
    #the idea is that if the camera height deviates too much something has likely gone wrong and use ultrasound value instead.

    if np.abs(cam_height-ultrasound_height)>=3:
        print(f"Converted height of {cam_height} did not pass sanity check.")
        return ultrasound_height
    return cam_height


class BFLive:
    PLATFORM: str = 'betaflight-2'
    PLOT_LAYOUT: dict = {(0, 0): 'mean_rpm',
                         (0, 1): 'total_mass',
                         (1, 0): 'dist',
                         (1, 1): 'accel_comp'}
    PLOT_NROWS: int = 2
    PLOT_NCOLS: int = 2

    # bf_name: path to betaflight-configurator executable.
    def __init__(self, path: str, bf_name: str = None):
        print('BFLive::__init__: initialising.')
        self.path = path
        self.quad = drone.Drone(bf_name)
        self.ardman = ard.ArdManager()
        self.plotter = plotter.Plotter(self.PLOT_NROWS, self.PLOT_NCOLS, self.PLOT_LAYOUT)

        self.t_str = datetime.now().strftime('%m-%d')
        self.timestamp = time.time()    # timestamp acts as a UUID for this set of data

        self.cnt = -1
        for filename in os.listdir(path):
            file = os.path.join(path, filename) 
            if not os.path.isfile(file) or "json" not in filename:
                continue
            try:
                cnt = int(filename.split('.')[-2].split('_')[-1])
                self.cnt = max(self.cnt, cnt)
            except ValueError:
                print(f'BFLive::__init__: ValueError: Could not parse cnt value in filename {filename}.')
        self.cnt = self.cnt + 1

        print('BFLive::__init__: init complete.')

    def set_height(self, height: float):
        # calling set_height on arduino #0
        self.ardman[0].set_height(height, block = True)

    # move by steps, then level if needed.
    def move_level(self, steps: list):
        self.ardman.move(steps, block = True)
        #self.ardman[0].level()

    def level(self):
        #print("Levelling...")
        self.ardman[0].level()

    def start(self, height: float, rpm_queue: list, rec_t: float, transient:float):
        print('BFLive::start: the following parameters are scheduled for testing.')
        print(f'height: {height}')
        print('rpm_queue:', *rpm_queue, sep = '\n- ')
        input('BFLive::start: confirm: ')

        # record is not responsible for arming, this way we can emergency quit and record won't rearm our drone.
        self.quad.set_arming(True)
        self.quad.set_rpm_worker_on(True)

        for rpm in rpm_queue:
            self.record(height, rpm, rec_t, transient)

        self.quad.set_rpm_worker_on(False)
        self.quad.set_arming(False)


    def start_with_camera(self, height_queue: list, rpm_queue: list, rec_t: float, transient:float, camera):

        print('BFLive::start: the following parameters are scheduled for testing.')
        print('height_queue:', *height_queue, sep = ', ')
        print('rpm_queue:', *rpm_queue, sep = '\n- ')
        input('BFLive::start: confirm: ')

        # record is not responsible for arming, this way we can emergency quit and record won't rearm our drone.
        self.quad.set_arming(True)
        self.quad.set_rpm_worker_on(True)

        for height in height_queue:
            print(f"\nBFLive::start: Setting height to {height}cm...")
            live.set_height(height)
            print(f"BFLive::start: Height set to {height}cm.")

            camera.take_picture(filename=f"{height}cm_")
            for rpm in rpm_queue:
                self.record(height, rpm, rec_t, transient)

        self.quad.set_rpm_worker_on(False)
        self.quad.set_arming(False)



    # target_rpm can be of multiple types, set_rpm function deal with this automatically. 
    def record(self, height: float, target_rpm: Number|list, rec_t: float, transient:float):
        print(f'\nBFLive::record: preparing for height = {height}, target_rpm = {target_rpm}, rec_t = {rec_t}')
        if isinstance(target_rpm, Number):
            target_rpm = [target_rpm] * self.quad.NUM_OF_MOTORS

        filename = f'bf_{height}_{target_rpm}_{self.t_str}_{self.cnt}.json'
        file = os.path.join(self.path, filename)
        data = utils.Data(height = height,
                          target_rpm = target_rpm,
                          timestamp = self.timestamp,
                          platform = self.PLATFORM)

        #input('Confirm continue: ')
        time.sleep(transient)

        print(f'BFLive::record: taring all load cells.')
        self.ardman.tare(block = True)
        time.sleep(5)
        print('BFLive::record: load cells tared.')

        self.quad.set_rpm_worker_on(True)
        self.quad.set_rpm(target_rpm, block = True, hold_throttle = True)
        print('BFLive::record: target_rpm range reached, throttle is now fixed.')
        print(f'BFLive::record: waiting for transient: {transient}s.')
        time.sleep(transient)

        print(f"Time: {datetime.fromtimestamp(time.time())}")
        print(f'BFLive::record: recording started...')
        t = time.time()

        """
        #This is the old record function that uses the ultrasound height measurements.
        #Would like to replace with camera measurement.

        while time.time() - t < rec_t:
            rpm = self.quad.get_rpm()
            ct = time.time() - t
            data.add(t = ct,
                     rpm = rpm,
                     **asdict(self.ardman.get_reading())
                     )
            self.plotter.plot(data)
        
        """

        while time.time() - t < rec_t:
            rpm = self.quad.get_rpm()
            ct = time.time() - t

            cam_dist=sanity_check(camera.get_height(),height)
            dict=asdict(self.ardman.get_reading())
            dict.update({'dist':[cam_dist]})

            data.add(t = ct,
                     rpm = rpm,
                     **dict
                     )
            self.plotter.plot(data)

        

        print('BFLive::record: dumping raw data.')
        data.dump(file)
        data2 = utils.Data()
        data2.load(file)
        print(f'BFLive::record: dumped == original: {data2 == data}')

        self.quad.set_rpm_worker_on(False)
        self.quad.set_throttle(0)


    def close(self):
        self.quad.set_rpm_worker_on(False)
        self.quad.set_arming(False)

if __name__ == '__main__':
    # rpm_queue = [2000, 4000] + np.linspace(6000, 12000, 7).tolist()

    rpm_queue = np.linspace(2000,8000,7).tolist()

    height_queue=np.arange(10,102,2).tolist()
    
    rec_t = 30
    transient = 5
    # rec_path = '../raw/bf2/120mm_prop_spacing_4inch_prop'
    rec_path = 'data/10-04-2024-240mm'

    image_save_path=os.path.join(rec_path,'images')
    os.makedirs(image_save_path, exist_ok=True)

    camera=Camera(serial_number='18181990',save_path=image_save_path)

    camera.take_picture("test_")
    live = BFLive(path=rec_path)
    live.start_with_camera(height_queue = height_queue,
               rpm_queue = rpm_queue,
               rec_t = rec_t,
               transient = transient,
               camera=camera)


