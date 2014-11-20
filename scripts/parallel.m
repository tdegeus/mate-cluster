% number of matlab Workers to use
cores = 2;

% change the scheduler data location
sched=findResource('scheduler','type','local');
sched.DataLocation = pwd;

% check if a matlab pool is already open
poolsize = matlabpool('size')
if poolsize == 0
    % no pool is found --> start a new one
    matlabpool(cores);
end

n = 1000;
m = 1000;
A = zeros(n,m);

% a parallel for loop
parfor (i = 1:n)
   A(i,:) = zeros(1,m);
end

% be sure to close the matlabpool
matlabpool close
