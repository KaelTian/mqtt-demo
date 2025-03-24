import paho.mqtt.client as mqtt  # type: ignore
import logging
import uuid
import sys
import time
import os

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# MQTT 服务器配置
# 从环境变量中读取 MQTT_BROKER，如果未设置则默认为 127.0.0.1
MQTT_BROKER = os.getenv("MQTT_BROKER", "127.0.0.1")
MQTT_PORT = 1883
MQTT_TOPIC = "sensor/data"

# 最大重试次数
MAX_RETRIES = 5

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("Connected successfully")
        client.subscribe(MQTT_TOPIC)
        logging.info(f"Subscribed to {MQTT_TOPIC}")
    else:
        logging.error(f"Connect failed with code {rc}")
    logging.debug(f"Flags: {flags}")

def on_message(client, userdata, msg):
    logging.info(f"Received: {msg.payload.decode()} from {msg.topic}")

def on_disconnect(client, userdata, rc):
    if rc != 0:
        logging.warning(f"Unexpected disconnection. Will auto-reconnect. Code: {rc}")

def on_connect_fail(client, userdata):
    logging.error("Connection failed")

def on_socket_open_fail(client, userdata, socket_id, result):
    logging.error(f"Socket open failed: {result}")

def connect_with_retry(client, broker, port, retries=MAX_RETRIES):
    attempt = 0
    while attempt < retries:
        try:
            logging.info(f"Attempting to connect to {broker}:{port} (Attempt {attempt + 1}/{retries})")
            client.connect(broker, port, keepalive=60)
            return True
        except Exception as e:
            logging.error(f"Connection attempt {attempt + 1} failed: {e}")
            attempt += 1
            if attempt < retries:
                time.sleep(5)  # 等待5秒后重试
    return False

try:
    # 创建客户端实例
    client_id = f'python-mqtt-{str(uuid.uuid4())}'
    client = mqtt.Client(client_id=client_id)

    # 设置回调函数
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    client.on_connect_fail = on_connect_fail
    # client.on_socket_open_fail = on_socket_open_fail

    # 连接到 MQTT 代理，带有重试机制
    if not connect_with_retry(client, MQTT_BROKER, MQTT_PORT):
        logging.error("Failed to connect after maximum retries. Exiting...")
        sys.exit(1)

    # 开始网络循环
    client.loop_forever()

except KeyboardInterrupt:
    logging.info("Interrupted by user, shutting down...")
    client.disconnect()
    sys.exit(0)
except Exception as e:
    logging.error(f"Unexpected error: {e}")
    sys.exit(1)