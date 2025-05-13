#!/usr/bin/env python3
import sys
import socket
import logging
import struct
import ipaddress

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("/tmp/bmp_controller.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

# 定义 BMP 消息类型
BMP_MSG_TYPES = {
    0: 'Route Monitoring',
    1: 'Statistics Report',
    2: 'Peer Down Notification',
    3: 'Peer Up Notification',
    4: 'Initiation',
    5: 'Termination',
    6: 'Route Mirroring'
}

def parse_bmp_header(data):

    # 解析 BMP 消息
    # logging.info(f"BMP 数据: {data.hex()}")
    
    """
    解析 BMP 消息头
    """
    if len(data) < 6:
        raise ValueError("数据长度不足以包含 BMP 消息头")

    version, msg_length, msg_type = struct.unpack('!BIB', data[:6])

    if version != 3:
        raise ValueError(f"不支持的 BMP 版本：{version}")

    msg_type_str = BMP_MSG_TYPES.get(msg_type, 'Unknown')

    logging.info(f"BMP 版本: {version}")
    logging.info(f"消息长度: {msg_length}")
    logging.info(f"消息类型: {msg_type_str} ({msg_type})")

    return version, msg_length, msg_type, data[6:msg_length]

def parse_peer_header(data):
    """
    解析 Peer Header，并返回剩余的 BGP Update 消息数据
    """
    if len(data) < 42:
        raise ValueError(f"数据长度不足 42 字节，仅有 {len(data)} 字节，无法解析 Peer Header")

    peer_type, peer_flags = struct.unpack('!B B', data[:2])
    peer_distinguisher = struct.unpack('!Q', data[2:10])[0]
    peer_address = data[10:26]  # 16字节
    peer_as, peer_bgp_id = struct.unpack('!II', data[26:34])
    timestamp_seconds, timestamp_microseconds = struct.unpack('!II', data[34:42])
    
    # 解析 IPv4/IPv6 地址
    if peer_flags & 0x80 == 0:  # IPv4
        peer_ip = socket.inet_ntop(socket.AF_INET, peer_address[12:])  # 取后4字节
    else:  # IPv6
        peer_ip = socket.inet_ntop(socket.AF_INET6, peer_address)
        
    # peer_bgp_id 是一个 32 位整数，需要分割为 4 个字节
    bgp_id_str = f"{(peer_bgp_id >> 24) & 0xFF}.{(peer_bgp_id >> 16) & 0xFF}.{(peer_bgp_id >> 8) & 0xFF}.{peer_bgp_id & 0xFF}"
    
    peer_distinguisher_hex = hex(peer_distinguisher)

    logging.info(f"Peer Type: {peer_type}")
    logging.info(f"Flags (peer_flags): {peer_flags}, V={(peer_flags >> 7) & 1}, "
                 f"L={(peer_flags >> 6) & 1}, A={(peer_flags >> 5) & 1}")
    logging.info(f"Peer Distinguisher: {peer_distinguisher_hex}")
    logging.info(f"Peer Address: {peer_ip}")
    logging.info(f"Peer AS: {peer_as}")
    logging.info(f"Peer BGP ID: {bgp_id_str}")
    logging.info(f"Timestamp: {timestamp_seconds}.{timestamp_microseconds}")

    remaining_bgp_data = data[42:]
    logging.info(f"解析 Peer Header 成功，剩余数据长度: {len(remaining_bgp_data)}")

    return remaining_bgp_data

def parse_route_monitoring(remaining_data):
    """
    解析 Route Monitoring 消息，并将 Withdrawn Routes 和 NLRI 转换成 IP 地址格式
    """
    try:
        # 解析 Peer Header，获取 BGP Update 数据
        data = parse_peer_header(remaining_data)

        # 记录 BGP Update 数据的长度和内容
        logging.info(f"剩余 BGP Update 数据长度: {len(data)}")
        logging.info(f"BGP Update 数据: {data.hex()}")

        # **解析 BGP Header**
        if len(data) < 19:
            logging.error("BGP Update 数据不足 19 字节，无法解析 BGP 头部")
            return

        marker = data[:16]  # 16 字节 Marker
        length = struct.unpack("!H", data[16:18])[0]  # 2 字节长度字段
        msg_type = struct.unpack("!B", data[18:19])[0]  # 1 字节类型字段

        if msg_type != 2:
            logging.warning(f"收到的 BGP 消息类型不是 UPDATE，而是 {msg_type}")
            return

        logging.info(f"BGP Header: Length={length}, Type={msg_type}")

        # **跳过 19 字节 BGP 头部**
        data = data[19:]

        # **解析 Withdrawn Routes Length（2字节）**
        if len(data) < 2:
            logging.error("BGP Update 数据不足，无法解析 Withdrawn Routes Length")
            return

        withdrawn_routes_length = struct.unpack("!H", data[:2])[0]
        offset = 2

        logging.info(f"Withdrawn Routes Length: {withdrawn_routes_length}")

        # **解析 Withdrawn Routes**
        withdrawn_routes = data[offset:offset + withdrawn_routes_length]
        offset += withdrawn_routes_length

        withdrawn_list = []
        while len(withdrawn_routes) > 0:
            prefix_length = withdrawn_routes[0]
            octets = (prefix_length + 7) // 8  # 计算前缀需要多少字节
            if len(withdrawn_routes) < 1 + octets:
                logging.error(f"Withdrawn Routes 数据不完整: {withdrawn_routes.hex()}")
                return
            prefix = withdrawn_routes[1:1 + octets]

            # **转换前缀为 IP 地址**
            ip_prefix = convert_prefix_to_ip(prefix, prefix_length)

            withdrawn_list.append(f"{ip_prefix}/{prefix_length}")
            withdrawn_routes = withdrawn_routes[1 + octets:]

        # **解析 Total Path Attribute Length（2字节）**
        if len(data) < offset + 2:
            logging.error("BGP Update 数据不足，无法解析 Total Path Attribute Length")
            return

        total_path_attr_length = struct.unpack("!H", data[offset:offset + 2])[0]
        offset += 2

        logging.info(f"Total Path Attributes Length: {total_path_attr_length}")

        # **解析 Path Attributes**
        path_attributes = data[offset:offset + total_path_attr_length]
        offset += total_path_attr_length

        parsed_attributes = parse_path_attributes(path_attributes)             
            
        # **解析 NLRI**
        nlri = data[offset:]
        nlri_list = []

        while len(nlri) > 0:
            prefix_length = nlri[0]
            octets = (prefix_length + 7) // 8
            if len(nlri) < 1 + octets:
                logging.error(f"NLRI 数据不完整: {nlri.hex()}")
                return
            prefix = nlri[1:1 + octets]

            # **转换前缀为 IP 地址**
            ip_prefix = convert_prefix_to_ip(prefix, prefix_length)

            nlri_list.append(f"{ip_prefix}/{prefix_length}")
            nlri = nlri[1 + octets:]

        logging.info(f"解析 BGP Update 消息: Withdrawn Routes={withdrawn_list}, Parsed Attributes:{parsed_attributes},NLRI={nlri_list}")

    except Exception as e:
        logging.error(f"解析 Route Monitoring 消息时出错: {e}")


def parse_path_attributes(path_attributes):
    """
    解析 BGP Path Attributes，仅解析：
      - AS_PATH (4 字节 AS)
      - Next_Hop
    假设所有 AS 都是 4 字节。
    """
    parsed_attributes = {}
    original_path_attributes = path_attributes

    while len(path_attributes) > 0:
        if len(path_attributes) < 2:
            logging.error(f"Path Attributes 数据不完整: {original_path_attributes.hex()}")
            return parsed_attributes

        flags = path_attributes[0]
        attr_type = path_attributes[1]

        # 判断是否使用 extended length（2 字节）还是 normal length（1 字节）
        # bit 4 (0x10) 标识 extended length
        if flags & 0x10:  # Extended length
            if len(path_attributes) < 4:
                logging.error(f"Path Attributes 长度字段不完整: {original_path_attributes.hex()}")
                return parsed_attributes
            attr_length = struct.unpack("!H", path_attributes[2:4])[0]
            header_size = 4
        else:
            if len(path_attributes) < 3:
                logging.error(f"Path Attributes 长度字段不完整: {original_path_attributes.hex()}")
                return parsed_attributes
            attr_length = path_attributes[2]
            header_size = 3

        if len(path_attributes) < header_size + attr_length:
            logging.error(f"Path Attributes 数据不完整: {original_path_attributes.hex()}")
            return parsed_attributes

        # 取出当前属性值
        attr_value = path_attributes[header_size : header_size + attr_length]
        # 更新剩余待解析的属性
        path_attributes = path_attributes[header_size + attr_length :]

        if attr_type == 2:  # AS_PATH
            # 下面是假设一段连续的 "AS_SEQUENCE" 或 "AS_SET" 等
            # 这里只做简单示例，只解析第一个 segment
            if len(attr_value) < 2:
                logging.error("AS_PATH 属性值不足 2 字节，无法解析 segment_type 和 segment_length")
                continue
            
            segment_type = attr_value[0]      # 比如 2 = AS_SEQUENCE
            segment_length = attr_value[1]   # 有多少个 AS number
            
            # 后面即 4 * segment_length 字节
            as_numbers_data = attr_value[2:]
            expected_length = segment_length * 4
            if len(as_numbers_data) < expected_length:
                logging.error("AS_PATH 属性中 AS number 数据长度不够，可能解析有误")
                continue

            # 按 4 字节解包
            as_format = f"!{segment_length}I"
            as_list = struct.unpack(as_format, as_numbers_data[:expected_length])
            # 转为十进制字符串
            as_path_str = " → ".join(map(str, as_list))
            parsed_attributes["AS_PATH"] = as_path_str

        elif attr_type == 3:  # Next_Hop
            if len(attr_value) != 4:
                logging.error("Next_Hop 属性长度不是 4 字节，解析失败")
                continue
            next_hop = ipaddress.IPv4Address(attr_value).exploded
            parsed_attributes["Next_Hop"] = next_hop

    return parsed_attributes

def convert_prefix_to_ip(prefix_bytes, prefix_length):
    """
    将 BGP NLRI 或 Withdrawn Routes 前缀转换为标准 IPv4 地址格式
    """
    # **IPv4 地址必须填充到 4 字节**
    prefix_bytes = prefix_bytes.ljust(4, b'\x00')

    # **转换成 IPv4 地址**
    ip_addr = socket.inet_ntop(socket.AF_INET, prefix_bytes)

    return ip_addr

def parse_bmp_message(data):
    """
    解析 BMP 消息
    """
    try:    	
        # 解析 BMP 消息头
        version, msg_length, msg_type, msg_body = parse_bmp_header(data)

        # 根据消息类型进一步解析
        if msg_type == 0:  # Route Monitoring
            parse_route_monitoring(msg_body)
        else:
            logging.info(f"未处理的 BMP 消息类型: {msg_type}")

    except Exception as e:
        logging.error(f"解析 BMP 消息时出错: {e}")

def bmp_main():
    host = "0.0.0.0"
    port = 5000
    logging.info(f"BMP 控制器正在监听 {host}:{port}...")

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)

    while True:
        conn, addr = server.accept()
        logging.info(f"[+] 来自 {addr} 的新 BMP 连接")
        try:
            buffer = b""
            while True:
                data = conn.recv(4096)
                if not data:
                    break

                buffer += data

                # 检查缓冲区中是否有完整的 BMP 消息
                while len(buffer) >= 6:
                    # BMP 消息头的前 6 个字节包含版本、消息长度和消息类型
                    version, msg_length, msg_type = struct.unpack('!BIB', buffer[:6])

                    if len(buffer) < msg_length:
                        # 如果缓冲区中的数据不足以组成一个完整的消息，等待更多数据
                        break

                    # 提取完整的 BMP 消息
                    bmp_message = buffer[:msg_length]
                    buffer = buffer[msg_length:]
                    print(f"接收到 BMP 消息: {bmp_message}")
                    # 解析 BMP 消息
                    parse_bmp_message(bmp_message)

        except Exception as e:
            logging.error(f"错误: {e}")
        finally:
            conn.close()
            logging.info(f"[-] 来自 {addr} 的 BMP 连接已关闭")

if __name__ == "__main__":
    bmp_main()

