
# Milestone-3

 ## Docker part 1 - Serving:
 <b>To create (build) a Docker image embedded with the flask app, </b>
 1. Navigate to the root of the git repository (nhl-hockey directory).<br>
 2. To makes use of Docker.serving file to create a docker image named "flask-container:v1". On the shell CLI, use the command :
   ```
  ./build.sh
  ```

 3. An image named "flask-container:v1" would have been created after step 2.<br>
 <br>

 <b>To run the image created using Docker.serving file,</b><br>
 1. Navigate to the root of the git repository (nhl-hockey directory).<br>
 2. To makes use of docker image "flask-container:v1" created in the previous step. On the shell CLI, use the command : 
 ```
 ./run.sh
 ```
 3. Command used in run.sh also passes the environment variable COMET_API_KEY to the docker image during runtime. It is retrieved from the environment variable of the local machine.<br>
 4. Commands executed when run.sh is run also perform port-mapping of the flask web application and maps the docker-image port 8083 to the docker host port 8080.<br><br>
 
 <a name="validate"><b> Validating flask-service reachable on docker host port 8080 :</b></a><br><br><b>Method 1 :</b>
 Open a browser on your host machine and run the following on the browser window :
  ```localhost:8080/parag``` <br>
  <b>Method 2:</b>
  Open an interactive shell CLI on Linux and run the following command : ```curl localhost:8080/parag``` 
  
  <b>Expected output on success ：</b><br>
  ```Parag, you are on the right path. Keep moving forward.```

  <br>

<b> To create (build) docker container image and run flask-service inside docker container using docker-compose.yaml file :</b><br>
 1. Navigate to the root of the git repository (nhl-hockey directory).<br>
 2. Open <b>docker-compose.yaml</b> and keep only flask-service section. Remove all other services from the file.
 2. Run this command on the shell CLI.
 ```
  docker-compose up
 ```
 3. Environment variables are retireved from the local-machine and passed to the docker image during runtime.<br>
 4. After the completion of execution of the docker-compose up command, in order to validate flask-service from docker host follow the steps given <a href="#validate">here</a>.
  
 ## Docker part 2 - Streamlit 
 
 <b>How to evaluate us?</b>
  1. Navigate to the root of the git repository (nhl-hockey directory).
  2. ```docker-compose.yaml``` is configured to create, run and enable interaction between 2 services : flask-service and streamlit-service. Run the following command on the shell CLI:
  ```python
  docker-compose up
  ```
  
  3. On completion of the <b>docker-compose up</b> command, you will see an IP-address and port-number published on your shell CLI (Network URL). We set the port number to be 8090 and ip address to be 0.0.0.0, so you can use this command to view the web-page corresponding to the streamlit-service:
  ```python
  localhost:8090
  ```
  or
  ```
  http://127.0.0.1:8090/
  ```
  
  4. Interact with this streamlit-service web-page opened in your browser to test its functionality.
  <br>
  <br>

  ## Explanation of streamlit service

  1. On the left side of the website, you can use the sidebar to choose the model and version you want. Some versions are disabled. There is notification about whether the download succeeds or not. If you can also jump this step and test, we will use our default mode.
  2. On the right side of the website, you can input the Gameid and click on <b>Ping Game</b> to check stats related to the game. Here, our model can handle a difficult situation - <b>the multiple live game switching</b>

  3. Streamlit service is built to provide wide-variety of information about any game. This includes basic information such as game status as well as more advanced and processed information such as occurence of any events between 2 clicks. 