#docker build -f Dockerfile-app -t covid-run-apps .

APP=$1
PICKPREF=$2

docker run -d -v `pwd`/../data:/home/jupuser/data covid-run-apps python3 $APP $PICKPREF 119 110
docker run -d -v `pwd`/../data:/home/jupuser/data covid-run-apps python3 $APP $PICKPREF 109 100
docker run -d -v `pwd`/../data:/home/jupuser/data covid-run-apps python3 $APP $PICKPREF 99 90
docker run -d -v `pwd`/../data:/home/jupuser/data covid-run-apps python3 $APP $PICKPREF 89 80
docker run -d -v `pwd`/../data:/home/jupuser/data covid-run-apps python3 $APP $PICKPREF 79 70
docker run -d -v `pwd`/../data:/home/jupuser/data covid-run-apps python3 $APP $PICKPREF 69 60
docker run -d -v `pwd`/../data:/home/jupuser/data covid-run-apps python3 $APP $PICKPREF 59 50
docker run -d -v `pwd`/../data:/home/jupuser/data covid-run-apps python3 $APP $PICKPREF 49 40
docker run -d -v `pwd`/../data:/home/jupuser/data covid-run-apps python3 $APP $PICKPREF 39 30
docker run -d -v `pwd`/../data:/home/jupuser/data covid-run-apps python3 $APP $PICKPREF 29 20
docker run -d -v `pwd`/../data:/home/jupuser/data covid-run-apps python3 $APP $PICKPREF 19 10
docker run -d -v `pwd`/../data:/home/jupuser/data covid-run-apps python3 $APP $PICKPREF 9 0
