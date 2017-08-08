#import modules
import sys
import os
import signal
import gi
import pyudev
import subprocess
import threading
import notify2

gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')

from gi.repository import Gtk as gtk, GLib, GObject
from gi.repository import AppIndicator3 as appindicator
from dbus.exceptions import DBusException

import dev_info

APPINDICATOR_ID = 'write_blocker'
context = pyudev.Context()

class MyIndicator(object):
    '''
    GTK tray applet for USB devices
    '''
    SHOW_NO_DEVICES = False
    
    def __init__(self):
        
        self.devices = {}  # keeps track of devices we added to the menu s
        
        self.image_path='/home/akl_dennis/Desktop/WB_Project/WRITE_BLOCKER.png'
        self.counter = 0
        
        self.no_devices = gtk.MenuItem('No devices')
        self.build_menu()
       

    def main(self):
        indicator = appindicator.Indicator.new(
              APPINDICATOR_ID,os.path.abspath(self.image_path),
                    appindicator.IndicatorCategory.SYSTEM_SERVICES)
         
        indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
        indicator.set_menu(self.menu)

        thread = threading.Thread(target=self.dev_monitor)
        thread.daemon = True
        thread.start()
        gtk.main()

    def build_menu(self):
        ''' Buid the initial menu synchronously '''
        
        self.menu = gtk.Menu()
        menu_icon = gtk.Image()
        image_file_path = "/home/akl_dennis/Desktop/WB_Project/WRITE_BLOCKER.png"
        
        write_blocker = gtk.ImageMenuItem('Open Write Blocker')
        menu_icon.set_from_file(image_file_path)
        write_blocker.set_image(menu_icon)
        write_blocker.set_always_show_image(True)
        self.menu.append(write_blocker)
        self.menu.append(gtk.SeparatorMenuItem())

        if MyIndicator.SHOW_NO_DEVICES:
            self.menu.append(self.no_devices)
        
        device = False
        for device in context.list_devices(subsystem='block',ID_BUS='usb'):
        
            #this for loop is for getting device names from pyudev database 
            #note: dev_info is a separated python script to get other device info.  
        
            disk_name = device.get('DEVNAME')
            dev_name_tmp = disk_name.startswith('/dev/sd') 
            if dev_name_tmp == True and len(disk_name) <=8:
                dev_list = self.create_menu_item(device)
                if dev_list:
                    self.menu.append(dev_list)
                    self.counter += 1

        self.menu.show_all()

        if MyIndicator.SHOW_NO_DEVICES:
            if self.counter == 0:
                print 'Show it buddy'
                self.no_devices.show()
            else:
                self.no_devices.hide()


    def dev_monitor(self):
        '''
        This is the event listener
        We keep an eye out for add and remove event.
        '''
        
        monitor = pyudev.Monitor.from_netlink(context)
        monitor.filter_by(subsystem='block')

        for action, device in monitor:
            disk_1 = device.get('DEVNAME')
            
            if disk_1.startswith('/dev/sd') and len(disk_1) <=8:
                if action == 'remove':
                    target = self.devices.get(device.get('ID_SERIAL'))
                    for i in self.menu.get_children():
                        if i == target:
                            GLib.idle_add(self.menu.remove, i)
                            GLib.idle_add(self.menu.hide)
                            GLib.idle_add(self.menu.show)
                            self.counter -= 1
                            break

                elif action == 'add':
                    self.counter += 1
                    try:
                        dev_notification_info = dev_info.Device(disk_1)
                        dev_notification_model = dev_notification_info.get_dev_model()
                        dev_notification_serial = dev_notification_info.get_dev_serial()
                        dev_notification_size = dev_notification_info.get_dev_size()
                        dev_notification_status = dev_notification_info.get_dev_status()
                        notification_icon_path = "/home/akl_dennis/Desktop/WB_Project/READ-WRITE.png"
                        if dev_notification_status == "READ-ONLY":
                           notification_icon_path = "/home/akl_dennis/Desktop/WB_Project/READ-ONLY.png"
                        dev_n_info = "%s %s %s %s %s %s %s %s %s %s %s" % ("Device:",disk_1,"\n","Model:",dev_notification_model,"\n","Size:",dev_notification_size,"\n","Status:",dev_notification_status)
                        notify2.init("USB_Device_Notification")
                        n = notify2.Notification("USB Inserted",dev_n_info, notification_icon_path)
                        n.show()
                        

                    except IOError, ex:
                        print (ex)

                    except DBusException, ex:
                        print (ex)

                    item = self.create_menu_item(device)
                    GLib.idle_add(self.menu.append, item)
                    GLib.idle_add(item.show)
                    if MyIndicator.SHOW_NO_DEVICES:
                        GLib.idle_add(self.no_devices.hide)
                   
            if MyIndicator.SHOW_NO_DEVICES and self.counter == 0:
                GLib.idle_add(self.no_devices.show)

    def create_menu_item(self,device):
        '''
        Creates a label for the menu item used in the AppIndicator
        '''
        disk_name = device.get('DEVNAME')

        if disk_name.startswith('/dev/sd') and len(disk_name) <=8:
            device_info = dev_info.Device(disk_name)
            dev_model = device_info.get_dev_model()
            dev_size = device_info.get_dev_size()
        
            label = "%s %s %s %s" % ("Model:",dev_model,"  ",dev_size)
            dev_list = gtk.ImageMenuItem(label)
    
            dev_status = device_info.get_dev_status()
            menu_item_icon = gtk.Image()
            menu_item_icon.set_from_file(self.update_menu_icon(dev_status))
            dev_list.set_image(menu_item_icon)
            dev_list.set_always_show_image(True)
            
        
            self.devices[device.get('ID_SERIAL')] = dev_list
            
            return dev_list
        return None
            
    def update_menu_icon(self,status):
        if (status) == "READ-WRITE":
            return "/home/akl_dennis/Desktop/WB_Project/green_dot.png"
           
        else:
            return "/home/akl_dennis/Desktop/WB_Project/red_dot.png"
    

if __name__=="__main__":
    GObject.threads_init()
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    m = MyIndicator()
    m.main()


