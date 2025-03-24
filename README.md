通过python+dokcer-compose 构建的一个mqtt消息通信的示例小demo

需要特别关注的是:
1. 消息的发布和订阅是在不同的容器中进行的, 因此需要使用docker-compose的network进行连接
2. 代码中进行客户端连接时, 要使用容器的名称, 而不是ip地址
    # 从环境变量中读取 MQTT_BROKER，如果未设置则默认为 127.0.0.1
    MQTT_BROKER = os.getenv("MQTT_BROKER", "127.0.0.1")
3. 在docker-compose.yml中, mqtt的生产者和消费者需要设置环境变量,因为compose构建的项目是在不同的容器中进行的,他们共享同一个网络栈,但是地址不是开发环境所用的ip,是服务名称,因此需要在部署时设置环境变量,加载client的broker, 否则会连接失败
docker-compose.yml:
    version: '3'
    services:
    mqtt-broker:
        image: eclipse-mosquitto
        ports:
        - "1883:1883"
        - "9001:9001"
        volumes:
        - ./mosquitto.conf:/mosquitto/config/mosquitto.conf
        - ./mosquitto/data:/mosquitto/data
        - ./mosquitto/log:/mosquitto/log
        user: "1000:1000"  # 使用当前用户的 UID 和 GID
        healthcheck:
        test: ["CMD", "mosquitto_pub", "-h", "localhost", "-t", "test", "-m", "test"]
        interval: 5s
        timeout: 1s
        retries: 10
    mqtt-producer:
        build:
        context: .
        dockerfile: Dockerfile.producer
        environment:
        - MQTT_BROKER_HOST=mqtt-broker
        - MQTT_BROKER_PORT=1883
        depends_on:
        mqtt-broker:
            condition: service_healthy  # 等待 mqtt-broker 健康检查通过

    mqtt-consumer:
        build:
        context: .
        dockerfile: Dockerfile.consumer
        environment:
        - MQTT_BROKER_HOST=mqtt-broker
        - MQTT_BROKER_PORT=1883
        depends_on:
        mqtt-broker:
            condition: service_healthy  # 等待 mqtt-broker 健康检查通过   