
all:
	python main_p.py & \
	GOOGLE_APPLICATION_CREDENTIALS=`pwd`/speech-to-text-360509-c64936ecb7c4.json celery -A main_p.celery worker --loglevel=INFO
