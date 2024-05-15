import time
import cv2
from queue import Queue
import argparse
import threading
import logging

class Sensor:

    def get(self):
        raise NotImplementedError("Subclasses must implement method get()")
    
class SensorX(Sensor):

    '''Sensor X'''
    def __init__(self, delay: float):
        self._delay = delay
        self._data = 0

    def get(self) -> int:
        time.sleep(self._delay)
        self._data += 1
        return self._data
    
class SensorCam:

    def __init__(self, camera_name, resolution):
        self._cap = cv2.VideoCapture(camera_name)
        if not self._cap.isOpened():
            raise Exception(f'Failed to open camera (wrong index {camera_name}).')
        self._camera_name = camera_name
        self._resolution = resolution
        
    def get(self):
        ret, frame = self._cap.read()
        if ret == False:
            logging.error(Exception('Camera not available'))
        frame = cv2.resize(frame, self._resolution)
        return frame

    def __del__(self):
        self._cap.release()

class WindowImage:

    def __init__(self, delay):
        self._delay = delay

    def show(self, name, img):
        cv2.imshow(name, img)
        
    def __del__(self):
        cv2.destroyAllWindows()

def push_to_queue(sensor, queue: Queue):

    while True:
        if queue.full():
            queue.get_nowait()
        else:
            queue.put_nowait(sensor.get())

if __name__ == '__main__':
    logging.basicConfig(filename="./logs/errors.log", level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
    parser = argparse.ArgumentParser(description='parameters')
    parser.add_argument('--camera_index', type=int, default=0)
    parser.add_argument('--resolution', type=str, default='1280x720')
    parser.add_argument('--frequency', type=float, default=60)

    args = parser.parse_args()

    camera_index = args.camera_index
    resolution_str = args.resolution
    delay = 1 / args.frequency
    
    resolution = list(map(int, resolution_str.split('x')))

    camera_sensor = SensorCam(camera_index, resolution)
    sensor0 = SensorX(0.01)
    sensor1 = SensorX(0.1)
    sensor2 = SensorX(1)

    queue0 = Queue(10)
    queue1 = Queue(10)
    queue2 = Queue(10)
    
    thread_sensor0 = threading.Thread(target=push_to_queue, args=(sensor0, queue0), daemon=True)
    thread_sensor1 = threading.Thread(target=push_to_queue, args=(sensor1, queue1), daemon=True)
    thread_sensor2 = threading.Thread(target=push_to_queue, args=(sensor2, queue2), daemon=True)
    
    
    thread_sensor0.start()
    thread_sensor1.start()
    thread_sensor2.start()

    image_window = WindowImage(delay)

    frame = None

    sensor_data0 = 0
    sensor_data1 = 0
    sensor_data2 = 0

    while not (cv2.waitKey(1) & 0xFF == ord('q')):
        try:
            frame = camera_sensor.get()
            if frame is None:
                logging.error(Exception('Unable to read the input.'))
                exit(1)

            if not queue0.empty():
                sensor_data0 = queue0.get_nowait()

            if not queue1.empty():
                sensor_data1 = queue1.get_nowait()

            if not queue2.empty():
                sensor_data2 = queue2.get_nowait()    
        except Exception as error:
            logging.error(error)
        try:      
            if frame is not None:
                frame_copy = frame.copy()
                cv2.putText(frame_copy, 'Sensor0: '+ str(sensor_data0), (frame_copy.shape[1] - 250, frame_copy.shape[0] - 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
                cv2.putText(frame_copy, 'Sensor1: '+ str(sensor_data1), (frame_copy.shape[1] - 250, frame_copy.shape[0] - 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,0,0), 2, cv2.LINE_AA)
                cv2.putText(frame_copy, 'Sensor2: '+ str(sensor_data2), (frame_copy.shape[1] - 250, frame_copy.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2, cv2.LINE_AA)
                image_window.show("lab4", frame_copy)
        except Exception as out:
            logging.error(f'Camera stopped working ({str(out)})')
