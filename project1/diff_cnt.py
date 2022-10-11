with open('input.txt','r') as f:
    data=f.read()

with open('output.txt','r') as f:
    data2=f.read()

cnt=0
l=min(len(data2),len(data))
for i in range(l):
    if data[i]!=data2[i]:
        cnt+=1
print("correct rate:", (l-cnt)/l)