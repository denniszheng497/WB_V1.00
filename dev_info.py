import pyudev
import subprocess



class Device(object):


   def __init__(self,dev):
      self.dev = dev

   def get_dev_model(self):

      context = pyudev.Context()
      udev_model = pyudev.Device.from_device_file(context,self.dev)
      dev_model = udev_model.get('ID_MODEL')
      return dev_model

   def get_dev_serial(self):

      serial_cmd = "hdparm -I %s|awk '/Serial Number:/ { print $3}'" %(self.dev)
      serial_output = subprocess.Popen(serial_cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
      serial = serial_output.communicate()[0].rstrip()
      if len(serial) > 100:
         return "empty"
      else:
         return serial

   def get_dev_size(self):
      size_cmd = "lsblk %s | awk 'FNR == 2 {print $4}'" %(self.dev)
      size_output = subprocess.Popen(size_cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
      size = size_output.communicate()[0].rstrip()
      return size

   def get_dev_status(self):
      dev_status_cmd = """lsblk -o RO %s | awk 'FNR ==2'""" %(self.dev)
      status_output = subprocess.Popen(dev_status_cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
      dev_status = status_output.communicate()[0].rstrip()
      if int(dev_status) == 0:
         status = "READ-WRITE"
      else:
         status = "READ-ONLY"
      return status



