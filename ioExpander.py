from pyftdi import i2c
import time
import argparse

class ioswitches:
    devname = 'ftdi://ftdi:232h:1/1'
    devI2CAddress = 0x41

    # tracking the value of the output register
    outputRegValue = 0x00

    # register addresses
    configReg  = 0x03
    outputPort = 0x01

    # Pin connection Definitions
    mc2switch = 0x01
    mc1switch = 0x02
    obswitch = 0x04
    fcswitch = 0x08

    mc1Mask = 0x0D
    mc2Mask = 0x0E
    obMask  = 0x0B
    fcMask  = 0x07

    def __init__(self):

        iic = i2c.I2cController()
        iic.configure('ftdi://ftdi:232h:1/1')
        self.io = iic.get_port(self.devI2CAddress)
        self.io.write_to(self.configReg, b'\xF0')
        self.readOutReg()

    def readOutReg(self):
        self.io.exchange([self.outputPort], 1)
        self.outputRegValue = int.from_bytes(self.io.read(1))
        return self.outputRegValue

    def turnOffChannel(self, channelNum):
        currentOut = self.readOutReg()

        mask = 0x0F
        if channelNum == self.mc2switch:
            mask = self.mc2Mask
        elif channelNum == self.mc1switch:
            mask = self.mc1Mask
        elif channelNum == self.obswitch:
            mask = self.obMask
        elif channelNum == self.fcswitch:
            mask = self.fcMask
        else:
            raise ValueError

        currentOut = currentOut & mask
        self.io.write_to(self.outputPort, currentOut.to_bytes(1, 'big'))
    
    def turnONChannel(self, channelNum):
        currentOut = self.readOutReg()

        mask = 0x0F
        if channelNum == self.mc2switch:
            mask = self.mc2switch
        elif channelNum == self.mc1switch:
            mask = self.mc1switch
        elif channelNum == self.obswitch:
            mask = self.obswitch
        elif channelNum == self.fcswitch:
            mask = self.fcswitch
        else:
            raise ValueError

        currentOut = currentOut | mask
        self.io.write_to(self.outputPort, currentOut.to_bytes(1, 'big'))
    

if __name__ == "__main__":
    # set up arguments 
    # 1st arg should be which device
    # 2nd arg should be on or off
    parser = argparse.ArgumentParser(description="Turn ebox things on or off")
    parser.add_argument("deviceName", choices=["mc1","mc2","ob", "fc"], help="Name of device to turn off. One of mc1, mc2, ob or fc.")
    parser.add_argument("action", choices=["on", "off"], help="Tell whether to turn given device on or off.")
    args = parser.parse_args()   
    
    if args.action:
        io = ioswitches()
        if args.action == "on":
            if args.deviceName:
                if args.deviceName == "mc1":
                    io.turnONChannel(io.mc1switch)
                    print(io.readOutReg()& 0x0F)
                elif args.deviceName == "mc2":
                    io.turnONChannel(io.mc2switch)
                    print(io.readOutReg()& 0x0F)
                elif args.deviceName == "ob":
                    io.turnONChannel(io.obswitch)
                    print(io.readOutReg()& 0x0F)
                elif args.deviceName == "fc":
                    io.turnONChannel(io.fcswitch)
                    print(io.readOutReg()& 0x0F)
                else:
                    print("Device Name not know")
            else:
                print("Error, no device name given")
        elif args.action == "off":
            if args.deviceName:
                if args.deviceName == "mc1":
                    io.turnOFFChannel(io.mc1switch)
                    print(io.readOutReg()& 0x0F)
                elif args.deviceName == "mc2":
                    io.turnOFFChannel(io.mc2switch)
                    print(io.readOutReg()& 0x0F)
                elif args.deviceName == "ob":
                    io.turnOFFChannel(io.obswitch)
                    print(io.readOutReg()& 0x0F)
                elif args.deviceName == "fc":
                    io.turnOFFChannel(io.fcswitch)
                    print(io.readOutReg()& 0x0F)
                else:
                    print("Device Name not know")
            else:
                print("Error, no device name given")
        else:
            print("Unkown action")
    else:
        print("Error, no given action")
        
    # io = ioswitches()
    # print(io.readOutReg() & 0x0F)
    # io.turnOffChannel(io.mc1switch)
    # print(io.readOutReg()& 0x0F)

    # time.sleep(2)
    # io.turnONChannel(io.mc1switch)
    # print(io.readOutReg()& 0x0F)

    print('Done')
