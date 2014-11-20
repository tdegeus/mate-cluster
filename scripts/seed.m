% initiate the random seed
mySeed=sum(100*clock);
if verLessThan('matlab','7.5.0') % 2007a or older
    rand('twister',mySeed) ;
elseif verLessThan('matlab','7.14.0')
    RandStream.setDefaultStream(RandStream( 'mt19937ar','Seed',mySeed));
else % newer than 2010b
    RandStream.setGlobalStream(RandStream( 'mt19937ar','Seed',mySeed));
end
