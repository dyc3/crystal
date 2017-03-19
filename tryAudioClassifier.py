#!/usr/bin/env python3
# TODO: replace this file with a unit test

from audio import AudioClassifier
import cProfile
pr = cProfile.Profile()

def printStats():
	pr.print_stats()

audioClass = AudioClassifier()
files = ["audio_train/speech/speech1.wav", "audio_train/speech/speech2.wav", "audio_train/speech/speech3.wav", "audio_train/no_speech/no_speech1.wav", "audio_train/no_speech/no_speech2.wav"]
classes = ["speech", "speech", "speech", "no_speech", "no_speech"]
print("training...")
pr.enable()
audioClass.fit(files, classes)
pr.disable()
printStats()

print("predicting...")
testFiles = ["audio_train/speech/speech4.wav","audio_train/speech/speech5.wav","audio_train/no_speech/no_speech3.wav","audio_train/no_speech/no_speech4.wav"]
results = []
pr = cProfile.Profile()
for f in testFiles:
	pr.enable()
	prediction = audioClass.predictFile(f)
	pr.disable()
	results.append((f,prediction))

print("RESULTS: ")
for r in results:
	print(r[0].ljust(45) + "   " + r[1])

printStats()
