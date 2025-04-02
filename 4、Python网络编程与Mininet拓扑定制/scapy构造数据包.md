# 使用 Scapy 构造和解析网络数据包：P4 网络测试指南

在完成 P4 程序并启动 Mininet 网络拓扑后，我们需要测试网络功能是否按预期运行。这时，构造特定的网络数据包进行发送和接收测试就显得尤为重要。Python 的 Scapy 模块是一个强大的网络数据包操作工具，非常适合这类任务。本指南将详细介绍如何使用 Scapy 构造自定义数据包、发送数据包，以及在接收端解析这些数据包。

## 1. 发送端：构造自定义数据包

通常，我们会使用两个 Python 文件来构造和发送自定义数据包：
- `header_definition.py` - 定义自定义数据包结构
- `send.py` - 使用上述定义构造并发送数据包

### 1.1 定义数据包结构 (header_definition.py)

```python
from scapy.fields import BitField, IP6Field
from scapy.layers.inet import IP, ICMP, UDP, TCP
from scapy.layers.inet6 import IPv6
from scapy.layers.l2 import Ether
from scapy.packet import Packet, bind_layers

# 定义探测包头部结构
class probe_t(Packet):
    name = "probe"  # 数据包名称
    fields_desc = [
        BitField('data_cnt', 0, 8)  # 定义 8 位的 data_cnt 字段，默认值为 0
    ]

# 定义探测数据结构
class probe_data_h(Packet):
    name = "probe_data"  # 数据包名称
    fields_desc = [
        BitField('swid', 0, 8),               # 交换机 ID
        BitField('ingress_port', 0, 8),       # 入端口
        BitField('egress_port', 0, 8),        # 出端口
        BitField('ingress_byte_cnt', 0, 32),  # 入端口字节计数
        BitField('egress_byte_cnt', 0, 32),   # 出端口字节计数
        BitField('ingress_last_time', 0, 48), # 上次入端口时间
        BitField('ingress_cur_time', 0, 48),  # 当前入端口时间
        BitField('egress_last_time', 0, 48),  # 上次出端口时间
        BitField('egress_cur_time', 0, 48),   # 当前出端口时间
        BitField('ingress_packet_count', 0, 32), # 入端口包计数
        BitField('egress_packet_count', 0, 32),  # 出端口包计数
    ]

# 绑定 IP 层和 probe_t 层，使用协议号 150
bind_layers(IP, probe_t, proto=150)
```

在上面的代码中：
- 我们定义了两个自定义数据包结构：`probe_t` 和 `probe_data_h`
- 每个结构中的 `fields_desc` 详细规定了结构内各个字段的定义
- `BitField('field_name', default_value, bit_length)` 表示一个字段，其中：
  - `field_name` - 字段名称
  - `default_value` - 默认值
  - `bit_length` - 字段位长度
- `bind_layers()` 函数用于预先定义各层结构之间的关系，方便接收解析

### 1.2 构造并发送数据包 (send.py)

```python
from scapy.all import *
from header_definition import *

# 构造复杂的多层数据包
packet = Ether(src="eth0", dst="ff:ff:ff:ff:ff:ff") / \
         IPv6(nh=43) / srv6h_t(segment_left=0, last_entry=4) / srv6_list_t(segment_id="::100") / \
         srv6_list_t(segment_id="::200") / srv6_list_t(segment_id="::300") / \
         srv6_list_t(segment_id="::400") / srv6_list_t(segment_id="::500") / \
         IP(src='10.0.0.1', dst='10.0.0.2', proto=150) / probe_t(data_cnt=0)

# 发送数据包，指定发送接口
sendp(packet, iface='eth0')
```

关键点：
- 使用 `/` 运算符将不同层的数据包组合在一起
- 每一层都可以指定特定的参数
- `sendp()` 函数用于发送二层数据包，指定发送接口即可

## 2. 接收端：解析数据包

接收端同样需要两个文件：
- `header_definition.py` - 与发送端相同的数据包结构定义
- `receive.py` - 接收并解析数据包

### 2.1 解析复杂数据包 (receive.py)

```python
from scapy.all import *
from header_definition import *

def packet_show(pkt):
    """解析并显示数据包内容"""
    
    # 转换为原始字节并解析以太网头部
    pkt = bytes(pkt)
    ether = Ether(pkt)
    print("Ethernet Header:")
    print(f"  dst = {ether.dst}")
    print(f"  src = {ether.src}")
    print(f"  type = 0x{ether.type:04x}")
    
    # 解析 IPv4 头部
    ipv4 = IP(bytes(ether.payload))
    print(f"IPv4 Header:")
    print(f"  version = {ipv4.version}")
    print(f"  ihl = {ipv4.ihl}")
    print(f"  tos = {ipv4.tos}")
    print(f"  len = {ipv4.len}")
    print(f"  id = {ipv4.id}")
    print(f"  flags = {ipv4.flags}")
    print(f"  frag = {ipv4.frag}")
    print(f"  ttl = {ipv4.ttl}")
    print(f"  proto = {ipv4.proto}")
    print(f"  chksum = {ipv4.chksum}")
    print(f"  src = {ipv4.src}")
    print(f"  dst = {ipv4.dst}")
    
    # 解析自定义探测头部
    probe_header = probe_t(bytes(ipv4.payload))
    print(f"Probe Header:")
    print(f"  data_cnt = {probe_header.data_cnt}")
    
    # 解析多个探测数据结构（如果存在）
    list = []
    if probe_header.data_cnt > 0:
        probe_data = probe_data_h(bytes(probe_header.payload))
        list.append(probe_data)
        
        # 遍历所有探测数据
        for i in range(probe_header.data_cnt):
            print(f" probe_data_{i + 1}")
            print(f"  swid={probe_data.swid}")
            print(f"  ingress_port={probe_data.ingress_port}")
            print(f"  egress_port={probe_data.egress_port}")
            print(f"  ingress_byte_cnt={probe_data.ingress_byte_cnt}")
            print(f"  egress_byte_cnt={probe_data.egress_byte_cnt}")
            print(f"  ingress_last_time={probe_data.ingress_last_time}")
            print(f"  ingress_cur_time={probe_data.ingress_cur_time}")
            print(f"  egress_last_time={probe_data.egress_last_time}")
            print(f"  egress_cur_time={probe_data.egress_cur_time}")
            print(f"  ingress_packet_count={probe_data.ingress_packet_count}")
            print(f"  egress_packet_count={probe_data.egress_packet_count}")
            
            # 继续解析下一个探测数据
            if i <= probe_header.data_cnt - 2:
                probe_data = probe_data_h(bytes(probe_data.payload))
                list.append(probe_data)

# 设置接收过滤器并开始接收
# 例如：sniff(iface="eth0", prn=packet_show, filter="ip proto 150")
```

解析过程说明：
1. 首先将数据包转换为原始字节
2. 逐层解析各层头部：以太网、IP、自定义探测头等
3. 对于具有多个数据结构的情况，使用循环解析
4. 通过 `payload` 属性访问下一层的数据

## 3. 完整工作流程

1. **准备工作**：
   - 定义自定义数据包结构 (`header_definition.py`)
   - 编写发送脚本 (`send.py`) 和接收脚本 (`receive.py`)

2. **测试流程**：
   - 在接收端启动接收脚本：`python receive.py`
   - 在发送端执行发送脚本：`python send.py`
   - 分析接收端的输出，验证数据包是否被正确传输和解析

## 4. 注意事项

- 使用 `bind_layers()` 可以简化数据包解析，但不是必须的
- 在解析复杂嵌套结构时，需要特别注意正确处理 `payload` 部分
- 针对特定网络环境，可能需要调整数据包的各层参数
- 在实际 P4 网络测试中，建议先从简单的数据包开始，逐步增加复杂度

通过 Scapy 构造和解析自定义数据包，我们可以全面测试 P4 网络的功能，确保网络按照预期设计正常工作。