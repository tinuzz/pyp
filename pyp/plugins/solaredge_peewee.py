# An output plugin that writes SolarEdge data to a database with Peewee

from .pluginbase import Pluginbase
from peewee import *
from pysolaredge.peewee import db_proxy, Inverter, Optimizer, Event
from pprint import pprint

class Solaredge_peewee(Pluginbase):

    defaults = {
        'db_type': 'mysql',
        'db_user': 'user',
        'db_pass': 'pass',
        'db_host': 'localhost',
        'db'     : 'solaredge',
    }

    def initialize(self):
        if self.db_type == 'mysql':
            dbc = MySQLDatabase(self.db, user=self.db_user, password=self.db_pass, host=self.db_host)
        if self.db_type == 'postgresql':
            dbc = PostgresqlDatabase(self.db, user=self.db_user, password=self.db_pass, host=self.db_host)
        db_proxy.initialize(dbc)
        dbc.connect()
        dbc.create_tables([Inverter, Optimizer, Event])

    def handle_raw(self, data):
        pass

    def handle_decoded(self, data):
        if 'decoded' in data:
            if 'inverters' in data['decoded']:
                for dev_id,inverter in data['decoded']['inverters'].items():
                    Inverter.create(**inverter)
            if 'optimizers' in data['decoded']:
                for dev_id,optimizer in data['decoded']['optimizers'].items():
                    Optimizer.create(**optimizer)
