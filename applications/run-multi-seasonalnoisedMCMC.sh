docker build -f Dockerfile-app -t covid-run-apps .

docker run --rm -d -v `pwd`/../data:/home/jupuser/data covid-run-apps python3 seasonalnoisedMCMC.py 119 110
docker run --rm -d -v `pwd`/../data:/home/jupuser/data covid-run-apps python3 seasonalnoisedMCMC.py 109 100
docker run --rm -d -v `pwd`/../data:/home/jupuser/data covid-run-apps python3 seasonalnoisedMCMC.py 99 90
docker run --rm -d -v `pwd`/../data:/home/jupuser/data covid-run-apps python3 seasonalnoisedMCMC.py 89 80
docker run --rm -d -v `pwd`/../data:/home/jupuser/data covid-run-apps python3 seasonalnoisedMCMC.py 79 70
docker run --rm -d -v `pwd`/../data:/home/jupuser/data covid-run-apps python3 seasonalnoisedMCMC.py 69 60
docker run --rm -d -v `pwd`/../data:/home/jupuser/data covid-run-apps python3 seasonalnoisedMCMC.py 59 50
docker run --rm -d -v `pwd`/../data:/home/jupuser/data covid-run-apps python3 seasonalnoisedMCMC.py 49 40
docker run --rm -d -v `pwd`/../data:/home/jupuser/data covid-run-apps python3 seasonalnoisedMCMC.py 39 30
docker run --rm -d -v `pwd`/../data:/home/jupuser/data covid-run-apps python3 seasonalnoisedMCMC.py 29 20
docker run --rm -d -v `pwd`/../data:/home/jupuser/data covid-run-apps python3 seasonalnoisedMCMC.py 19 10
docker run --rm -d -v `pwd`/../data:/home/jupuser/data covid-run-apps python3 seasonalnoisedMCMC.py 9 0
