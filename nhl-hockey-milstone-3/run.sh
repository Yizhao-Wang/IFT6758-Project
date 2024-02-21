# When run using ./run.sh, we don't need an interactive shell and therefore run it without -it
#echo $SYSTEM_PASSWD | sudo -S docker run -e COMET_API_KEY sbs:v1
#echo $SYSTEM_PASSWD | sudo -S docker run -e COMET_API_KEY -p 8080:8083 sbs:v1

# When running manually on the shell terminal, then run using -it flag as shown below
#echo $SYSTEM_PASSWD | sudo -S docker run -it -e COMET_API_KEY sbs:v1
docker run -e COMET_API_KEY -p 8080:8083 flask-container:v1
