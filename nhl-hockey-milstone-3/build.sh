#echo $SYSTEM_PASSWD | sudo -S docker build -f Dockerfile.serving --tag sbs:v1 .
docker build -f Dockerfile.serving --tag flask-container:v1 .

