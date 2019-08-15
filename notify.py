from umqtt.simple import MQTTClient

topic = 'sprinkler'
client = None
lastMessage = None
messageCount = 0


def setup():
    global client, topic
    client = MQTTClient("sprinkler123", 'test.mosquitto.org')
    result = client.connect()
    if result != 0:
        return False
    client.set_callback(onMessage)
    client.subscribe(topic)
    return True


def publish(message):
    global client, topic
    if client is None:
        return
    client.publish(topic, message)


def onMessage(topic, message):
    global lastMessage, messageCount
    lastMessage = message
    messageCount = messageCount + 1


def getLastMessage():
    global client, lastMessage, messageCount
    client.check_msg()
    return (messageCount, lastMessage)
