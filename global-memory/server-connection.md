---
name: server-connection
description: AWS EC2 server connection details for running Jupyter notebooks
metadata: 
  node_type: memory
  type: project
  originSessionId: 5fbc6e8c-ca2b-417d-a941-048c0a7aa807
---

AWS EC2 server: `ec2-user@44.210.141.140`
SSH key: `/Users/lanyuanzhe/Documents/GitHub/jisuan_wuli/labsuser.pem`
Permission: chmod 600 required on the pem file

Server specs: Amazon Linux 2023, Python 3.13.9 (Anaconda), 2GB RAM, 50GB disk, Jupyter/numpy/scipy/matplotlib all installed.

The server IP changes on every restart (no Elastic IP). Need to get the current public IP from AWS console each session. Notebooks are stored at `/home/ec2-user/homework/`.

**How to apply:** Use `ssh -o ConnectTimeout=10 -i labsuser.pem ec2-user@<IP>` to connect. Execute notebooks with `jupyter nbconvert --to notebook --execute --inplace`.

[[pdf-generation-chrome]]
