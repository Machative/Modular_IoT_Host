import time, threading

STATUS_NO_CONN = "Disconnected."
STATUS_CONN = "Connected."
STATUS_CAPT = "Capturing..."


class Device():
    uuid=0
    client=None
    name=""
    units=""
    sampleRate=20
    status=""
    def __init__(self, uuid, client, name="", units="", sampleRate=20):
        #TODO: Check if uuid in _known_devs, update name if so
        self.uuid=uuid
        if name=="": self.name=uuid
        else: self.name=name
        self.client=client
        self.units=units
        self.sampleRate=sampleRate
    
    def getUUID(self):
        return self.uuid
    
    def getStatus(self):
        return self.status
    
    def setStatus(self, status):
        self.status=status

    def getName(self):
        return self.name
    
    def setName(self,name):
        self.name=name
        #TODO: Update in _known_devs

    def getSampleRate(self):
        return self.sampleRate
    
    #TODO: This can be generalized to send any command with ack and timeout
    def selfIdentify(self):
        ctrlTopic = self.uuid+"/ctrl"
        self.client.subscribe(ctrlTopic)

        ack_event = threading.Event()
        def on_message(client,userdata,message):
            msg = message.payload.decode()
            if msg=="ACK": ack_event.set()
        def publish_til_ack(timeout=5):
            start_time = time.time()
            while not ack_event.is_set():
                self.client.publish(ctrlTopic,"identify")
                time.sleep(1)
                if time.time()-start_time > timeout:
                    self.status=STATUS_NO_CONN
                    break
            self.client.unsubscribe(ctrlTopic)

        self.client.on_message = on_message

        ack_event.clear()
        threading.Thread(target=publish_til_ack, daemon=True).start()
