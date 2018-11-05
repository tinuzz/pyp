# This plugin starts a tshark process and reads its output

from .pluginbase import Pluginbase
import time
from subprocess import Popen, PIPE
import os
import binascii

class Tshark(Pluginbase):

    defaults = {
        'exe': '/usr/bin/tshark',
        'interface': 'ens5',
        'filter': 'tcp',
        'write_pcap': 'no',
        'pcap_dir': '/var/lib/pyp/pcap',
        'pcap_strftime': '%Y%m%d%H%M%S',
        'callback': None,
    }

    def run(self):
        cmd = [ self.exe, '-l', '-i', self.interface, '-f', self.filter, '-T', 'fields', '-e', 'data' ]
        if self.write_pcap in [ 'yes', 'true' ]:
            pcap = os.path.join(self.pcap_dir, '%s.pcap' % time.strftime(self.pcap_strftime))
            cmd += [ '-w', pcap ]
        tshark = Popen(cmd, bufsize=1, universal_newlines=True, stdout=PIPE, stderr=PIPE)
        while True:
            line = tshark.stdout.readline()
            if len(line) == 0:
                break
            line = line.rstrip()
            if len(line) > 0:
                self.callback(binascii.unhexlify(line))
        print("Tshark terminated. Output follows.")
        stdout, stderr = tshark.communicate(timeout=5)
        print(stdout)
        print(stderr)
