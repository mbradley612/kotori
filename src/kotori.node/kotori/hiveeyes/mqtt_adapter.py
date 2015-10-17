# -*- coding: utf-8 -*-
# (c) 2015 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
# https://pypi.python.org/pypi/twisted-mqtt
# https://github.com/astrorafael/twisted-mqtt/
from twisted.logger import Logger
from twisted.internet import reactor, task
from twisted.application.service import Service
from twisted.internet.endpoints import TCP4ClientEndpoint
from mqtt.client.factory import MQTTFactory

logger = Logger()

class HiveeyesMqttAdapter(Service):

    def __init__(self, broker_host, broker_port=1883, debug=False, callback=None, subscriptions=None):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.callback = callback or self.onPublish
        self.subscriptions = subscriptions or {}
        self.connect()

    def connect(self):
        print 'INFO: Starting MQTT adapter. broker=', self.broker_host, self.broker_port

        factory = MQTTFactory(profile=MQTTFactory.PUBLISHER | MQTTFactory.SUBSCRIBER)
        point   = TCP4ClientEndpoint(reactor, self.broker_host, self.broker_port)

        d = point.connect(factory).addCallback(self.gotProtocol)

    def gotProtocol(self, p):
        self.protocol = p
        d = p.connect("kotori.mqtt", keepalive=0)
        d.addCallback(self.subscribe)
        #d.addCallback(self.prepareToPublish)

    def subscribe(self, *args):
        #d = self.protocol.subscribe("foo/bar/baz", 0)
        for topic in self.subscriptions:
            e = self.protocol.subscribe(topic, 0)
        self.protocol.setPublishHandler(self.callback)

    def onPublish(self, topic, payload, qos, dup, retain, msgId):
        logger.debug("topic={topic}, msg={payload} qos={qos}, dup={dup} retain={retain}, msgId={id}", topic=topic, payload=payload,
            qos=qos, dup=dup, retain=retain, id=msgId)

    def prepareToPublish(self, *args):
        self.task = task.LoopingCall(self.publish)
        self.task.start(5.0)

    def publish(self):
        d = self.protocol.publish(topic="foo/bar/baz", message="hello friends")
        d.addErrback(self.printError)

    def printError(self, *args):
        logger.debug("args={args!s}", args=args)
        reactor.stop()
