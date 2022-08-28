# Reading_analyzer

/////////////////////////////////////////////////////////////////
/////	Installazione con Anaconda                            ///
/////////////////////////////////////////////////////////////////

0-  installare il database mysql o maridb ed il client mysql
1-  installare la distribuzione python Anaconda o Miniconda
2-  creare un environment con i pacchetti necessari
    `conda create -n dsa-reading -f dsa-reading.env.yaml`
3-  Attivare l'environment
    `. activate dsa-reading`
4-  installare i pacchetti rimanenti con pip
    `pip install celery-amqp-backend pytaglib`
5-  creare l'utente `dsa-reading` ed il database con lo stesso nome in mysql
6-  importare il dump del database 
    (quando viene richiesto inserire la password scelta alla creazione dell'utente)
    `mysql -u dsa-reading -p dsa-reading < dumps/dsa-reading.sql`
7-  installare il pacchetto `rabbitmq-server`
    `dnf install rabbitmq-server`
    oppure
    `apt install rabbitmq-server`
8-  attivare rabbitmq-server:
    sudo systemctl start rabbitmq-server.service
9-  Lanciare il server web e il client Celery con la configurazione d'accesso al progetto
    su cloud google (vedi email)
    `make`

Nota: per uccidere i due processi usare Control-C e poi `pkill -f main_p.py`

/////////////////////////////////////////////////////////////////
/////	Installazione componenti necessari al funzionamento   ///
/////   Sistema operativo Linux Ubuntu 16.04 64 bit   ///////////
/////////////////////////////////////////////////////////////////

1-  installare i seguenti package:
    sudo apt-get install python python-pip mysql-server libmysqlclient-dev libtag1-dev rabbitmq-server
3-  installare virtualenv:
    pip install virtualenv
4-  creare un nuovo virtualenv:
    virtualenv [path della directory scelta]
    esempio: virtualenv Desktop/new_env
5-  attivare il nuovo env:
    source [path alla directory del new_env]/bin/activate
6-  installare i moduli pip nel file python_modules.py:
    pip install -r [pathto]/python_modules.py
7-  seguire le istruzioni alla pagina:
    https://cloud.google.com/sdk/docs#linux
8-  seguire le istruzioni alla pagina 
    https://cloud.google.com/speech-to-text/docs/quickstart-protocol
    per creare un nuovo account google cloud, un nuovo progetto e scaricare la chiave per utilizzare i servizi google cloud
10- installare il file dsa-database.sql tra quelli scaricati:
    mysql -u [username] -p dsa_db < mysql_dump.sql
    dove username sarà = "root" e il file .sql sarà quello nella directory principale del progetto
    il database in cui sarà importato il database nel file .sql deve essere già creato localmente con il nome dsa_db
11- attivare rabbitmq-server:
    sudo systemctl start rabbitmq-server.service
12- eseguire con python il file main_p.py
13- eseguire i worker celery con:
    celery -A [path to]/main_p.celery worker --loglevel=INFO

Al termine di questo procedimento il sistema funzionerà in locale all'indirizzo indicato quando si esegue main_p.py

