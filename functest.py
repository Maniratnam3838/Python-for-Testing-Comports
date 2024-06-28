import sys
import serial
import re
import time
import datetime
import os

class Tracker:
    def __init__(self, com_num, bd_rate, logfile, resultfile):
        self.com_num = com_num
        self.bd_rate = bd_rate
        self.logfile = logfile
        self.resultfile = resultfile
        self.testNumber = 1
        self.hCom = None
        self.exp = None
        self.devid = None
        self.iccid = None
        self.gpsnmea = False
        self.gpsfix = False
        self.gsmuart = False
        self.gsm_Registration = False
        self.sim = False
        self.GPRS = False
        self.servercon = False
        self.Acc = False
        self.can = False
        self.factoryset = False
        self.factoryread = False
        self.ConfigRead = False
        self.testfailed = False
        self.logfp = open(logfile, 'a')
        self.fp = open(resultfile, 'a')

    def log(self, message, bprint=True):
        if bprint:
            print(message)
        self.logfp.write(message + '\n')
        self.logfp.flush()
        os.fsync(self.logfp)

    def write_to_com(self, cmd):
        try:
            self.hCom.write(cmd.encode())
            return 0
        except:
            self.log('Serial write exception\n', 1)
            return -1

    def read_from_com(self, eol='\n'):
        response = ''
        leol = len(eol)
        while True:
            ch = self.hCom.read(1).decode()
            response += ch
            if response[-leol:] == eol:
                return response
            now = datetime.datetime.now()
            if now > self.exp:
                return -1

    def set_cmd_timeout(self, timeout):
        now = datetime.datetime.now()
        self.exp = now + datetime.timedelta(seconds=timeout)

    def update_result(self):
        if self.devid:
            self.fp.write(f" {self.devid}")
        else:
            self.fp.write(' No DEVID')
        
        if self.iccid:
            self.fp.write(f' {self.iccid}')
        else:
            self.fp.write(' No ICCID')
            
        self.fp.write(' OK' if self.gpsnmea else ' Not OK')
        self.fp.write(' OK' if self.gsmuart else ' Not OK')
        self.fp.write(' OK' if self.gsm_Registration else ' Not OK')
        self.fp.write(' OK' if self.sim else ' Not OK')
        self.fp.write(' OK' if self.GPRS else ' Not OK')
        self.fp.write(' OK' if self.servercon else ' Not OK')
        self.fp.write(' OK' if self.Acc else ' Not OK')
        self.fp.write(' OK' if self.can else ' Not OK')
        self.fp.write(' OK' if self.factoryset else ' Not OK')
        self.fp.write(' OK' if self.factoryread else ' Not OK')


    def run_test(self):
        self.log(f'Trying to open comport {self.com_num}\n', 1)
        self.log(f'Trying to open baudrate {self.bd_rate}\n', 1)
        try:
            self.hCom = serial.Serial(f'COM{self.com_num}', self.bd_rate, timeout=1)
            self.hCom.writeTimeout = 1
        except:
            self.log(f'Error opening com port {self.com_num}', 1)
            return

        self.fp.write(
            '\nSl. No.,IMEI,ICCID,NMEA,GPS FIX,GSM UART,Registration,SIM,GPRS,Server Connection,Accelerometer,CAN,FACTORY SET,FACTORY READ,Test Result\n'
        )

        while True:
            self.log(f'Running test {self.testNumber}\n', 1)
            self.init_test()
            self.single_test()
            self.fp.write(f' {self.testNumber},')
            if not self.ConfigRead or not self.iccid:
                self.testfailed = True

            if not self.testfailed:
                self.update_result()
                self.fp.write('PASS\n')
                self.log(
                    f'*******************\nTest completed successfully on com{self.com_num}\n*******************\n',1
                )
            else:
                self.update_result()
                self.fp.write('FAIL\n')
                self.log(
                    f'*******************\nTest FAILED on com{self.com_num}\n*******************\n',1
                )
            self.fp.flush()
            os.fsync(self.fp)
            self.init_test()
            self.logfp.flush()
            os.fsync(self.logfp)

            nexttest = input('Run next test again(y) or Stop the test(n)?:')
            if nexttest.lower() == 'n':
                break
            else:
                self.testNumber += 1
                
    #def result_file(self):
     #   if(resultfile == True):
      #      resultfile += 1
       # self.result_file()
            

    def init_test(self):
        self.hCom.flushInput()
        self.testfailed = False
        self.csqfound = False
        self.gpsok = False
        self.nmeadelay = False
        self.iook = False
        self.copsattempts = False
        self.imeiattempts = False
        self.flashok = True
        self.nofix = 'auto'
        self.chkrestart = False
        self.factoryset = False
        self.factoryread = False
        self.ConfigRead = False
        self.devid = False
        self.iccid = False

    def single_test(self):
        self.csqfound = False
        self.simok = False
        self.testfailed = False

        self.send_comands([
            ('SET FACTORY DEFAULT\r\n', 3),
            ('SET CANP 3\r\n', 3),
            ('SET SMO DISABLE\r\n', 3),
            ('START BIT\r\n', 120)
        ])

        while True:
            line = self.read_from_com()
            if re.search('BEGIN THE TEST', line):
                self.log("BIT Started", 1)
                break
        self.test_results()

    def send_comands(self, comands):
        for cmd, timeout in comands:
            self.set_cmd_timeout(timeout)
            self.hCom.flushInput()
            self.write_to_com(cmd)
            time.sleep(1)

    def test_results(self):
        while True:
            line = self.read_from_com()
            self.log(line, 0)

            if re.search('OK', line):
                self.final_inputs(line, True)
            elif re.search('FAIL', line):
                self.final_inputs(line, False)
            elif re.search('ID', line) and not self.ConfigRead:
                self.devid = self.pre_fix(line, 'ID')
                self.ConfigRead = True
            elif re.search('ICCID', line):
                self.iccid = self.pre_fix(line, 'ICCID')
                self.log('Configuration Set OK', 1)
            elif re.search('END OF TEST', line):
                self.log('END OF TEST', 1)
                break

    def final_inputs(self, line, Good):
        if re.search('0 ', line):
            self.gpsnmea = Good
            self.log('NMEA ' + ('OK' if Good else 'FAIL'), 1)
        elif re.search('1 ', line):
            self.gpsfix = Good
            self.log('GPS FIX ' + ('OK' if Good else 'FAIL'), 1)
        elif re.search('2 ', line):
            self.gsmuart = Good
            self.log('GSM UART ' + ('OK' if Good else 'FAIL'), 1)
        elif re.search('3 ', line):
            self.gsm_Registration = Good
            self.log('GSM Registration ' + ('OK' if Good else 'FAIL'), 1)
        elif re.search('4 ', line):
            self.sim = Good
            self.log('SIM ' + ('OK' if Good else 'FAIL'), 1)
        elif re.search('5 ', line):
            self.GPRS = Good
            self.log('GPRS ' + ('OK' if Good else 'FAIL'), 1)
        elif re.search('6 ', line):
            self.servercon = Good
            self.log('SERVER CONNECTION ' + ('OK' if Good else 'FAIL'), 1)
        elif re.search('7 ', line):
            self.Acc = Good
            self.log('Accelero ' + ('OK' if Good else 'FAIL'), 1)
        elif re.search('9 ', line):
            self.can = Good
            self.log('CAN ' + ('OK' if Good else 'FAIL'), 1)
        elif re.search('10 ', line):
            self.factoryset = Good
            self.log('Factory Set ' + ('OK' if Good else 'FAIL'), 1)
        elif re.search('11 ', line):
            self.factoryread = Good
            self.log('Factory Read ' + ('OK' if Good else 'FAIL'), 1)
        if not Good:
            self.testfailed = True


    def pre_fix(self, line, prefix):
        index = line.find(prefix)
        return line[index + len(prefix):]

def main():
    tracking = Tracker(
        com_num= input("Enter a comport number: "),
        bd_rate= input("Enter a Baudrate: "),
        logfile='tracker.log',
        resultfile='results.csv'
    )
    tracking.run_test()

if __name__ == '__main__':
    main()
