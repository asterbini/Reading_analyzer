#    coding=utf-8

import io, os, six, difflib
from google.cloud import speech_v1 as speech
#from google.cloud.speech_v1 import enums
from google.cloud.speech_v1 import types
from google.cloud import storage
import json

BUCKET_NAME = 'speech-to-text-long-audio'

def short_audio(audio, context=[]):

    client = speech.SpeechClient()

    with io.open(audio, 'rb') as audio_file:
        content = audio_file.read()

    audio = types.RecognitionAudio(content=content)
    config = types.RecognitionConfig(
        encoding=types.RecognitionConfig.AudioEncoding.FLAC,
        audio_channel_count=2,
        language_code='it-IT',
        enable_word_time_offsets=True)

    response = client.recognize(config, audio)

    for result in response.results:
        alternative = result.alternatives[0]
        '''print('Transcript: {}'.format(alternative.transcript))
        print('Confidence: {}'.format(alternative.confidence))
        '''
        for word_info in alternative.words:
            word = word_info.word.encode('utf-8')
            start_time = word_info.start_time
            end_time = word_info.end_time
            print('Word: {}, start_time: {}, end_time: {}'.format(word, start_time, end_time))

    return (result.alternatives[0].transcription, result.alternatives[0].confidence)


def long_audio(audio_url, phrases=[]):
    """Asynchronously transcribes the audio file specified by the gcs_uri."""
    #from Contexts import phrases_rows
    transcript = ''
    word_offsets = []
    client = speech.SpeechClient()

    audio = types.RecognitionAudio(uri=audio_url)
    config = types.RecognitionConfig(
             encoding=types.RecognitionConfig.AudioEncoding.FLAC,
             audio_channel_count=2,
             language_code='it-IT',
             enable_word_time_offsets=True,
             speech_contexts=[speech.types.SpeechContext(
                             phrases=phrases,
                             )],
             )
    operation = client.long_running_recognize(config=config, audio=audio)

    print('Waiting for operation to complete...')
    response = operation.result(timeout=300)

    # Each result is for a consecutive portion of the audio. Iterate through
    # them to get the transcripts for the entire audio file.
    i=0
    for result in response.results:
        alternative = result.alternatives[0]
        transcript += result.alternatives[0].transcript #.encode('utf-8')

        for word_info in alternative.words:
            word = word_info.word #.encode('utf-8')
            start_time = word_info.start_time
            end_time = word_info.end_time
            word_offsets.append({'word': word,
                               'start': start_time.seconds + start_time.microseconds * 10**(-6),
                               'end':   end_time.seconds   + end_time.microseconds   * 10**(-6)})

    with open('transcription.txt', mode='w') as F:
        F.write(transcript)
    with open('offsets.txt', mode='w') as F:
        json.dump(word_offsets,F)

    return (transcript, word_offsets, alternative.confidence)


def download_blob(bucket_name, source_blob_name, destination_file_name):
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)


def upload_file(file_stream, filename, content_type):
    """
    Uploads a file to a given Cloud Storage bucket and returns the public url
    to the new object.
    """
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(filename)

    blob.upload_from_string(
        file_stream
  ,      content_type=content_type
        )
    blob.make_public()
    url = blob.public_url

    if isinstance(url, six.binary_type):
        url = url.decode('utf-8')

    return url


def list_blobs(bucket_name):
    """Lists all the blobs in the bucket."""
    result = []
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blobs = bucket.list_blobs()
    for i in blobs:
        result.append(i.name)
    return result



import sys
def main1():
    file = open(sys.argv[1])
    audio_url = upload_file(file.read(), 'T5246', 'audio/flac')
    transcript, confidence = long_audio(audio_url)
    print('Transcript:\n {}\n\n Confidence: {}'.format(transcript, confidence))


def main2(audio_url):
    from Contexts import phrases_words, phrases_rows, phrases_all

    outf = open('data/altro/outf.txt', 'w+')
    transcript, offsets, confidence = long_audio(f"gs://{BUCKET_NAME}/{audio_url}")
    outf.write("\n|||\n**********Niente***********")
    outf.write("Transcript:\n{}\n\nConfidence: {}".format(transcript, confidence))
    transcript, offsets, confidence = long_audio(f"gs://{BUCKET_NAME}/{audio_url}", phrases_words)
    outf.write("\n|||\n**********Parole separate***********")
    outf.write("Transcript:\n{}\n\nConfidence: {}".format(transcript, confidence))
    transcript, offsets, confidence = long_audio(f"gs://{BUCKET_NAME}/{audio_url}", phrases_rows)
    outf.write("\n|||\n**********Righe separate***********")
    outf.write("Transcript:\n{}\n\nConfidence: {}".format(transcript, confidence))
    outf.close()



def diff_test(source_f, endf):
    from Text import nclean
    #from Myers_onl import diff
    with open(source_f, "r") as test, open(endf, "r") as mano:
        orig, trans = test.read(), mano.read()
    orig, trans = orig.decode('utf-8').lower(), trans.decode('utf-8').lower().split(' ')

    orig = nclean(orig)
    print(orig)
    orig = orig.split(" ")
    print(orig)
    #print "Orig:\n{}\n\nTrans:\n{}".format(orig, trans)
    diff = list(difflib.ndiff(orig, trans))
    outf = open("data/T5246/new_diff.txt", "w")

        
    for w in diff:
        w = w.encode('utf-8')
        outf.write(str(w)+"\n")

    outf.close()

def ritorna(source_f):
    with open(source_f, "r") as f, open("data/altro/testo_a_mano.txt", "r") as tm:
        file_t, orig= f.readlines(), tm.read().split(' ')

    count_r = 0.0
    for w in file_t:
        if w[:3] == '   ':
            pass
        elif w[0] == ' ':
            count_r+=1
    print("******"+source_f+"******")        
    print("len: {}, orig: {}".format(str(len(file_t)), str(len(orig))))
    print(round(count_r/len(orig)*100, 2))

def main():
    from Text import nclean

    diff_test("data/vecchi_proverbi.txt", "data/T5246/diff_Righe_separate.txt")


if __name__ == "__main__":
    main()
