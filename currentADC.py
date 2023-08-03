from pyftdi import i2c
import datetime

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
            # print(f'Channel Number {chanNum:02d}: ', end='')

            conv = (int(xx) & 0x0F) << 8
            conv = conv | (int(resArray[idx+1]))
            
            self.convResults[idx+1] = conv


if __name__ == "__main__":
    import time
    # import json

    line = ""
    current = iadc()
    # for xx in range(10):


    with open('current_log_data.txt', 'w') as ff:
        try: 
            while True:
                try:
                    current.readAllChannels()
                    print(current.convResults)
                    
                    for val in current.convResults:
                        line += f'{current.convResults[val]}, '

                    line += '\n'
                    ff.write(line)
                    line = ""
                
                except i2c.I2cNackError:
                    pass
                
                time.sleep(0.075)
        
        except KeyboardInterrupt:
            print("done")
