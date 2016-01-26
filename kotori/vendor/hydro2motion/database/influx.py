# -*- coding: utf-8 -*-
# (c) 2015 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
from twisted.logger import Logger
from twisted.internet import reactor
from autobahn.twisted.wamp import ApplicationRunner, ApplicationSession
from kotori.daq.storage.influx import InfluxDBAdapter

logger = Logger()

class InfluxDatabaseService(ApplicationSession):
    """An application component for logging telemetry data to InfluxDB databases"""

    def onJoin(self, details):
        logger.info("Realm joined (WAMP session started).")

        # subscribe to telemetry data channel
        self.subscribe(self.receive, u'de.elmyra.kotori.telemetry.data')

        self.startDatabase()

        #self.leave()

    def startDatabase(self):

        logger.info('InfluxDB host={host}, version={version}'.format(
            host=self.config.extra['influxdb']['host'],
            version=self.config.extra['influxdb']['version']))

        self.influx = InfluxDBAdapter(
            version  = self.config.extra['influxdb']['version'],
            host     = self.config.extra['influxdb']['host'],
            username = self.config.extra['influxdb']['username'],
            password = self.config.extra['influxdb']['password'],
            database = self.config.extra['hydro2motion']['database'])

    def onLeave(self, details):
        logger.info("Realm left (WAMP session ended).")
        ApplicationSession.onLeave(self, details)

    def onDisconnect(self):
        logger.info("Transport disconnected.")
        #reactor.stop()


    def receive(self, data):
        #print "RECEIVE:", data

        # decode wire data
        payload = data.split(';')
        #print 'payload:', payload

        try:
            MSG_ID          = int(payload[0])
            V_FC            = float(payload[1]) * 0.001
            V_CAP           = float(payload[2]) * 0.001
            A_ENG           = float(payload[3]) * 0.001
            A_CAP           = float(payload[4]) * 0.001
            T_O2_In         = float(payload[5]) * 0.1
            T_O2_Out        = float(payload[6]) * 0.1
            T_FC_H2O_Out    = float(payload[7]) * 0.1
            Water_In        = float(payload[8])
            Water_Out       = float(payload[9])
            Master_SW       = bool(payload[10])
            CAP_Down_SW     = bool(payload[11])
            Drive_SW        = bool(payload[12])
            FC_state        = bool(payload[13])
            Mosfet_state    = bool(payload[14])
            Safety_state    = bool(payload[15])
            Air_Pump_load   = float(payload[16]) * 0.1
            Mosfet_load     = float(payload[17]) * 0.1
            Water_Pump_load = float(payload[18]) * 0.1
            Fan_load        = float(payload[19]) * 0.1
            Acc_X           = float(payload[20]) * 0.001
            Acc_Y           = float(payload[21]) * 0.001
            Acc_Z           = float(payload[22]) * 0.001
            H2_flow         = float(payload[23]) * 0.001
            GPS_X           = float(payload[24]) * 0.01
            GPS_Y           = float(payload[25]) * 0.01
            GPS_Z           = float(payload[26]) * 0.01
            GPS_Speed       = float(payload[27]) * 0.01
            V_Safety        = float(payload[28]) * 0.001
            H2_Level        = int(payload[29])
            O2_calc         = float(payload[30]) * 0.01
            lat             = float(payload[31])
            lng             = float(payload[32])
            P_In            = A_CAP * V_FC
            P_Out           = A_ENG * V_CAP

            # store data to database
            if self.influx:

                success = self.influx.write_points(
                   'telemetry',
                   ["MSG_ID", "V_FC", "V_CAP", "A_ENG", "A_CAP", "T_O2_In", "T_O2_Out", "T_FC_H2O_Out", "Water_In", "Water_Out", "Master_SW", "CAP_Down_SW", "Drive_SW", "FC_state", "Mosfet_state", "Safety_state", "Air_Pump_load", "Mosfet_load", "Water_Pump_load", "Fan_load", "Acc_X", "Acc_Y", "Acc_Z", "H2_flow", "GPS_X", "GPS_Y", "GPS_Z", "GPS_Speed", "V_Safety", "H2_Level", "O2_calc", "lat", "lng", "P_In", "P_Out"],
                   [MSG_ID, V_FC, V_CAP, A_ENG, A_CAP, T_O2_In, T_O2_Out, T_FC_H2O_Out, Water_In, Water_Out, Master_SW, CAP_Down_SW, Drive_SW, FC_state, Mosfet_state, Safety_state, Air_Pump_load, Mosfet_load, Water_Pump_load, Fan_load, Acc_X, Acc_Y, Acc_Z, H2_flow, GPS_X, GPS_Y, GPS_Z, GPS_Speed, V_Safety, H2_Level, O2_calc, lat, lng, P_In, P_Out]
                )
                logger.info("Saved event to InfluxDB: %s" % success)


        except ValueError:
            logger.warn('Could not decode data: {}'.format(data))


def h2m_boot_influx_database(config, debug=False, trace=False):

    websocket_uri = unicode(config.get('wamp', 'listen'))

    logger.info('Starting InfluxDB database service, connecting to WAMP broker "{}"'.format(websocket_uri))

    runner = ApplicationRunner(
        websocket_uri, u'kotori-realm',
        extra={'influxdb': dict(config.items('influxdb')), 'hydro2motion': dict(config.items('hydro2motion'))},
        debug=trace, debug_wamp=debug, debug_app=debug)

    d = runner.run(InfluxDatabaseService, start_reactor=False)

    def croak(ex, *args):
        logger.error('Problem in InfluxDBAdapter, please also check if "crossbar" WAMP broker is running at {websocket_uri}'.format(websocket_uri=websocket_uri))
        logger.error("{ex}, args={args!s}", ex=ex.getTraceback(), args=args)
        reactor.stop()
        raise ex
    #d.addErrback(croak)
