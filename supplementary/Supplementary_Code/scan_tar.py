import tarfile, sys
p=sys.argv[1]
n=0; last=''
try:
    with tarfile.open(p,'r:',ignore_zeros=False) as t:
        for m in t:
            n+=1; last=m.name
            if n % 25 == 0: print('members',n,flush=True)
    print('OK members',n,flush=True)
except Exception as e:
    print('ERROR after',n,'last',last,type(e).__name__,str(e),flush=True)
