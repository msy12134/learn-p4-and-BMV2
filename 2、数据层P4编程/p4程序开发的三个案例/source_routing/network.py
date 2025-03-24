from p4utils.mininetlib.network_API import NetworkAPI

net = NetworkAPI()

# Network general options
net.setLogLevel('info')
net.enableCli()

# Network definition
net.addP4Switch('s1', cli_input='s1-commands.txt')
net.addP4Switch('s2', cli_input='s2-commands.txt')
net.addP4Switch('s3', cli_input='s3-commands.txt')
net.addP4Switch('s4', cli_input='s4-commands.txt')
net.setP4SourceAll('p4src/source_routing.p4')

net.addHost('h1')
net.addHost('h2')

net.addLink('h1','s1')
net.addLink('s1','s2')
net.addLink('s1','s3')
net.addLink('s2','s4')
net.addLink('s3','s4')
net.addLink('s4','h2')

# Assignment strategy
net.mixed()

# Nodes general options
net.enablePcapDumpAll()
net.enableLogAll()

# Start network
net.startNetwork()