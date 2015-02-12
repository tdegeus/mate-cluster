
import gpbs

# a = gpbs.Time('1d')
# b = gpbs.Time('2d')

# print a
# print b
# print a-b



# a = gpbs.Host(node=[1,1],cpu=[1,1])
# b = gpbs.Host(node=[1,2],cpu=[1,1])

# print sorted([a,b])


(jobs,nodes) = gpbs.stat(
  qstat    = open('qstat.log'   ,'r').read() ,
  pbsnodes = open('pbsnodes.log','r').read() ,
  ganglia  = open('ganglia.log' ,'r').read() ,
)

A = [i['walltime'] for i in jobs if i['owner']=='tdegeus']

print sum([float(i) for i in A])
print float(sum(A))