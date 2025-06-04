import os, apport.packaging, apport.hookutils

def add_info(report):
	apport.hookutils.attach_file_if_exists(report, '/var/log/fontconfig.log', 'FontConfigLog')

