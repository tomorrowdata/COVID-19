#docker build -f Dockerfile-app -t covid-run-apps .

APP=$1

docker run -d -v `pwd`/../data:/home/jupuser/data covid-run-apps python3 $APP 119 110
docker run -d -v `pwd`/../data:/home/jupuser/data covid-run-apps python3 $APP 109 100
docker run -d -v `pwd`/../data:/home/jupuser/data covid-run-apps python3 $APP 99 90
docker run -d -v `pwd`/../data:/home/jupuser/data covid-run-apps python3 $APP 89 80
docker run -d -v `pwd`/../data:/home/jupuser/data covid-run-apps python3 $APP 79 70
docker run -d -v `pwd`/../data:/home/jupuser/data covid-run-apps python3 $APP 69 60
docker run -d -v `pwd`/../data:/home/jupuser/data covid-run-apps python3 $APP 59 50
docker run -d -v `pwd`/../data:/home/jupuser/data covid-run-apps python3 $APP 49 40
docker run -d -v `pwd`/../data:/home/jupuser/data covid-run-apps python3 $APP 39 30
docker run -d -v `pwd`/../data:/home/jupuser/data covid-run-apps python3 $APP 29 20
docker run -d -v `pwd`/../data:/home/jupuser/data covid-run-apps python3 $APP 19 10
docker run -d -v `pwd`/../data:/home/jupuser/data covid-run-apps python3 $APP 9 0
