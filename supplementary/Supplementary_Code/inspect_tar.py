import tarfile, sys
p=sys.argv[1]
n=0
try:
    with tarfile.open(p,'r:',ignore_zeros=True) as t:
        for m in t:
            n+=1
            print(n,m.name,m.size,flush=True)
            if n>=10: break
    print('OK first10',flush=True)
except Exception as e:
    print('ERROR after',n,type(e).__name__,str(e),flush=True)
