from base64 import decodebytes

f = open('images.txt', 'rb')
lines = f.readlines()
imagestr = lines[3][7:-2]

print(imagestr)

with open("foo.png","wb") as f:
    f.write(decodebytes(imagestr))
