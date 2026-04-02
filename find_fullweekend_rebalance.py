from datetime import date,timedelta
from itertools import combinations
start=date(2026,4,9)
N=364
base_even=[1,None,0,0,0,1,1,0,0,1,1,1,0,0]

def make_odd(e):
    return [None if v is None else 1-v for v in e]

def eval_pattern(even):
    odd=make_odd(even)
    off=[]
    base=[]
    for i in range(N):
        dt=start+timedelta(days=i)
        w=(even if (i//14)%2==0 else odd)[i%14]
        base.append((dt,w))
        if w is None:
            off.append(dt)
    if len(off)!=26:
        return None

    def calc(ov):
        arr=[ov.get(dt,w) for dt,w in base]
        def mx(wid):
            m=c=0
            for w in arr:
                c=c+1 if w==wid else 0
                m=max(m,c)
            return m
        def exact4off(wid):
            count=run=0
            for w in arr+[wid]:
                if w!=wid:
                    run+=1
                else:
                    if run==4:
                        count+=1
                    run=0
            return count
        aw=rw=0
        for i,w in enumerate(arr):
            if w is None:
                continue
            dt=start+timedelta(days=i)
            if dt.weekday()>=5:
                if w==0:
                    aw+=1
                else:
                    rw+=1
        return (arr.count(0),arr.count(1),arr.count(None),mx(0),mx(1),exact4off(0),exact4off(1),aw,rw)

    best=None
    for a,b in combinations(off,2):
        for mode in [(a,0,b,1),(a,1,b,0)]:
            ov={mode[0]:mode[1],mode[2]:mode[3]}
            s=calc(ov)
            if s[:3]!=(170,170,24):
                continue
            if s[3]>3 or s[4]>3:
                continue
            score=(abs(s[5]-s[6]),abs(s[7]-s[8]),s[5]+s[6])
            item=(score,s,{str(k):v for k,v in ov.items()})
            if best is None or item[0]<best[0]:
                best=item
    return best

indices=[i for i,v in enumerate(base_even) if v is not None]
seen=[]
for k in range(0,5):
    for comb in combinations(indices,k):
        e=base_even[:]
        for i in comb:
            e[i]=1-e[i]
        if e[2]!=e[3] or e[9]!=e[10] or e[2]==e[9]:
            continue
        r=eval_pattern(e)
        if r:
            seen.append((r,e))

seen.sort(key=lambda x:x[0][0])
print('solutions',len(seen))
for (score,s,ov),e in seen[:20]:
    print('score',score,'stats',s,'ov',ov)
    print('even',e)
    print('odd ',make_odd(e))
    print('---')
