# Deploying a project using AWS EC2 and Docker

Sources: 
- https://www.machinelearningplus.com/deployment/deploy-ml-model-aws-ec2-instance/
- https://www.analyticsvidhya.com/blog/2022/09/how-to-deploy-a-machine-learning-model-on-aws-ec2/


## 1. Launch an EC2 instance on AWS

> Login to your AWS account from console.aws.amazon.com

### Create an EC2 instance
> 1. Search *EC2* in the search box in the top (or *Compute* in the list of services)
> 2. Click the `launch instance` button
> 3. Choose a name and an AMI Image that match the need (i.e. Ubuntu server 22.04 LTS)
> 4. Choose an instance type that matches the need (i.e. t3.medium)
> 5. Create a Key Pair (don’t ignore it) and download the .pem file (put it in your project folder, but don't share it!)
> 6. Increase the Storage to 30GB of EBS General Purpose
> 7. Review and click `Launch`

### Create a security group
> 1. Under `Network and Security / Security Groups` (of the EC2 instance), click `Create Security Group`
> 2. Give it a name, then add Inboud & Outbount rules (type: All traffic | Source/Destination: 0.0.0.0/0).
> 3. Click "Create security group" at the bottom.
> 4. Under `Network and Security` tab, select `Network Interfaces`
> 5. Click on the instance and in the `Actions` menu, select `Change security groups`
> 6. Select the group we just created (basicgroup) and hit `Add Security Group` and `Save`. 
> 7. If needed, start the instance (but it should already be running)


## 2. Connect to AWS EC2 instance and run the last Docker version using ssh

> 1. Under `EC2 / Instances` select your EC2 instance and click `Connect`
> 2. Select `SSH client` tab and follow the instructions
> 3. `cd to the project folder with the .pem file`
> 4. `chmod 400 my_key_pair.pem`
> 5. copy and remember the given Public DNS (let's call it PUBLICuRL in this doc)

### Install docker (if you didn't select an AMI with docker already installed)
> 1. ```ssh -i my_key_pair.pem ubuntu@PUBLICuRL```
> 2. (remote) Follow the instructions here: https://docs.docker.com/engine/install/ubuntu/
> ```
> sudo apt-get update
> sudo apt-get install ca-certificates curl gnupg
> sudo install -m 0755 -d /etc/apt/keyrings
> curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
> sudo chmod a+r /etc/apt/keyrings/docker.gpg
> echo \
>  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
>  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
>  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
> sudo apt-get update
> sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
> ```

### Run the project
> 1. (remote) `sudo docker run -it -p 5000:5000 --pull=always valkea/reachbots:latest`
> 2. Access the model using the public URL (EC2/Instances) + the app port (i.e. : http://PUBLICuRL:5000 )

Then you can stop the instance
> (remove) `CTRL+C` to stop the instance

Or let it run and close the terminal...

## 3. Make it persistent

**Docker instances are persistent by default**, so if you close the terminal *(without `CTRL+C` before)* the container will keep running (which is not the case if you run a Python script for instance).
However, the next time you connect to the EC2 instance you won't see the API running and won't be able to stop it...

To solve this problem, you simply need to get the current docker container NAME
> (remote) `sudo docker ps` and grab de name in the last column

Then you can check the logs
> (remote) `sudo docker logs -f NAME`

Or stop the instance
> (remote) `sudo docker stop NAME`

Or restart it with the lastest available Docker image
> (remote) `sudo docker run -it -p 5000:5000 --pull=always valkea/reachbots:latest`
