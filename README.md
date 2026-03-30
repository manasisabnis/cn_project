Custom DNS Server with SSL/TLS Support:
This project implements a custom DNS server using UDP sockets with support for multiple clients, caching, performance evaluation, and secure communication using SSL/TLS.

1.Features

* Custom DNS resolution for local domains (e.g., example.local)
* DNS caching with TTL
* Upstream DNS forwarding (Google DNS 8.8.8.8)
* Multi-client handling using threading
* Performance metrics:

  * Latency (response time)
  * Throughput (requests/sec)
* Error handling for invalid queries and failures
* SSL/TLS-based secure communication

2. Architecture

Client → DNS Server (UDP, port 53)
Client → TLS Server (TCP, port 8443)

3. Setup Instructions

 1. Clone the repository

git clone https://github.com/manasisabnis/cn_project.git
cd cn_project

 2. Generate SSL Certificates

openssl req -new -x509 -days 365 -nodes -out server.crt -keyout server.key
 3. Run DNS Server (Mac/Linux)

sudo python dns_server.py

 4. Run TLS Server

python ssl_server.py
5. Run DNS Client (Windows)

nslookup example.local <SERVER-IP>

 6. Run TLS Client

python ssl_client.py
4. Improvements from Deliverable 1

* Added DNS caching with TTL
* Added performance metrics (latency, throughput)
* Improved error handling (NXDOMAIN, SERVFAIL)
* Added SSL/TLS secure communication
* Enhanced multi-client handling


 Security Note

SSL certificates and private keys are excluded using .gitignore for security reasons.

