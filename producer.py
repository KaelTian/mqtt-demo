import paho.mqtt.client as mqtt  # type: ignore
import random
import time
import logging
import uuid
import sys
import os
# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# MQTT 服务器配置
# 从环境变量中读取 MQTT_BROKER，如果未设置则默认为 127.0.0.1
MQTT_BROKER = os.getenv("MQTT_BROKER", "127.0.0.1")
MQTT_PORT = 1883
MQTT_TOPIC = "sensor/data"
PUBLISH_INTERVAL = 5  # 发布间隔，单位为秒

# 最大重试次数
MAX_RETRIES = 5

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("Connected successfully to MQTT broker")
    else:
        logging.error(f"Connect failed with code {rc}")

def on_disconnect(client, userdata, rc):
    logging.warning(f"Disconnected with result code {rc}")
    if rc != 0:
        logging.info("Attempting to reconnect...")
        try:
            client.reconnect()
        except Exception as e:
            logging.error(f"Reconnection failed: {e}")

def on_publish(client, userdata, mid):
    logging.debug(f"Message {mid} published successfully")

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
    client_id = f'python-mqtt-producer-{str(uuid.uuid4())}'
    client = mqtt.Client(client_id=client_id)

    # 设置回调函数
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_publish = on_publish

    # 连接到 MQTT 代理，带有重试机制
    if not connect_with_retry(client, MQTT_BROKER, MQTT_PORT):
        logging.error("Failed to connect after maximum retries. Exiting...")
        sys.exit(1)

    # 设置自动重连参数
    client.reconnect_delay_set(min_delay=1, max_delay=120)

    # 启动网络循环
    client.loop_start()

    # 在主循环中
    while True:
        try:
            sensor_data = random.uniform(20, 30)
            result = client.publish(MQTT_TOPIC, str(sensor_data))
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logging.info(f"Published: {sensor_data:.2f} to {MQTT_TOPIC}")
            else:
                logging.error(f"Failed to publish message. Error code: {result.rc}")
                client.reconnect()  # 尝试重新连接
        except Exception as e:
            logging.error(f"Error in main loop: {e}")
            time.sleep(5)  # 等待一段时间后继续尝试
        time.sleep(PUBLISH_INTERVAL)

except KeyboardInterrupt:
    logging.info("Interrupted by user, exiting...")
except Exception as e:
    logging.error(f"Unexpected error: {e}")
finally:
    logging.info("Disconnecting from MQTT broker...")
    client.loop_stop()
    client.disconnect()
    sys.exit(0)