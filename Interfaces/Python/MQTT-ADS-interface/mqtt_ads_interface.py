# -*- coding: utf-8 -*-
"""
Created on Tue Feb 23 12:42:53 2021

@author: Markus Schraven
"""

from threading import Thread
import threading
import mqtt as mqtt_module
import ads as ads_module
import time
import parsing_and_assignment

#%%
class mqtt_ads_interface():
    
    def __init__(self):
        """"
        Instantiate MQTT and ADS class objects
        """
        self.mqtt = mqtt_module.mqtt()
        self.ads = ads_module.ads()
    
    def connect_mqtt(self, mqtt_host, mqtt_port, mqtt_keepalive, aedifion=False, credentials=False):
        """"
        Establish connection to MQTT broker:
        1. Set the host address of the broker
        2. Get username and password from your system environment variables
        """
        if credentials == True:
            if aedifion == True:
                self.mqtt.get_credentials(mqtt_user_environment_variable='AED_USER_MQTT',
                                          mqtt_password_environment_variable='AED_PASSWORD_MQTT')
        if aedifion == True:
            self.mqtt.connect_aedifion()
        else:
            self.mqtt.connect(host=mqtt_host, port=mqtt_port, keepalive=mqtt_keepalive)

    def disconnect_mqtt(self):
        self.mqtt.disconnect()    

    def connect_ads(self, ams_netID, host, create_route=False):
        if create_route == True:
            self.ads.create_route()
        self.ads.connect(ams_netID, host)
    
    def disconnect_ads(self):
        self.ads.disconnect()
    
    def listen(self, threadname, termination):
        """"
        1. Listen for MQTT messages from cloud to write PLC data points
        2. Parse MQTT message to write PLC data point
        3. Send ADS command to PLC data point
        """
        i = 0 
        while termination.is_set():       
            print(f"\n >>> {threadname} \n Thread {threadname} lives for {i} seconds >>> \n")
            time.sleep(1)
            i += 1
    
    def publish(self, threadname, termination, pub_format='simple_json'):
        """"
        Loop through PLC data points to send
        1. Get data point to send from PLC
        2. Parse data point to send to MQTT message
        3. Publish MQTT message
        """
        # print(f"thread {threadname} sleeps for 8 seconds\n")
        # i = 0
        # temp = False
        # while termination.is_set():
        #     if i < 8:
        #         time.sleep(1)
        #         i += 1
        #     elif temp == False:
        #         print(f"thread {threadname} woke up")
        #         temp = True
        while termination.is_set():
            print(f"\n >>> {threadname} >>>")
            # print('Publishing GVL..')
            for i in pub:
                value = self.ads.read('sampleADSGVL.'+i[0])
                if pub_format == 'simple_json':
                    timestamp = time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime())
                    json = parsing_and_assignment.parseJSON(i[0], value, timestamp)
                    print(json)
                    self.mqtt.publish(message=json, topic='general')
            # print('Restart publishing.')
            time.sleep(1)
        
#%%
if __name__ == "__main__":
    # Create ads and mqtt instances
    mqtt_ads = mqtt_ads_interface()
    # Connect MQTT
    try:
        mqtt_ads.connect_mqtt('localhost', 1883, 60)
    except:
        print('\n ****************************************** \n Could not create MQTT connection to broker. \n ****************************************** \n')
    # Connect ADS
    try:
        mqtt_ads.connect_ads(ams_netID='192.168.0.2.1.1', host='192.168.0.2')
    except:
        print('\n ****************************************** \n Could not create ADS connection to target system. \n ****************************************** \n')
    
    # Variables and Parsing
    # Get ADS variables from variable list
    pub, sub = parsing_and_assignment.getADSVariables(file='TwinCAT Project1/TwinCAT Project1/Untitled1/GVLs/sampleADSGVL.TcGVL')
    # Create termination event, e.g. keyboardinterrupt
    termination = threading.Event()
    termination.set()
    try:
        # Create two threads for MQTT listening and publishing
        listen = Thread(target=mqtt_ads.listen, args=("MQTT-listen",termination,))
        publish = Thread(target=mqtt_ads.publish, args=("MQTT-publish",termination,))
        try:
            listen.start()
            publish.start()
        except:
            print("Error: unable to start thread")
        while termination.is_set():
            # Keep main thread alive
            pass
    except KeyboardInterrupt:
        print("Attempting to close threads.")
        termination.clear()
        listen.join()
        publish.join()
        print("Threads successfully closed")
        print("Disconnect MQTT..")
        mqtt_ads.disconnect_mqtt()
        print("MQTT was disconnected")
        print('Disconnect ADS..')
        mqtt_ads.disconnect_ads()
        print('ADS was disconnected')