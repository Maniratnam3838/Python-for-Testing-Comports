import time
import tkinter as tk
from tkinter import ttk, messagebox
import serial
import datetime
from threading import Thread
from tkinter import filedialog as fd
import serial.tools
import serial.tools.list_ports 

comPorts = []

def updatePassFail(textVal, passVal):
    if passVal == True:
        app.updateCount(textVal)
    else:
        app.updateCount1(textVal)

def totalCount(countVal):  
  app.totalCount(countVal)

def upDateCom():
    global comPorts
    comPorts.clear()
    totPorts = serial.tools.list_ports.comports()
    for i in range(len(totPorts)):
        comPorts.append(totPorts[i].name)
    print(comPorts)
    

class Tracker:
    global comPorts
    totalCount = 0
    passCount = 0
    failCount = 0
    def __init__(self, parent, frame_id):
        self.parent = parent
        self.frame_id = frame_id  # Identifier for the frame

        # Create a Frame within the parent
        self.frame = ttk.Frame(parent, padding="10 10 10 10")
        self.frame.pack(fill=tk.BOTH, expand=True)

        # Variables
        self.com_num_var = tk.StringVar()
        self.bd_rate_var = tk.StringVar()
        #CHECK Button
        self.run_test_var = tk.BooleanVar()
        self.run_test_checkbutton = ttk.Checkbutton(self.frame, text=  frame_id, variable=self.run_test_var)
        self.run_test_checkbutton.grid(row=0, columnspan=2, pady=10)
    
        # Widgets
        ttk.Label(self.frame, text=f"COM Port Number : ").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.com_num_combobox = ttk.Combobox(self.frame, textvariable=self.com_num_var)
        self.com_num_combobox['values'] = ['Select'] + [f'{i}' for i in comPorts]
        self.com_num_combobox.grid(row=1, column=1, padx=5, pady=5)
        self.com_num_combobox.current(0)
        self.com_num_combobox.bind('<<ComboboxSelected>>', self.update_com_baud_labels)

        ttk.Label(self.frame, text=f"Baud Rate : ").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.bd_rate_combobox = ttk.Combobox(self.frame, textvariable=self.bd_rate_var)
        self.bd_rate_combobox['values'] =['Select'] + ['4800', '9600','14400', '19200', '38400', '57600', '115200','230400','460800','921600']
        self.bd_rate_combobox.grid(row=2, column=1, padx=5, pady=5)
        self.bd_rate_combobox.current(0)
        self.bd_rate_combobox.bind('<<ComboboxSelected>>', self.update_com_baud_labels)

        connect_button = ttk.Button(self.frame, text="Connect", command=self.connect_to_device)
        connect_button.grid(row=3, column=0, columnspan=2, pady=10)

        ttk.Separator(self.frame, orient=tk.HORIZONTAL).grid(row=4, column=0, columnspan=2, pady=10, sticky="ew")
        ttk.Separator(self.frame, orient=tk.VERTICAL).grid(row=0, column=3, rowspan=35, padx=10, sticky="NS")
        
        self.left_labels = {}
        left_label_texts = ["COM", "Baudrate", "Hardware Version", "Software Version", "ICCID", "IMEI"]
        for i, label_text in enumerate(left_label_texts):
            ttk.Label(self.frame, text=label_text + ":").grid(row=i + 5, column=0, padx=2, pady=2, sticky=tk.W)
            value_label = ttk.Label(self.frame, text=" ")
            value_label.grid(row=i + 5, column=1, padx=2, pady=2, sticky=tk.W)
            self.left_labels[label_text] = value_label

        self.update_com_baud_labels()

        # Right-side Widgets
        self.right_labels = {}
        right_label_texts = ["GPS NMEA", "GPS FIX", "GSM UART", "GSM Registration", "SIM", "GPRS", "Server Connection",
                             "Accelerometer", "CAN", "Factory Set", "Factory Read"]
        for i, label_text in enumerate(right_label_texts):
            ttk.Label(self.frame, text=label_text).grid(column=0, row=i + len(left_label_texts) + 11, padx=2, pady=2, sticky=tk.W)
            value_label = ttk.Label(self.frame, text=" ")
            value_label.grid(column=1, row=i + len(left_label_texts) + 12, padx=2, pady=2, sticky=tk.W)
            self.right_labels[label_text] = value_label

        self.bulbs = {}
        for idx, label in enumerate(right_label_texts):
            canvas = tk.Canvas(self.frame, width=20, height=20)
            canvas.grid(column=1, row=idx + len(left_label_texts) + 11, padx=(10, 5))
            bulb_id = canvas.create_oval(5, 5, 15, 15, fill="gray")
            self.bulbs[label] = (canvas, bulb_id)

        self.result_label = ttk.Label(self.frame, text="Test Result: ")
        self.result_label.grid(row=len(right_label_texts) + len(left_label_texts) + 11, columnspan=2, pady=10)

        self.serial_port = None
        self.logfile = f"tklog_{frame_id}.txt"
        self.resultfile = f"tkresult_{frame_id}.csv"
        self.logfp = open(self.logfile, 'a')
        self.fp = open(self.resultfile, 'a')

        self.status_dict = {
                'GPS NMEA': False,
                'GPS FIX': False,
                'GSM UART': False,
                'GSM Registration': False,
                'SIM': False,
                'GPRS': False,
                'Server Connection': False,
                'Accelerometer': False,
                'CAN': False,
                'Factory Set': False,
                'Factory Read': False
            }
        self.reset_attributes()
        
    def reset_attributes(self):
        self.hCom = None
        self.exp = None
        self.devid = None
        self.iccid = None
        self.imei = None
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

    def update_com_baud_labels(self, event=None):
        self.left_labels["COM"].config(text=self.com_num_var.get())
        self.left_labels["Baudrate"].config(text=self.bd_rate_var.get())
        
    def toggle_enabled(self):
        if self.checked_var.get():
            self.log(f"Tracker {self.frame_id} enabled\n")
            self.connect_to_device()
        else:
            self.log(f"Tracker {self.frame_id} disabled\n")
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()


    def connect_to_device(self):
        com_num = self.com_num_var.get()
        bd_rate = self.bd_rate_var.get()

        if com_num == 'Select' or not bd_rate:
            messagebox.showerror("Error", "COM port number and baud rate must be provided.")
            return

        try:
            self.serial_port = serial.Serial()
            self.serial_port.port = com_num
            self.serial_port.baudrate = int(bd_rate)
            self.serial_port.timeout = 1
            self.serial_port.open()

            self.update_com_baud_labels()  # Update labels with selected values

            messagebox.showinfo("Connected", f"Successfully connected to {com_num} with baud rate {bd_rate}.")

            # Fetch device data on successful connection
            self.fetch_device_data()

        except Exception as e:
            self.log(f"Error opening COM port {com_num} with baud rate {bd_rate}: {e}\n", 1)
            messagebox.showerror("Error", f"Error opening COM port {com_num}: {e}")

    def fetch_device_data(self):
        try:
            if not self.serial_port.is_open:
                self.log(f"Opening COM port {self.serial_port.port} with baud rate {self.serial_port.baudrate}\n", 1)
                self.serial_port.open()

            # Clear the serial buffer
            self.serial_port.flushInput()

            # Command to get software and hardware versions
            self.serial_port.write(b'SHOW CONFIG\n')
            time.sleep(1)
            response = self.serial_port.read_all().decode('utf-8')
            #self.log(f"Response from SHOW CONFIG command: {response}\n", 1)

            # Parse software and hardware version
            for line in response.splitlines():
                if 'SV:' in line:
                    self.left_labels["Software Version"].config(text=line.split(':')[1].strip())
                elif 'HV:' in line:
                    self.left_labels["Hardware Version"].config(text=line.split(':')[1].strip())

            # Command to get ICCID and IMEI
            self.serial_port.write(b'SHOW GSM\n')
            time.sleep(1)
            response = self.serial_port.read_all().decode('utf-8')
            #self.log(f"Response from SHOW GSM command: {response}\n", 1)

            # Parse ICCID and IMEI
            for line in response.splitlines():
                if 'IMEI:' in line:
                    self.left_labels["IMEI"].config(text=line.split(':')[1].split(',')[0].strip())
                    self.left_labels["ICCID"].config(text=line.split(':')[2].split(',')[0].strip())

        except Exception as e:
            self.log(f'Error fetching device data: {e}\n')

    def update_gui(self):
        self.root.after(5000, self.update_gui)

    def update_bulbs(self, status_dict):
        for status, value in status_dict.items():
            #print(status, value)
            canvas, bulb_id = self.bulbs[status]
            color = "green" if value else "red"
            canvas.itemconfig(bulb_id, fill=color)

    def log(self, message, bprint=False):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{now}] {message}"
        self.logfp.write(log_message)
        self.fp.write(log_message)
        if bprint:
            print(log_message)
    
    def run_test(self):
        if self.run_test_var.get() == True:
            print("****")
            self.reset_attributes()
            self.single_test()
            # Determine overall test resultl
            if all([self.gpsnmea, self.gpsfix, self.gsmuart, self.gsm_Registration, self.sim,
                    self.GPRS, self.servercon, self.Acc, self.can, self.factoryset, self.factoryread]):
                self.result_label.config(text="Test Result: PASS", foreground="green")
                Tracker.passCount += 1
                passVal = "Pass Count: "+ str(Tracker.passCount)
                updatePassFail(passVal, True)
            else:
                self.result_label.config(text="Test Result: FAIL", foreground="red")
                Tracker.failCount += 1
                failVal = "Fail Count: "+ str(Tracker.failCount)
                updatePassFail(failVal, False)
            #self.confirm_retry_test()
            totVal = "Total Count: "+str(Tracker.passCount+Tracker.failCount)
            totalCount(totVal)
        else:
            self.result_label.config(text="Test Result: ", foreground="black")
            
    
    def confirm_retry_test(self):
        # Ask user for confirmation before retrying the test
        #answer = messagebox.askyesno("Retry Test", "Do you want to retry the test?")
        #if answer:
            self.status_dict['GPS NMEA'] = False
            self.status_dict['GPS FIX'] = False
            self.status_dict['GSM UART'] = False
            self.status_dict['GSM Registration'] = False
            self.status_dict['SIM'] = False
            self.status_dict['GPRS'] = False
            self.status_dict['Server Connection'] = False
            self.status_dict['Accelerometer'] = False
            self.status_dict['CAN'] = False
            self.status_dict['Factory Set'] = False
            self.status_dict['Factory Read'] = False
            
            self.update_bulbs(self.status_dict)
            self.run_test()  # If the user clicks 'Yes', run the test again

    def final_inputs(self, line):
        #for line in response.splitlines():#data_lines
        #print("***",line)
        if '10' in line:
            self.factoryset = True
            self.log('Factory Set OK', 1)
        elif '11' in line:
            self.factoryread = True
            self.log('Factory Read OK', 1)
        elif '0' in line:
            self.gpsnmea = True
            self.log('NMEA OK', 1)
        elif '1' in line:
            self.gpsfix = True
            self.log('GPS FIX OK', 1)
        elif '2' in line:
            self.gsmuart = True
            self.log('GSM UART OK', 1)
        elif '3' in line:
            self.gsm_Registration = True
            self.log('GSM Registration OK', 1)
        elif '4' in line:
            self.sim = True
            self.log('SIM OK', 1)
        elif '5' in line:
            self.GPRS = True
            self.log('GPRS OK', 1)
        elif '6' in line:
            self.servercon = True
            self.log('Server Connection OK', 1)
        elif '7' in line:
            self.Acc = True
            self.log('Accelerometer OK', 1)
        elif '9' in line:
            self.can = True
            self.log('CAN OK', 1)
        

    def single_test(self):
        try:
            if not self.serial_port.is_open:
                self.log(f"Opening COM port {self.serial_port.port} with baud rate {self.serial_port.baudrate}\n", 1)
                self.serial_port.open()

            self.serial_port.write(b'START BIT\n')
            time.sleep(1)
            while True:
                line = self.serial_port.readline().decode('utf-8')
                if "OK" in line:
                    self.final_inputs(line)
                elif 'END OF TEST' in line:
                    break
            #response = self.serial_port.readline().decode('utf-8')
            #self.log(f"Response: {response}\n", 1)
            #data_lines = response.splitlines()

            # Reset attributes
            #self.reset_attributes()

            # Update the status dictionary
            self.status_dict['GPS NMEA'] = self.gpsnmea
            self.status_dict['GPS FIX'] = self.gpsfix
            self.status_dict['GSM UART'] = self.gsmuart
            self.status_dict['GSM Registration'] = self.gsm_Registration
            self.status_dict['SIM'] = self.sim
            self.status_dict['GPRS'] = self.GPRS
            self.status_dict['Server Connection'] = self.servercon
            self.status_dict['Accelerometer'] = self.Acc
            self.status_dict['CAN'] = self.can
            self.status_dict['Factory Set'] = self.factoryset
            self.status_dict['Factory Read'] = self.factoryread
            ######
            self.log(f"NMEA: {self.gpsnmea}, GPS FIX: {self.gpsfix}, GSM UART: {self.gsmuart}, "
                     f"Registration: {self.gsm_Registration}, SIM: {self.sim}, GPRS: {self.GPRS}, "
                     f"Server Connection: {self.servercon}, Accelerometer: {self.Acc}, CAN: {self.can}, "
                     f"Factory Set: {self.factoryset}, Factory Read: {self.factoryread}\n", 1)

            self.update_bulbs(self.status_dict)  # Call update_bulbs() after tests

        except Exception as e:
            self.log(f'Error during single test: {e}\n')
            
    def refresh_all(self):       
        if comPorts is not None:
            self.com_num_combobox.config(values=comPorts)
            
    def close(self):
        #self.log("Closing application.\n", 1)
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.logfp.close()
        self.fp.close()
        
class Application:
    global comPorts
    def __init__(self, root):
        self.root = root
        self.root.title("Four Tracker Test")
        #self.root.geometry('1700x1200')
        
        self.frames  = ttk.Frame(self.root)
        self.frames.pack(side='top')
        
        quit_button = ttk.Button(self.frames, text="Quit", command= self.quit_all) #command=self.parent.quit)
        #quit_button.grid(column=1, row= 32, pady=5)
        quit_button.grid(column=4, row = 1, ipadx=5, ipady=5)
        
        stop_button = ttk.Button(self.frames, text='Stop', command= self.stop_all)
        stop_button.grid(column=3, row =1, ipadx=5, ipady=5)
        
        start_button = ttk.Button(self.frames, text="Start",command=self.start_all) #command=self.run_test)
        start_button.grid(column=2, row = 1, ipadx=5, ipady=5)
        
        refresh_Button = ttk.Button(self.frames, text="Refresh", command=self.refreshAll)
        refresh_Button.grid(column=1, row = 1, ipadx=5, ipady=5)

        
        self.trakAll = []
        
        self.Fullcount = ttk.Label(self.root,text='Total Count: 0')
        self.Fullcount.pack(side='bottom', anchor='w')
        
        self.count = ttk.Label(self.root, text='Pass Count: 0')
        self.count.pack(side='bottom', anchor='w')
        
        self.count1 = ttk.Label(self.root, text='Fail Count: 0')
        self.count1.pack(side='bottom', anchor='w')
        
        self.path = ttk.Label(self.root, text = "D:\\")
        self.path.pack(side='bottom',anchor='w')
        
        open_button = ttk.Button(self.root, text='Open a File', command=self.open_text_file)    
        open_button.pack(side='bottom', anchor='w')
        
        self.date_ll = ttk.Label(self.root, text= datetime.datetime.now().strftime("%Y-%m-%d"))
        self.date_ll.pack(side='top', anchor='w')
        
        upDateCom()
        
        # Create PanedWindow to hold two main frames
        self.paned_window = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # Create two Tracker instances in separate frames
        self.first_frame = ttk.Frame(self.paned_window)
        self.second_frame = ttk.Frame(self.paned_window)
        self.third_frame = ttk.Frame(self.paned_window)
        self.fourth_frame = ttk.Frame(self.paned_window)
        
        self.paned_window.add(self.first_frame, weight=1)
        self.paned_window.add(self.second_frame, weight=1)
        self.paned_window.add(self.third_frame, weight=1)
        self.paned_window.add(self.fourth_frame, weight=1)

        self.tracker1 = Tracker(self.first_frame, frame_id="Tracker 1")
        self.tracker2 = Tracker(self.second_frame, frame_id="Tracker 2")
        self.tracker3 = Tracker(self.third_frame, frame_id="Tracker 3")
        self.tracker4 = Tracker(self.fourth_frame, frame_id="Tracker 4")
        
        self.trakAll.append(self.tracker1)
        self.trakAll.append(self.tracker2)
        self.trakAll.append(self.tracker3)
        self.trakAll.append(self.tracker4)
        
    
    def open_text_file(self): 
        filetypes = (('text files', '*.txt'), ('All files', '*.*'))
        filePath = fd.askopenfile(filetypes=filetypes, initialdir="/")
        self.root.update()
        print(filePath)
        if filePath != None:
            self.path.config(text=filePath.name)
        
    def start_all(self):
        print("starting...")
        for tracker in self.trakAll:
            thId = Thread(target=tracker.run_test())
            thId.start()
            thId.join()
    
    def stop_all(self):
        print('stoping...')
        for tracker in self.trakAll:
            tracker.refresh_all()
            tracker.confirm_retry_test()
    
    def refreshAll(self):import random
import time
import tkinter as tk
from tkinter import ttk, messagebox
import serial
import datetime
import threading
from tkinter import filedialog as fd
import serial.tools
import serial.tools.list_ports 

comPorts = []
baudrates = '115200'

def updateWindow():
    root.update()

def updatePassFail(textVal, passVal):
    if passVal == True:
        app.updateCount(textVal)
    else:
        app.updateCount1(textVal)

def totalCount(countVal):  
  app.totalCount(countVal)

def upDateCom():
    global comPorts
    comPorts.clear()
    totPorts = serial.tools.list_ports.comports()
    for i in range(len(totPorts)):
        comPorts.append(totPorts[i].name)
    print(comPorts)
    

class Tracker:
    global comPorts
    global baudrates
    totalCount = 0
    passCount = 0
    failCount = 0
    def __init__(self, parent, frame_id):
        self.parent = parent
        self.frame_id = frame_id  # Identifier for the frame

        # Create a Frame within the parent
        self.frame = ttk.Frame(parent, padding="10 10 10 10")
        self.frame.pack(fill=tk.BOTH, expand=True)

        # Variables
        self.com_num_var = tk.StringVar()
        self.running = True
        #self.bd_rate_var = tk.StringVar()
        #CHECK Button
        self.run_test_var = tk.BooleanVar()
        self.run_test_checkbutton = ttk.Checkbutton(self.frame, text=  frame_id, variable=self.run_test_var)
        self.run_test_checkbutton.grid(row=0, columnspan=2, pady=10)
        
    
        # Widgets
        ttk.Label(self.frame, text=f"COM Port Number : ").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.com_num_combobox = ttk.Combobox(self.frame, textvariable=self.com_num_var)
        self.com_num_combobox['values'] = ['Select'] + [f'{i}' for i in comPorts]
        self.com_num_combobox.grid(row=1, column=1, padx=5, pady=5)
        self.com_num_combobox.current(0)
        self.com_num_combobox.bind('<<ComboboxSelected>>', self.update_com_baud_labels)

        # ttk.Label(self.frame, text=f"Baud Rate : ").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        # self.bd_rate_combobox = ttk.Combobox(self.frame, textvariable=self.bd_rate_var)
        # #self.bd_rate_combobox['values'] =['Select'] + ['4800', '9600','14400', '19200', '38400', '57600', '115200','230400','460800','921600']
        # self.bd_rate_combobox['values'] =['Select'] + ['9600','115200']
        # self.bd_rate_combobox.grid(row=2, column=1, padx=5, pady=5)
        # self.bd_rate_combobox.current(0)
        # self.bd_rate_combobox.bind('<<ComboboxSelected>>', self.update_com_baud_labels)

        # connect_button = ttk.Button(self.frame, text="Connect", command=self.connect_to_device)
        # connect_button.grid(row=3, column=0, columnspan=2, pady=10)

        ttk.Separator(self.frame, orient=tk.HORIZONTAL).grid(row=4, column=0, columnspan=2, pady=10, sticky="ew")
        ttk.Separator(self.frame, orient=tk.VERTICAL).grid(row=0, column=3, rowspan=35, padx=10, sticky="NS")
        
        self.left_labels = {}
        left_label_texts = ["COM", "Baudrate", "Hardware Version", "Software Version", "ICCID", "IMEI"]
        for i, label_text in enumerate(left_label_texts):
            ttk.Label(self.frame, text=label_text + ":").grid(row=i + 5, column=0, padx=5, pady=5, sticky=tk.W)
            value_label = ttk.Label(self.frame, text=" ")
            value_label.grid(row=i + 5, column=1, padx=2, pady=2, sticky=tk.W)
            self.left_labels[label_text] = value_label
        
        self.canvas_com = tk.Canvas(self.frame, width=20, height=20)
        self.canvas_com.grid(column=1, row =5, padx=(10, 5))
        self.status_ind = self.canvas_com.create_rectangle(5, 5, 15, 15)

        #self.update_com_baud_labels()

        # Right-side Widgets
        self.right_labels = {}
        right_label_texts = ["GPS NMEA", "GPS FIX", "GSM UART", "GSM Registration", "SIM", "GPRS", "Server Connection",
                             "Accelerometer", "CAN", "Factory Set", "Factory Read"]
        for i, label_text in enumerate(right_label_texts):
            ttk.Label(self.frame, text=label_text).grid(column=0, row=i + len(left_label_texts) + 11, padx=5, pady=5, sticky=tk.W)
            value_label = ttk.Label(self.frame, text=" ")
            value_label.grid(column=1, row=i + len(left_label_texts) + 12, padx=2, pady=2, sticky=tk.W)
            self.right_labels[label_text] = value_label

        self.bulbs = {}
        for idx, label in enumerate(right_label_texts):
            canvas = tk.Canvas(self.frame, width=20, height=20)
            canvas.grid(column=1, row=idx + len(left_label_texts) + 11, padx=(10, 5))
            bulb_id = canvas.create_oval(5, 5, 20, 20)
            self.bulbs[label] = (canvas, bulb_id)

        self.result_label = ttk.Label(self.frame, text="Test Result: ")
        self.result_label.grid(row=len(right_label_texts) + len(left_label_texts) + 11, columnspan=2, pady=10)

        self.serial_port = None
        self.logfile = f"tk4log.txt"
        self.resultfile = f"tk4result.csv"
        self.logfp = open(self.logfile, 'a')
        self.fp = open(self.resultfile, 'a')
        pos = self.fp.tell()
        if pos == 0:
            self.report("gpsnmea,gpsfix,gsmuart,gsm_Registration,sim,GPRS,servercon,Acc,can,factoryset,factoryread,testfailed",0)
        
        self.status_dict = {
                'GPS NMEA': 0,
                'GPS FIX': 0,
                'GSM UART': 0,
                'GSM Registration': 0,
                'SIM': 0,
                'GPRS': 0,
                'Server Connection': 0,
                'Accelerometer': 0,
                'CAN': 0,
                'Factory Set': 0,
                'Factory Read': 0
            }
        self.reset_attributes()
        
    def reset_attributes(self):
        self.hCom = None
        self.exp = None
        self.devid = None
        self.iccid = None
        self.imei = None
        self.gpsnmea = "NOK"
        self.gpsfix = "NOK"
        self.gsmuart = "NOK"
        self.gsm_Registration ="NOK"
        self.sim ="NOK"
        self.GPRS = "NOK"
        self.servercon = "NOK"
        self.Acc = "NOK"
        self.can = "NOK"
        self.factoryset = "NOK"
        self.factoryread = "NOK"
        self.ConfigRead = False
        self.testfailed = False

    def update_com_baud_labels(self, event=None):
        self.left_labels["COM"].config(text=self.com_num_var.get())
        self.left_labels["Baudrate"].config(text=baudrates)
        
    # def toggle_enabled(self):
    #     if self.checked_var.get():
    #         self.log(f"Tracker {self.frame_id} enabled\n")
    #         self.connect_to_device()
    #     else:
    #         self.log(f"Tracker {self.frame_id} disabled\n")
    #         if self.serial_port and self.serial_port.is_open:
    #             self.serial_port.close()


    def connect_to_device(self):
        if self.run_test_var.get() == True:
            self.com_num = self.com_num_var.get()
            bd_rate = baudrates
            
            self.left_labels["Baudrate"].config(text=baudrates)

            if self.com_num == 'Select' or not bd_rate:
                # messagebox.showerror("Error", "COM port number and baud rate must be provided.")
                 return

            try:
                self.serial_port = serial.Serial()
                self.serial_port.port = self.com_num
                self.serial_port.baudrate = int(bd_rate)
                self.serial_port.timeout = 1
                self.serial_port.open()

                self.update_com_baud_labels()  # Update labels with selected values

                #messagebox.showinfo("Connected", f"Successfully connected to {com_num} with baud rate {bd_rate}.")
                self.canvas_com.itemconfig(self.status_ind,fill='green')
                    
            # Fetch device data on successful connection
            #self.fetch_device_data()

            except Exception as e:
                self.log(f"Error opening COM port {self.com_num} with baud rate {bd_rate}: {e}\n", 1)
                # messagebox.showerror("Error", f"Error opening COM port {com_num}: {e}")
                self.canvas_com.itemconfig(self.status_ind,fill='red')

    def fetch_device_data(self):
        try:
            if not self.serial_port.is_open:
                self.log(f"Opening COM port {self.serial_port.port} with baud rate {self.serial_port.baudrate}\n", 1)
                self.serial_port.open()

            # Clear the serial buffer
            self.serial_port.flushInput()

            # Command to get software and hardware versions
            self.serial_port.write(b'SHOW CONFIG\n')
            time.sleep(1)
            response = self.serial_port.read_all().decode('utf-8')
            #self.log(f"Response from SHOW CONFIG command: {response}\n", 1)

            # Parse software and hardware version
            for line in response.splitlines():
                for text1 in line.split(','):   
                    print(text1)
                    if 'SV:' in text1:
                        self.left_labels["Software Version"].config(text=text1.split(':')[1].strip())
                    elif 'HV:' in text1:
                        self.left_labels["Hardware Version"].config(text=text1.split(':')[1].strip())
                    elif 'ID:' in text1:
                        self.left_labels["IMEI"].config(text=text1.split(':')[1].strip())

            # Command to get ICCID and IMEI
            self.serial_port.write(b'SHOW GSM\n')
            time.sleep(1)
            response = self.serial_port.read_all().decode('utf-8')
            #self.log(f"Response from SHOW GSM command: {response}\n", 1)

            # Parse ICCID and IMEI
            for line in response.splitlines():
                print(line)
                if 'ICCID:' in line:
                    #self.left_labels["IMEI"].config(text=line.split(':')[1].split(',')[0].strip())
                    self.left_labels["ICCID"].config(text=line.split(':')[2].split(',')[0].strip())
                elif 'IMEI:' in line:
                    #self.left_labels["IMEI"].config(text=line.split(':')[1].split(',')[0].strip())
                    self.left_labels["IMEI"].config(text=line.split(':')[1].split(',')[0].strip())

        except Exception as e:
            self.log(f'Error fetching device data: {e}\n')

    def update_gui(self):
        self.root.after(5000, self.update_gui)

    def update_bulbs(self, status_dict):
        for status, value in status_dict.items():
            canvas, bulb_id = self.bulbs[status]
            color = "white" if value==0 else "red" if value==1 else "green"
            canvas.itemconfig(bulb_id, fill=color)

    def log(self, message, bprint=False):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{now}] {message}"
        self.logfp.write(log_message)
        #self.fp.write(message)
        if bprint:
            print(message)
            
    def report(self, message, bprint=False):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"\n[{now}] {message}"
        #self.logfp.write(log_message)
        self.fp.write(log_message)
        if bprint:
            print(log_message)
    
    def run_test(self):
        if self.run_test_var.get() == True:
            self.reset_attributes()
            self.single_test()
            # Determine overall test resultl
            if self.testfailed == False:
                self.result_label.config(text="Test Result: PASS", foreground="green")
                Tracker.passCount += 1
                #self.testfailed = True
                passVal = "Pass Count: "+ str(Tracker.passCount)
                updatePassFail(passVal, True)
            else:
                self.result_label.config(text="Test Result: FAIL", foreground="red")
                Tracker.failCount += 1
                #self.testfailed = False
                failVal = "Fail Count: "+ str(Tracker.failCount)
                updatePassFail(failVal, False)
            #self.confirm_retry_test()
            totVal = "Total Count: "+str(Tracker.passCount+Tracker.failCount)
            totalCount(totVal)
        else:
            self.result_label.config(text="Test Result: ", foreground="black")
            
    
    def confirm_retry_test(self):
        # Ask user for confirmation before retrying the test
        answer = messagebox.askyesno("Retry Test", "Do you want to retry the test?")
        if answer:
            self.status_dict['GPS NMEA'] = False
            self.status_dict['GPS FIX'] = False
            self.status_dict['GSM UART'] = False
            self.status_dict['GSM Registration'] = False
            self.status_dict['SIM'] = False
            self.status_dict['GPRS'] = False
            self.status_dict['Server Connection'] = False
            self.status_dict['Accelerometer'] = False
            self.status_dict['CAN'] = False
            self.status_dict['Factory Set'] = False
            self.status_dict['Factory Read'] = False
            
            self.update_bulbs(self.status_dict)
            self.run_test()  # If the user clicks 'Yes', run the test again

    def final_inputs(self, line, good):
        if '10' in line:
            self.status_dict['Factory Set'] = good
            self.log('Factory Set '+ ('OK' if good else 'FAIL'), 1)
            if good ==2:
                self.factoryset = "OK"
            else:
                self.factoryset = "FAIL"
                self.testfailed =True   
        elif '11' in line:
            self.status_dict['Factory Read'] = good
            self.log('Factory Read '+ ('OK' if good else 'FAIL'), 1)
            if good ==2:
                self.factoryread = "OK"
            else:
                self.factoryread = "FAIL"
                self.testfailed =True  
        elif '0' in line:
            self.status_dict['GPS NMEA'] = good
            self.log('NMEA '+ ('OK' if good else 'FAIL'), 1)
            if good ==2:
                self.gpsnmea = "OK"
            else:
                self.gpsnmea = "FAIL"
                self.testfailed =True  
        elif '1' in line:
            self.status_dict['GPS FIX'] = good
            self.log('GPS FIX '+ ('OK' if good else 'FAIL'), 1)
            if good ==2:
                self.gpsfix = "OK"
            else:
                self.gpsfix = "FAIL"
                self.testfailed =True  
        elif '2' in line:
            self.status_dict['GSM UART'] = good
            self.log('GSM UART '+ ('OK' if good else 'FAIL'), 1)
            if good ==2:
                self.gsmuart = "OK"
            else:
                self.gsmuart = "FAIL"
                self.testfailed =True  
        elif '3' in line:
            self.status_dict['GSM Registration'] = good
            self.log('GSM Registration '+ ('OK' if good else 'FAIL'), 1)
            if good ==2:
                self.gsm_Registration = "OK"
            else:
                self.gsm_Registration = "FAIL"
                self.testfailed =True  
        elif '4' in line:
            self.status_dict['SIM'] = good
            self.log('SIM '+ ('OK' if good else 'FAIL'), 1)
            if good ==2:
                self.sim = "OK"
            else:
                self.sim = "FAIL"
                self.testfailed =True
        elif '5' in line:
            self.status_dict['GPRS'] = good
            self.log('GPRS ' + ('OK' if good else 'FAIL'), 1)
            if good ==2:
                self.GPRS = "OK"
            else:
                self.GPRS = "FAIL"
                self.testfailed =True  
        elif '6' in line:
            self.status_dict['Server Connection'] = good
            self.log('Server Connection '+ ('OK' if good else 'FAIL'), 1)
            if good ==2:
                self.servercon = "OK"
            else:
                self.servercon = "FAIL"
                self.testfailed =True  
        elif '7' in line:
            self.status_dict['Accelerometer'] = good
            self.log('Accelerometer '+ ('OK' if good else 'FAIL'), 1)
            if good ==2:
                self.Acc = "OK"
            else:
                self.ACC = "FAIL"
                self.testfailed =True  
        elif '9' in line:
            self.status_dict['CAN'] = good
            self.log('CAN '+ ('OK' if good else 'FAIL'), 1)
            if good ==2:
                self.can = "OK"
            else:
                self.can = "FAIL"
                self.testfailed =True  
        
        self.update_bulbs(self.status_dict)

    def single_test(self):
        try:
            if not self.serial_port.is_open:
                self.log(f"Opening COM port {self.serial_port.port} with baud rate {self.serial_port.baudrate}\n", 1)
                self.serial_port.open()

            self.serial_port.write(b'START BIT\n')
            time.sleep(1)
            while True:
                updateWindow()  
                line = self.serial_port.readline().decode('utf-8')
                if "OK" in line:
                    self.final_inputs(line, 2)
                elif "FAIL" in line:
                    self.final_inputs(line, 1)
                elif 'END OF TEST' in line:
                    break
                if self.running == False:
                    self.close()
                    return
            ######
            self.serial_port.write(b'SHOW CONFIG\n')
            time.sleep(1)
            response = self.serial_port.read_all().decode('utf-8')
            #self.log(f"Response from SHOW CONFIG command: {response}\n", 1)

            # Parse software and hardware version
            for line in response.splitlines():
                for text1 in line.split(','):   
                    print(text1)
                    if 'SV:' in text1:
                        self.left_labels["Software Version"].config(text=text1.split(':')[1].strip())
                    elif 'HV:' in text1:
                        self.left_labels["Hardware Version"].config(text=text1.split(':')[1].strip())
                    elif 'ID:' in text1:
                        self.left_labels["IMEI"].config(text=text1.split(':')[1].strip())

            # Command to get ICCID and IMEI
            self.serial_port.write(b'SHOW GSM\n')
            time.sleep(1)
            response = self.serial_port.read_all().decode('utf-8')
            #self.log(f"Response from SHOW GSM command: {response}\n", 1)

            # Parse ICCID and IMEI
            for line in response.splitlines():
                for text1 in line.split(','):
                    print(text1)
                    if 'ICCID:' in text1:
                        #self.left_labels["IMEI"].config(text=line.split(':')[1].split(',')[0].strip())
                        self.left_labels["ICCID"].config(text=text1.split(':')[1].strip())
                    elif 'IMEI:' in text1:
                        #self.left_labels["IMEI"].config(text=line.split(':')[1].split(',')[0].strip())
                        self.left_labels["IMEI"].config(text=text1.split(':')[1].strip())
            var = "PASS" if self.testfailed==False else "FAIL" 
            self.report(f"{self.gpsnmea},{self.gpsfix},{self.gsmuart},"
                     f"{self.gsm_Registration},{self.sim},{self.GPRS},"
                     f"{self.servercon},{self.Acc},{self.can},"
                     f"{self.factoryset},{self.factoryread},{var}",1)

            #self.update_bulbs(self.status_dict)  # Call update_bulbs() after tests

        except Exception as e:
            #self.log(f'Error during single test: {e}\n')
            messagebox.showerror("Error", f"Error with COM port {self.com_num} and error is {e}") 
            #print("error single test", e)
            
    def trak_sel(self, val):
        self.run_test_var.set(val)
        updateWindow()      
            
    def refresh_all(self):       
        if comPorts is not None:
            self.com_num_combobox.config(values=comPorts)
    
    def disconCom(self):
        if self.run_test_var.get() == True:
            self.left_labels["COM"].config(text="")
            self.left_labels["Baudrate"].config(text="")
            self.stop_test()
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
            self.canvas_com.itemconfig(self.status_ind,fill='red')
        
                      
    def stop_test(self):
        self.running = False
        self.clear_to_stop()
        
    def clear_to_stop(self):
        self.left_labels["Hardware Version"].config(text="")
        self.left_labels["Software Version"].config(text="")
        self.left_labels["ICCID"].config(text="")
        self.left_labels["IMEI"].config(text="")
        for i in self.status_dict:
            self.status_dict[i] = 0
        self.update_bulbs(self.status_dict)
        self.testfailed=False
            
    def close(self):
        #self.log("Closing application.\n", 1)
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.logfp.close()
        self.fp.close()
        
class Application:
    def __init__(self, root):
        self.root = root
        self.root.title("Four Tracker Test")
        #self.root.geometry('1700x1200')
        
        self.frames  = ttk.Frame(self.root)
        self.frames.pack(side='top')
        quit_button = ttk.Button(self.frames, text="Quit", command= self.quit_all) #command=self.parent.quit)
        #quit_button.grid(column=1, row= 32, pady=5)
        quit_button.grid(column=3, row = 1, ipadx=5, ipady=5, sticky= tk.W)
        
        stop_button = ttk.Button(self.frames, text ="Stop", command= self.stopAll)
        stop_button.grid(column=1, row = 1, ipadx=5, ipady=5)
        
        start_button = ttk.Button(self.frames, text="Start",command=self.start_all) #command=self.run_test)
        start_button.grid(column=0, row = 1, ipadx=5, ipady=5)
        
        refresh_Button = ttk.Button(self.frames, text="Refresh", command=self.refreshAll)
        refresh_Button.grid(column=2, row = 1, ipadx=5, ipady=5)
        
        self.Fullcount = ttk.Label(self.frames,text='Total Count: 0')
        self.Fullcount.grid(column=7, row = 1, padx=50, pady=5)
        
        self.count = ttk.Label(self.frames, text='Pass Count: 0')
        self.count.grid(column=8, row = 1, padx=50, pady=5)
        
        self.count1 = ttk.Label(self.frames, text='Fail Count: 0')
        self.count1.grid(column=9, row = 1, padx=50, pady=5)
        
        self.bd_rate_var = tk.StringVar()
        ttk.Label(self.frames, text=f"Baud Rate : ").grid(column=4, row = 1, padx = 50)
        self.bd_rate_combobox = ttk.Combobox(self.frames, textvariable=self.bd_rate_var)
        self.bd_rate_combobox['values'] = ['9600','115200','230400','460800','921600']
        self.bd_rate_combobox.grid(column=5, row = 1,)
        self.bd_rate_combobox.current(1)
        self.bd_rate_combobox.bind('<<ComboboxSelected>>', self.updBaud)
        
        
        connect_button = ttk.Button(self.frames, text='Connect', command=self.connBut)
        connect_button.grid(column=6, row = 1,)
        
        disconnect_button = ttk.Button(self.frames, text='Disconnect', command=self.disconnBut)
        disconnect_button.grid(column=6, row = 2)
        
        self.tot_track = tk.StringVar()
        ttk.Label(self.frames,text=f'Trackers: ').grid(column=4, row = 2, padx = 5)
        self.comtrak_combobox = ttk.Combobox(self.frames, textvariable= self.tot_track)
        self.comtrak_combobox['values'] = [f'{i}' for i in range(1,5)]
        self.comtrak_combobox.grid(column=5,row=2)
        self.comtrak_combobox.current(0)
        self.comtrak_combobox.bind('<<ComboboxSelected>>', self.trakS)
        
        self.trakAll = []
        
        self.path = ttk.Label(self.root, text = "D:\\")
        self.path.pack(side='bottom',anchor='w')
        
        open_button = ttk.Button(self.root, text='Open a File', command=self.open_text_file)    
        open_button.pack(side='bottom', anchor='w')
        
        # self.date_ll = ttk.Label(self.root, text= datetime.datetime.now().strftime("%Y-%m-%d"))
        # self.date_ll.pack(side='top', anchor='w')
        
        upDateCom()
        
        # Create PanedWindow to hold two main frames
        self.paned_window = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # Create two Tracker instances in separate frames
        self.first_frame = ttk.Frame(self.paned_window)
        self.second_frame = ttk.Frame(self.paned_window)
        self.third_frame = ttk.Frame(self.paned_window)
        self.fourth_frame = ttk.Frame(self.paned_window)
        
        self.paned_window.add(self.first_frame, weight=1)
        self.paned_window.add(self.second_frame, weight=1)
        self.paned_window.add(self.third_frame, weight=1)
        self.paned_window.add(self.fourth_frame, weight=1)

        self.tracker1 = Tracker(self.first_frame, frame_id="Tracker 1")
        self.tracker2 = Tracker(self.second_frame, frame_id="Tracker 2")
        self.tracker3 = Tracker(self.third_frame, frame_id="Tracker 3")
        self.tracker4 = Tracker(self.fourth_frame, frame_id="Tracker 4")
        
        self.trakAll.append(self.tracker1)
        self.trakAll.append(self.tracker2)
        self.trakAll.append(self.tracker3)
        self.trakAll.append(self.tracker4)
        
        
    def trakS(self, event=None):
        selCount = int(self.tot_track.get())
        for i in range(4):
            self.trakAll[i].trak_sel(0)
        for i in range(selCount):
            self.trakAll[i].trak_sel(1)
    
    def updBaud(self, event=None):
        global baudrates
        baudrates = self.bd_rate_var.get()
        print(baudrates)
    
    def open_text_file(self): 
        filetypes = (('text files', '*.txt'), ('All files', '*.*'))
        filePath = fd.askopenfile(filetypes=filetypes, initialdir="/")
        self.root.update()
        print(filePath)
        if filePath != None:
            self.path.config(text=filePath.name)
        
    def start_all(self):
        print("starting...")
        self.thId = []
        
        for trackerObj in self.trakAll:
            self.thId.append(threading.Thread(target=trackerObj.run_test))
            
        for i in self.thId:    
            i.start()
        
        #for i in self.thId:    
        #    i.join()
        
    def connBut(self):
        for trak in self.trakAll:
            trak.connect_to_device()
    
    def disconnBut(self):
        for tracker in self.trakAll:
            tracker.disconCom()
    
    def refreshAll(self):
        upDateCom()
        for tracker in self.trakAll:
            tracker.refresh_all()
    
    def stopAll(self):
        print('stoping..')
        for tracker in self.trakAll:
            tracker.stop_test()
    
    def quit_all(self):
        print("quiting...")
        for tracker in self.trakAll:
            tracker.close()
        self.root.quit()
        
    
    def updateCount(self, countVal):
        self.count.config(text=countVal)
        self.root.update()
    
    def updateCount1(self, countVal):
        self.count1.config(text=countVal)
        self.root.update()   
     
    def totalCount(self, countVal):
        self.Fullcount.config(text = countVal)
        self.root.update()   
        
if __name__ == "__main__":
    root = tk.Tk()
    app = Application(root)
    # root.protocol("WM_DELETE_WINDOW", app.tracker1.close)
    # root.protocol("WM_DELETE_WINDOW", app.tracker2.close)
    # root.protocol("WM_DELETE_WINDOW", app.tracker3.close)
    # root.protocol("WM_DELETE_WINDOW", app.tracker4.close)
    root.mainloop()

    def upDateCom(self):
        for tracker in self.trakAll:
            tracker.refresh_all()

    def quit_all(self):
        print("quiting...")
        for tracker in self.trakAll:
            tracker.close()
        self.root.quit()
    
    def updateCount(self, countVal):
        self.count.config(text=countVal)
        self.root.update()
    
    def updateCount1(self, countVal):
        self.count1.config(text=countVal)
        self.root.update()   
     
    def totalCount(self, countVal):
        self.Fullcount.config(text = countVal)
        self.root.update()   
        
if __name__ == "__main__":
    root = tk.Tk()
    app = Application(root)
    root.protocol("WM_DELETE_WINDOW", app.tracker1.close)
    root.protocol("WM_DELETE_WINDOW", app.tracker2.close)
    root.protocol("WM_DELETE_WINDOW", app.tracker3.close)
    root.protocol("WM_DELETE_WINDOW", app.tracker4.close)
    root.mainloop()