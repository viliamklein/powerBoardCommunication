from pyftdi import i2c
import datetime
import threading
import queue
import time

from influxdb_client import InfluxDBClient, Point, WriteOptions

class iadc:

    devname = 'ftdi://ftdi:232h:1/1'
    devI2CAddress = 0x23

    def __init__(self):

        self.iic = i2c.I2cController()
        self.iic.configure('ftdi://ftdi:232h:1/1')
        self.io = self.iic.get_port(self.devI2CAddress)

        # config so that filter bit is on 
        # and channels 1-7 (NOT 8) are enabled
        try:
            self.io.write_to(2, [0x07, 0xF8], relax=True)
        
        except i2c.I2cNackError:
            # print('here')
            pass

        try:
            self.io.write_to(2, [0x07, 0xF8], relax=True)
        
        except i2c.I2cNackError:
            print('caught NACK. Try again')
            # print('fail')
            raise


        self.convResults = dict.fromkeys(range(1,8))
        self.convResults['time'] = None
    
    def __del__(self):
        self.iic.close()
        # self.io.flush()
        # print('here')

    
    def readAllChannels(self):
        
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        self.convResults['time'] = timestamp

        # Writing 0b0111 to C3-C1 bits
        self.io.write([0x70], relax=False, start=True)
        resArray = self.io.read(14, relax=True, start=True)

        for idx, xx in enumerate(resArray[::2]):
            chanNum = (int(xx) & 0x70) >> 4
            # print(f'Channel Number {chanNum:02d} ', end=' ')

            conv = (int(xx) & 0x0F) << 8
            conv = conv | (int(resArray[idx+1]))
            
            self.convResults[idx+1] = conv
        # print("")
            
def influx_writer_thread(data_queue,):

    buffer = []
    buffer_size = 50

    with InfluxDBClient.from_config_file("influxconfig.ini") as client:

        with client.write_api(write_options=WriteOptions(batch_size=200, flush_interval=100)) as writer:

            while True:
                # Get the data from the queue
                data = data_queue.get()
                buffer.append(data)

                # If the buffer has enough lines, write to the file
                if len(buffer) >= buffer_size:
                    # with open(logfile_name, "a") as file:
                    #     file.write("\n".join(buffer) + "\n")
                    # print("write to influx")
                    points = []
                    for data in buffer:
                        line = data.split(',')
                        tt = int(datetime.datetime.strptime(line[-2], ' %Y-%m-%d %H:%M:%S.%f').timestamp()*1E9)
                        # print(line)
                        dp = Point('CurrentADC') \
                        .tag("type", "testing") \
                        .field("5V", float(line[0])) \
                        .field("MC2", float(line[1])) \
                        .field("12V", float(line[2])) \
                        .field("MC1", float(line[3])) \
                        .field("24V", float(line[4])) \
                        .field("OB", float(line[5])) \
                        .field("Battery", float(line[6])) \
                        .time(tt)

                        points.append(dp.to_line_protocol())
                        # break
                    
                    # Clear the buffer after writing
                    writer.write(bucket="Powerboard Current Data", record=points)
                    buffer.clear()
                
                # Mark the queue task as done
                data_queue.task_done()
        

def file_writer_thread(sensor_queue, logfile_name):
    buffer = []
    buffer_size = 100  # Number of lines to store before writing to the file

    while True:
        # Get the data from the queue
        data = sensor_queue.get()
        buffer.append(data)
        
        # If the buffer has enough lines, write to the file
        if len(buffer) >= buffer_size:
            with open(logfile_name, "a") as file:
                file.write("\n".join(buffer) + "\n")
            
            # Clear the buffer after writing
            buffer.clear()
        
        # Mark the queue task as done
        sensor_queue.task_done()

def main():
    line = ""
    current = iadc()
    # for xx in range(10):

    # Create a queue to communicate between threads
    sensor_queue = queue.Queue()
    influx_queue = queue.Queue()

    # Get the current date and time to use in the filename
    current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    logfile_name = f"{current_time}_current_sensor_data.log"

    # Start the file-writing thread with the logfile name
    threading.Thread(target=file_writer_thread, args=(sensor_queue, logfile_name), daemon=True).start()
    threading.Thread(target=influx_writer_thread, args=(influx_queue, ), daemon=True).start()
    
    runflag = True
    try:
        while runflag:
            try:
                current.readAllChannels()
                # print(current.convResults)
                
                for val in current.convResults:
                    line += f'{current.convResults[val]}, '

                # line += '\n'
                sensor_queue.put(line)
                influx_queue.put(line)
                # ff.write(line)
                line = ""
            
            except i2c.I2cNackError:
                pass
            
            time.sleep(0.075)
        
    except KeyboardInterrupt:
        runflag = False
        
    print('Done with current logging')

if __name__ == "__main__":
    main()
