"""Restricted, resource-bounded local execution for benchmark candidate code."""
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import time


def run(command, workspace=None, read_paths=(), timeout=15, memory_mb=768, *, cwd=None):
    # Candidate tasks use stdlib only. Keep the tested system runtime independent
    # of the API SDK venv, whose Python libraries can live in private user caches.
    command=list(command)
    if Path(command[0]).name.startswith('python'):command[0]='/opt/homebrew/bin/python3'
    root=Path(workspace or cwd).resolve()
    scratch=root/'.sandbox-tmp';scratch.mkdir(exist_ok=True)
    reads=[root,*(Path(p).resolve() for p in read_paths)]
    profile='(version 1) (allow default) (deny network*) (deny process-fork) (deny signal) '
    # Darwin runtime needs additional system data outside library prefixes.
    # Block private user/temp/volume trees except the named test inputs.
    for private in ('/Users','/private/tmp','/private/var/folders','/Volumes'):
        profile+='(deny file-read-data (require-all '+f'(subpath {json.dumps(private)})'+''.join(f'(require-not (subpath {json.dumps(str(p))}))' for p in reads)+')) '
    profile+=f'(deny file-write* (require-all (require-not (subpath {json.dumps(str(root))})) (require-not (literal "/dev/null"))))'
    env={'PATH':'/usr/bin:/bin:/opt/homebrew/bin','TMPDIR':str(scratch),'PYTHONDONTWRITEBYTECODE':'1','PYTHONHASHSEED':'0','LANG':'en_US.UTF-8'}
    def limits():
        resource.setrlimit(resource.RLIMIT_CPU,(max(2,int(timeout)),max(3,int(timeout)+1)))
        resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2))
        resource.setrlimit(resource.RLIMIT_NOFILE,(128,128))
    args=['/usr/bin/sandbox-exec','-p',profile,*map(str,command)]
    proc=subprocess.Popen(args,cwd=root,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,
                          start_new_session=True,preexec_fn=limits)
    deadline=time.monotonic()+timeout
    while True:
        try:
            out,err=proc.communicate(timeout=min(.25,max(.01,deadline-time.monotonic())))
            break
        except subprocess.TimeoutExpired:
            # macOS rejects RLIMIT_AS; sample child RSS as a best-effort memory
            # guard, not a kernel-enforced process-tree memory guarantee.
            status=subprocess.run(['/bin/ps','-o','rss=','-p',str(proc.pid)],capture_output=True,text=True)
            over_memory=status.stdout.strip().isdigit() and int(status.stdout.strip())>memory_mb*1024
            if over_memory or time.monotonic()>=deadline:
                os.killpg(proc.pid,signal.SIGKILL);out,err=proc.communicate()
                return subprocess.CompletedProcess(args,124,out,err+('\nMEMORY_GUARD' if over_memory else '\nTIMEOUT'))
    return subprocess.CompletedProcess(args,proc.returncode,out,err)


def preflight():
    import sys,tempfile
    with tempfile.TemporaryDirectory(prefix='v3-isolation-') as td:
        root=Path(td);outside=root/'outside.txt';outside.write_text('synthetic-canary')
        work=root/'work';work.mkdir()
        script=work/'probe.py'
        script.write_text('''import pathlib,socket,sys,json
checks={}
try:pathlib.Path(sys.argv[1]).read_text();checks['outside_read_denied']=False
except PermissionError:checks['outside_read_denied']=True
try:socket.socket().bind(('127.0.0.1',0));checks['network_denied']=False
except PermissionError:checks['network_denied']=True
pathlib.Path('inside.txt').write_text('ok');checks['workspace_write']=True
print(json.dumps(checks))
''')
        r=run([sys.executable,'-I',str(script),str(outside)],work)
        if r.returncode:raise RuntimeError('Sandbox preflight failed: '+r.stderr[:500])
        checks=json.loads(r.stdout);assert all(checks.values()),checks
        return checks


if __name__=='__main__':print(json.dumps(preflight()))
