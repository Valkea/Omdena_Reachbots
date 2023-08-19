# Deploying a model using AWS EC2 (Elastic Cloud Computing)

Sources: 
- https://www.machinelearningplus.com/deployment/deploy-ml-model-aws-ec2-instance/
- https://www.analyticsvidhya.com/blog/2022/09/how-to-deploy-a-machine-learning-model-on-aws-ec2/


## 1. Launch an EC2 instance on AWS

> Login to your AWS account from console.aws.amazon.com

### Create an EC2 instance
> 1. Search *EC2* in the search box in the top (or *Compute* in the list of services)
> 2. Click the `launch instance` button
> 3. Choose a name and an AMI Image that match the need (i.e. Ubuntu server 22.04 LTS)
> 4. Choose an instance type that match the need (i.e. t3.medium)
> 5. Create a Key Pair (don’t ignore) and download the .pem file (put it in your project folder, but don't share it!)
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


## 2. Connect to AWS EC2 instance using ssh
> 1. Under `EC2 / Instances` select your EC2 instance and click `Connect`
> 2. Select `SSH client` tab and follow the instructions
> 3. `cd to the project folder with the .pem file`
> 4. `chmod 400 my_key_pair.pem`
> 5. copy and remember the given Public DNS (let's call it PUBLICuRL in this doc)

### Install docker (if you didn't selected an AMI with docker already installed)
> 1. ```ssh -i my_key_pair.pem ubuntu@PUBLICuRL```
> 2. (remote) Follow the instructions here: https://docs.docker.com/engine/install/ubuntu/
> 	2.1 (remote) `sudo apt-get update`
>	2.2 (remote) `sudo apt-get install ca-certificates curl gnupg`
>	2.3 (remote) `sudo install -m 0755 -d /etc/apt/keyrings`
>	2.4 (remote) `curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg`
>	2.5 (remote) `sudo chmod a+r /etc/apt/keyrings/docker.gpg`
> 	2.6 (remote) `echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null`


### Connect the EC2 instance and run the project
> 1. ```ssh -i my_key_pair.pem ubuntu@PUBLICuRL```
> 2. (remote) `sudo docker run -it -p 5000:5000 valkea/reachbots:latest`
> 3. Access the model using the public url (EC2/Instances) + the app port <br>(i.e. : http://PUBLICuRL:5000 )


## 3. Make it persistant

**Now the model should be running** and that's quite handy to make computations that can't be made on the local computer, but **if we disconnect the terminal the app will stop running!**

So in order to perenize this, we can use the following command:

> (remote) `screen -R deploy docker run -it -p 5000:5000 valkea/reachbots:latest`

And hence the API server will keep running even if the terminal is closed.

But, next time you connect to the EC2 instance you won't see the API running and won't be able to stop it...
To solve this problem, you simply need to get the screen-instance back with the following command:
> (remote) `screen -r`

Then you can check the logs and / or stop the instance
> (remove) `CTRL+C` to stop the instance
