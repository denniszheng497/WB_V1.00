#Cennix Write-Blocker Verison 1.00
#Date:8-8-2017
#This wb_app.py creates the main Write-blocker GUI and also the READ-ONLY ,READ-WRITE and log functions.
# The "dev_info" class is imported into this GUI class for retriving device info from udev database.


#Import modules
import gi
import pyudev
import os
import subprocess
import threading
import dev_info

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk as gtk,GObject

#connect to pyudev database
context = pyudev.Context()


class WB_Window(gtk.Window):

    def __init__(self):
        gtk.Window.__init__(self, title="Write Blocker")

        headerbar = gtk.HeaderBar()
        headerbar.set_title("Write Blocker")
        self.set_titlebar(headerbar)

        #GUI window config
        self.set_border_width(10)
        self.set_position(gtk.WindowPosition.CENTER)
        self.set_default_size(1000, 450)
        self.outter_box = gtk.VBox(False,spacing=10)
        self.add(self.outter_box)

        #creat device list store
        self.device_list_store = gtk.ListStore(str, str, str, str, str)
        #create device treeview and adding device list store to the treeview
        self.device_list_treeview = gtk.TreeView(self.device_store())

        #get selected values whenever a row is selected
        selected_row = self.device_list_treeview.get_selection()
        selected_row.connect("changed",self.list_selected_item)

        #build the list and append it to the treeview
        self.build_device_list()

        #create buttons
        hbox = gtk.ButtonBox.new(gtk.Orientation.HORIZONTAL)
        hbox.set_layout(gtk.ButtonBoxStyle.CENTER)
        self.outter_box.pack_start(hbox, False,True,0)

        hbox.get_style_context().add_class("linked")

        button_ro = gtk.Button(label="Read-Only")
        button_ro.connect("clicked",self.ro_clicked)
        hbox.add(button_ro)
        button_rw = gtk.Button(label="Read-Write")
        hbox.add(button_rw)
        button_rw.connect("clicked",self.rw_clicked)
        button_log = gtk.Button(label="Log")
        hbox.add(button_log)
        button_quit = gtk.Button(label="Quit")
        button_quit.connect("clicked",self.destory)
        button_quit.show()
        hbox.add(button_quit)

        #create thread to monitor udev activities,update the treeview if there's any device
        #removed or connected
        thread = threading.Thread(target=self.device_monitor)
        thread.daemon = True
        thread.start()

    #this Forloop is getting block devices from udev database and append it to the device_store
    def device_store(self):
        for device in self.get_dev_list():
            self.device_list_store.append(list(device))
        return self.device_list_store

    #build the columns and add them to the treeview
    def build_device_list(self):
        for i, column_title in enumerate(["Device", "Model", "Serial Number","Size","Status"]):
            renderer = gtk.CellRendererText()
            column = gtk.TreeViewColumn(column_title, renderer, text=i)
            column.set_sort_column_id(i)
            self.device_list_treeview.append_column(column)

        self.scrollable_treelist = gtk.ScrolledWindow()
        self.scrollable_treelist.set_vexpand(True)
        self.outter_box.pack_start(self.scrollable_treelist,False,True,0)
        self.scrollable_treelist.add(self.device_list_treeview)

    #get selected rows and only return the first column
    def list_selected_item(self,selection):
        (model,row) = selection.get_selected()
        if row is not None:
            self.selected_device = model[row][0]
            return self.selected_device

    #Read-Only function, import "dev_info" class for getting device info and return them to the message dialog .
    def ro_clicked(self,widget):
        dev = dev_info.Device(self.selected_device)
        dev_serial = dev.get_dev_serial()
        dev_model = dev.get_dev_model()
        dev_status = dev.get_dev_status()
        dev_size = dev.get_dev_size()
        dialog = gtk.MessageDialog(self,0, gtk.MessageType.WARNING,
          gtk.ButtonsType.OK_CANCEL,"Apply READ-ONLY to Device :%s"% self.selected_device)
        dialog.format_secondary_text("Serial Number: %s\nModel Number: %s\nStatus: %s\nSize: %s" % (
          dev_serial, dev_model, dev_status, dev_size))
        response = dialog.run()
    #if user click Ok button , it runs "blockdev" command to mark the disk and linked partitions as Read-Only
        if response == gtk.ResponseType.OK:
           subprocess.call('blockdev --setro %s*' %(self.selected_device),shell=True)
           self.device_list_store.clear()
           self.device_store()

        dialog.destroy()
    #READ-WRITE function, same method as "ro_clicked" function but with READ-WRITE option
    def rw_clicked(self,widget):
        dev = dev_info.Device(self.selected_device)
        dev_serial = dev.get_dev_serial()
        dev_model = dev.get_dev_model()
        dev_status = dev.get_dev_status()
        dev_size = dev.get_dev_size()
        dialog = gtk.MessageDialog(self,0, gtk.MessageType.WARNING,
          gtk.ButtonsType.OK_CANCEL,"Apply READ-WRITE to Device :%s"% self.selected_device)
        dialog.format_secondary_text("Serial Number: %s\nModel Number: %s\nStatus: %s\nSize: %s" % (
          dev_serial, dev_model, dev_status, dev_size))
        response = dialog.run()
        if response == gtk.ResponseType.OK:
           subprocess.call('blockdev --setrw %s*' % (self.selected_device), shell=True)
           self.device_list_store.clear()
           self.device_store()
        dialog.destroy()


    def destory(self, widget, data=None):
        gtk.main_quit()


    def get_dev_list(self):
        dev_list = []
        dev_info_list = []
        for device in context.list_devices(subsystem='block'):
            disk_name = device.get('DEVNAME')
            dev_name_tmp = disk_name.startswith('/dev/sd')
            if dev_name_tmp == True and len(disk_name) <= 8:
                dev_name = disk_name
                dev = dev_info.Device(disk_name)
                dev_model = dev.get_dev_model()
                dev_serial = dev.get_dev_serial()
                dev_size = dev.get_dev_size()
                dev_status = dev.get_dev_status()
                dev_list = [str(disk_name), str(dev_model), str(dev_serial), str(dev_size), str(dev_status)]
                dev_info_list.append(dev_list)
        return dev_info_list


    def device_monitor(self):
        monitor = pyudev.Monitor.from_netlink(context)
        monitor.filter_by(subsystem='block')

        for action, device in monitor:
            dev = device.get('DEVNAME')
            if dev.startswith('/dev/sd') and len(dev) <= 8:
                if action == 'remove' or action == 'add':
                    self.device_list_store.clear()
                    self.device_store()

win = WB_Window()
win.connect("delete-event", gtk.main_quit)
win.show_all()
GObject.threads_init()
gtk.main()


