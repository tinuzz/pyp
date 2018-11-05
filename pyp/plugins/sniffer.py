# This plugin implements a IPv4 TCP sniffer

from .pluginbase import Pluginbase
import socket
import sys
import struct
import binascii

class Sniffer(Pluginbase):

    defaults = {
        'interface': 'ens5',
        'protocols': 'tcp',
        'ports': None,
        'callback': None,
    }

    def run(self):
        try:
            s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(0x0003))
            s.bind((self.interface, 0))
        except socket.error as e:
            self.logger.critical('Socket could not be created: %s' % e)
            sys.exit(1)

        if self.ports is not None:
            self.ports_list = str(self.ports).split(',')
        else:
            self.ports_list = []

        if self.protocols is not None:
            self.protocols_list = str(self.protocols).split(',')
        else:
            self.protocols_list = []

        self.logger.info('Ports: %s' % str(self.ports_list))
        self.logger.info('Protocols: %s' % str(self.protocols_list))

        # receive a packet
        while True:
            packet = s.recvfrom(65565)

            #packet string from tuple
            packet = packet[0]

            #parse ethernet header
            eth_length = 14
            eth_header = packet[:eth_length]
            eth = struct.unpack('!6s6sH' , eth_header)
            eth_protocol = socket.ntohs(eth[2])

            #Parse IP packets, IP Protocol number = 8
            if eth_protocol == 8 :

                #take first 20 characters for the ip header
                ip_header = packet[eth_length:20+eth_length]

                #now unpack them
                iph = struct.unpack('!BBHHHBBH4s4s' , ip_header)
                version_ihl = iph[0]
                version = version_ihl >> 4
                ihl = version_ihl & 0xF
                iph_length = ihl * 4
                ttl = iph[5]
                protocol = iph[6]
                s_addr = socket.inet_ntoa(iph[8]);
                d_addr = socket.inet_ntoa(iph[9]);

                #self.logger.debug('Received IP packet: src=%s, dst=%s, protocol=%s' % (str(s_addr), str(d_addr), str(protocol)))

                #TCP protocol
                if protocol == 6 and 'tcp' in self.protocols_list:
                    t = iph_length + eth_length
                    tcp_header = packet[t:t+20]

                    #now unpack them
                    tcph = struct.unpack('!HHLLBBHHH' , tcp_header)
                    source_port = tcph[0]
                    dest_port = tcph[1]
                    sequence = tcph[2]
                    acknowledgement = tcph[3]
                    doff_reserved = tcph[4]
                    tcph_length = doff_reserved >> 4

                    if not self.ports_list or str(source_port) in self.ports_list or str(dest_port) in self.ports_list:

                        self.logger.debug('Received TCP packet: version=%s, ttl=%s, protocol=%s, src=%s, dst=%s, sport=%s, dport=%s, seq=%s' %
                            (str(version), str(ttl), str(protocol), str(s_addr), str(d_addr), str(source_port), str(dest_port), str(sequence)))

                        h_size = eth_length + iph_length + tcph_length * 4
                        data_size = len(packet) - h_size
                        data = packet[h_size:]

                        if len(data) > 0:
                            self.callback(data)
                        else:
                            self.logger.debug('Packet %s contains no data' % str(sequence))


                #UDP packets
                elif protocol == 17 and 'udp' in self.protocols_list:
                    u = iph_length + eth_length
                    udph_length = 8
                    udp_header = packet[u:u+8]

                    udph = struct.unpack('!HHHH' , udp_header)

                    source_port = udph[0]
                    dest_port = udph[1]
                    length = udph[2]
                    checksum = udph[3]


                    if not self.ports_list or str(source_port) in self.ports_list or str(dest_port) in self.ports_list:

                        self.logger.debug('Received UDP packet: version=%s, protocol=%s, src=%s, dst=%s, sport=%s, dport=%s' %
                            (str(version), str(protocol), str(s_addr), str(d_addr), str(source_port), str(dest_port)))

                        h_size = eth_length + iph_length + udph_length
                        data_size = len(packet) - h_size
                        data = packet[h_size:]

                        if len(data) > 0:
                            self.callback(data)
                        else:
                            self.logger.debug('Packet contains no data')
