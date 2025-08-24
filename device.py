import time, threading, csv

STATUS_NO_CONN = "Disconnected"
STATUS_CONN = "Connected"
MODE_CAPT = "Capturing..."
MODE_IDLE = "Idle"

devStore = "res/_known_devs.csv"

ping_timeout=1
ping_list=[]

class Device():
    uuid=0
    client=None
    name=""
    desc=""
    units=""
    sampleRate=20
    status=""
    mode=""
    def __init__(self, uuid, client, name="", desc="", units="", sampleRate=20, status=STATUS_NO_CONN, mode=MODE_IDLE):
        self.uuid=uuid
        self.client=client
        if name=="": self.name=uuid
        else: self.name=name
        self.desc=desc
        self.units=units
        self.sampleRate=float(sampleRate)
        self.status=status
        self.mode=mode

        # If not known, add to known devices file
        known=False
        with open(devStore) as fp:
            reader = csv.reader(fp,delimiter=",",quotechar='"')
            for row in reader:
                if uuid==row[0]:
                    known=True
                    break
        if not known:
            configTopic = uuid+"/config"
            client.subscribe(configTopic)
            client.message_callback_add(configTopic, self.configIn)
            client.publish(configTopic,"profile")
            ping_start = time.time()
            #TODO: Make this threaded. See device.self_identify for example
            while(time.time() - ping_start <= ping_timeout): 
                pass
            client.unsubscribe(configTopic)

            with open(devStore, "a",newline='') as fp:
                writer = csv.writer(fp, delimiter=",")
                writer.writerow([uuid,name,desc,units,self.sampleRate,mode])

    @staticmethod
    def importDevices(client):
        devices=[]
        with open(devStore) as fp:
            reader = csv.reader(fp, delimiter=",",quotechar='"')
            for row in reader:
                if len(row)==0: continue
                dev = Device(row[0],client,row[1],row[2],row[3],row[4],STATUS_NO_CONN,row[5])
                devices.append(dev)
        return devices

    @staticmethod
    def updateDevStore(device):
        data=[]
        with open(devStore) as fp:
            reader = csv.reader(fp, delimiter=",",quotechar='"')
            data = [row for row in reader]
        for row in data:
            if len(row)==0: continue
            if row[0]==device.getUUID():
                row[1]=device.getName()
                row[2]=device.getDesc()
                row[3]=device.getUnits()
                row[4]=device.getSampleRate()
                row[5]=device.getMode()
        with open(devStore,"w",newline='') as fp: #TODO: Might need to fix this newline thing once you have more than one device
            writer = csv.writer(fp, delimiter=",")
            writer.writerows(data)

    @staticmethod
    def find_devices(client, devices):
        ping_list.clear()

        client.subscribe("ping")
        client.message_callback_add("ping", Device.on_message)
        client.publish("ping","ping")
        ping_start = time.time()
        #TODO: Make this threaded. See device.self_identify for example
        while(time.time() - ping_start <= ping_timeout): pass
        
        client.unsubscribe("ping")
        
        # For known devices, check if found in ping
        for dev in devices:
            if dev.getUUID() in ping_list:
                dev.setStatus(STATUS_CONN)
                ping_list.remove(dev.getUUID())
            else:
                dev.setStatus(STATUS_NO_CONN)

        #For pinged UUIDs not linked to known device, create device
        for newID in ping_list:
            newDev = Device(newID, client)
            newDev.setStatus(STATUS_CONN)
            devices.append(newDev)

    @staticmethod
    def on_message(client,userdata,msg):
        message = msg.payload.decode()
        if not message == "ping":
            ping_list.append(message)

    def configIn(self,client,userdata,msg):
        message = msg.payload.decode()
        if not message == "profile":
            if message.startswith("sampleRate"):
                self.sampleRate = float(message[message.index(':')+1:])

    def getUUID(self):
        return self.uuid
    
    def getMode(self):
        return self.mode
    
    def setMode(self,mode): #This method should only be called in a thread, since it may hold the program
        self.mode=mode
        maxTimeout = (60/self.sampleRate) + 5   #time between samples, plus 5s
        self.publishWithACK(self.uuid+"/ctrl",("capture" if mode==MODE_CAPT else "idle"),maxTimeout,0.1)
        Device.updateDevStore(self)

    def getStatus(self):
        return self.status
    
    def setStatus(self, status):
        self.status=status

    def getName(self):
        return self.name
    
    def setName(self,name):
        self.name=name
        Device.updateDevStore(self)

    def getDesc(self):
        return self.desc

    def setDesc(self,desc):
        self.desc=desc
        Device.updateDevStore(self)

    def getUnits(self):
        return self.units
    
    def setUnits(self,units):
        self.units=units
        Device.updateDevStore(self)

    def getSampleRate(self):
        return self.sampleRate
    
    def setSampleRate(self,sampleRate):
        self.sampleRate=float(sampleRate)
        #TODO: Make a generic publish/ACK method and use it for this
        self.client.publish(self.getUUID()+"/config/sampleRate",sampleRate)
        Device.updateDevStore(self)
    
    def publishWithACK(self,topic,message,timeout=5,rptDelay=1): #If timeout is -1, try forever (used to exit capture mode)
        self.client.subscribe(topic)
        ack_event = threading.Event()
        def on_message(client,userdata,message):
            msg = message.payload.decode()
            if msg=="ACK": ack_event.set()
        def publish_til_ack():
            start_time = time.time()
            while not ack_event.is_set():
                self.client.publish(topic,message)
                time.sleep(rptDelay)
                if (not timeout==-1) and (time.time()-start_time > timeout):
                    self.status=STATUS_NO_CONN
                    break
            self.client.unsubscribe(topic)
        self.client.on_message=on_message

        ack_event.clear()
        threading.Thread(target=publish_til_ack,daemon=True).start()

    def selfIdentify(self):
        ctrlTopic = self.uuid+"/ctrl"
        self.publishWithACK(ctrlTopic,"identify")
