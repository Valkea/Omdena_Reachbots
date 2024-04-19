# Inference API for the Reachbots Omdena's project

You will find in the section below, all the instructions required to run the API on your own computer.
 
1 - in the first section, I will describe how to run it from the source (so you can modify the API)<br>
2 - in the second section, I will explain how to use the API from the docker I prepared and deployed on the Docker Hub.
3 - in the third section, I will explain how to run both the Inference API and Streamlit app using docker-compose.

> The easiest and quicker way to test the inference API is to run the docker version hosted on DockerHub
>
> ```bash
> >> docker run -it -p 5000:5000 valkea/reachbots:latest
> ```

## 1. Run the API locally from sources
(You will need Omdena's credential for this part, but if you don't have these credentials, you can try out the Docker version at the bottom)

### First, 
let's dupliacate the project github repository

```bash
>>> git clone https://dagshub.com/Omdena/Reachbots.git
>>> git checkout task-4-deployment
>>> cd API_serving
```

### Secondly,
let's create a virtual environment and install the required Python libraries

(Linux or Mac)
```bash
>>> python3 -m venv venv_t4_InfAPI
>>> source venv_t4_InfAPI/bin/activate
(venv) >>> pip install -r requirements.txt
```

(Windows):
```bash
>>> py -m venv venv_t4_InfAPI
>>> .\venv_t4_InfAPI\Scripts\activate
(venv) >>> py -m pip install -r requirements.txt
```

### Running API server locally using python scripts

Start both API and CLIENT Flask servers:
```bash
(venv) >>> python API_client_server.py
```
Stop with CTRL+C *(once the tests are done, from another terminal...)*


### Tests

> One can check that the server is running by opening the following url:<br>
> http://0.0.0.0:5000/

> Then you can try the API endpoints from here:<br>
> http://0.0.0.0:5000/docs

> Regular instructions:
> 1. fetch a model key from: http://0.0.0.0:5000/get_available_models
> 2. `post` an image along with a model key to: http://0.0.0.0:5000/predict_defects

> Postman instructions:
> 1. create a POST query with the previous URL,
> 2. add a field named 'file' of type File in Body/form-data),
> 3. select an image to send with the request,
> 4. add a field named 'selected_model',
> 5. select the key of one of the models returned by the /get_available_models
> 6. send the request and get the result.

> You can also use the simple front-end available here:<br>
> * http://0.0.0.0:5000/upload_defects/ <br>
> When posting an image from this simple frontend, the data will be send to the /predict_defects and the result will be displayed in HTML.

Note that the first request might take some time. But once you've got the first prediction, it should run pretty fast for the others.

### Documentation

The API documentation is available at this endpoint: http://0.0.0.0:5000/docs



## 2. Docker

### Building a Docker image

```bash
>>> docker build -t reachbots .
```

### (Optional) Tag and Push the Docker image

```bash
>>> docker tag reachbots:latest valkea/reachbots:latest
>>> docker push valkea/reachbots:latest
```

> Replace `valkea` with your own repo indeed.

### Running a local Docker image

```bash
>>> docker run -it -p 5000:5000 reachbots:latest
```

Then one can run the same test steps as before with curl, postman etc.

Stop with CTRL+C


### (Optional) Pulling a Docker image from Docker-Hub

I pushed a copy of my docker image on the Docker-hub, so one can pull it:

```bash
>>> docker pull valkea/reachbots:latest
```

But this command is optionnal, as running it (see below) will pull it if required.

### Running a Docker image gathered from Docker-Hub

Then the command to start the docker is almost similar to the previous one:

```bash
>>> docker run -it -p 5000:5000 valkea/reachbots:latest
```

And once again, one can run the same curve or postman tests.

Stop with CTRL+C


## 3. Docker compose

First install [docker compose](https://docs.docker.com/compose/install/)

### (Optional) Build

It's common to use `docker compose build` command, but we don't need it here because this one uses images that have already been built (but if you edit the docker-compose.yml file, and define directories instead of pre-built images you will have to use it)

### Run

Once docker-compose and docker are installed, all you need is to **go to the directory with the docker-compose.yml" (it should be the root directory) and run the following command:

```bash
>>> docker compose up
```
Stop with CTRL+C

#### (Optional) Run in detached mode
 
Run it in detached mode with the following command:
```bash
>>> docker compose up -d
```

Then you can get the logs with this one:
```bash
>>> docker compose logs -f
```
Stop with CTRL+C

Finally you can stop the detached containers with:
```bash
>>> docker compose down
```