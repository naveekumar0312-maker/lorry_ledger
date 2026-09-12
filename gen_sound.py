import wave, struct, math

f = wave.open('static/sounds/notification.wav', 'w')
f.setnchannels(1)
f.setsampwidth(2)
f.setframerate(44100)

data = b''
duration = 0.5
frequency = 880  # A5

for i in range(int(44100 * duration)):
    # exponential decay
    value = int(32767.0 * math.sin(2.0 * math.pi * frequency * i / 44100.0) * math.exp(-i/8000.0))
    data += struct.pack('<h', value)

f.writeframesraw(data)
f.close()
