import os
import re
import signal
import socket
import subprocess
import platform
import time
from typing import TypeVar
import requests



T = TypeVar("T")
class SingletonMeta(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]



class ProxyController(metaclass=SingletonMeta):
    def __init__(self):
        self.proxy_list = []
        self._pproxy_pids = []


    def add_proxy(self, listener_port: int, proxy:str,):
        LISTEN = f"http://0.0.0.0:{listener_port}"


    def __run_pproxy(self, listen, proxy: str):

        user = proxy.split('@')[0].split('//')[-1]
        host = proxy.split('@')[-1]

        rserver = f'socks5://{host}#{user}'
        command = f'pproxy -l {listen} -r "{rserver}"'
        # if get_co
        try:
            process = subprocess.Popen(command, shell=True, preexec_fn=os.setsid)
            return process.pid
        except subprocess.CalledProcessError as e:
            print(f"Ошибка при выполнении команды: {e}")


def run_pproxy(listen_port,*, proxy: str =None, host:str=None, username:str=None, password:str=None, get_command=False):
    
    if proxy:
        host = proxy.split('@')[-1]
        user = proxy.split('@')[0].split('//')[-1]
    elif all([host, username, password]):
        user = f'{username}:{password}'
    else: 
        raise Exception(f'proxy not valid, proxy: str ={proxy}, host:str={host}, username:str={username}, password:str={password},')

    rserver = f'socks5://{host}#{user}'
    listen = f"http://0.0.0.0:{listen_port}"

    command = f'pproxy -r "{rserver}" -l {listen} -v'
    if get_command:
        return command
    try:
        if platform.system() == 'Windows':

            windows_command = f'start cmd /c "{command} & pause"'
            process = subprocess.Popen(command, shell=True)
        else:
            gnome_command = f'gnome-terminal -- bash -c "{command}; exec bash"'
            process = subprocess.Popen(gnome_command, shell=True, preexec_fn=os.setsid)
        return process.pid
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при выполнении команды: {e}")



def kill_pproxy_unix(port):
    try:
        result = subprocess.run(f'lsof -i :{port}', shell=True, capture_output=True, text=True)
        out = result.stdout.strip().split('\n')[-1]
        name = out.split(' ')[0]
        print(out)
        print(name)
        if name == 'pproxy':
            pid = int(re.findall(r'\b\d+\b', out)[0])
            os.kill(pid, signal.SIGTERM)
            print('Pproxy_killed')
        else:
            print(f'Port[{port}] busy by: {name}')
    except Exception as ex:
        print('Не удалось получить pid', ex)

def kill_pproxy_windows(port):
    try:
        result = subprocess.run(f'netstat -ano | findstr :{port}', shell=True, capture_output=True, text=True)
        out = result.stdout.strip().split('\n')[-1]
        print(out)
        if out:
            pid = int(out.strip().split()[-1])
            tasklist_result = subprocess.run(f'tasklist /FI "PID eq {pid}"', shell=True, capture_output=True, text=True)
            tasklist_out = tasklist_result.stdout.strip().split('\n')[-1]
            name = tasklist_out.split()[0]
            if pid != 0:
                subprocess.run(f'taskkill /F /PID {pid}', shell=True)
            # if name.lower() == 'python.exe':
            #     print('Pproxy_killed')
            # else:
            #     print(f'Port[{port}] busy by: {name}')
        else:
            print(f'Port[{port}] is not in use')
    except Exception as ex:
        print('Не удалось получить pid', ex)

def kill_pproxy(port):
    os_name = platform.system().lower()
    if os_name == 'windows':
        kill_pproxy_windows(port)
    else:
        kill_pproxy_unix(port)

def get_free_port():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            s.listen(1)
            return s.getsockname()[1]
    except:
        print('sokect close rise error')


def check_proxy_ip(port):
    url = 'https://httpbin.org/ip'
    proxies = {
        'http': f'http://127.0.0.1:{port}',
        'https': f'http://127.0.0.1:{port}',
    }
    try:
        response = requests.get(url, proxies=proxies, timeout=10)
        print(f"Ваш IP через прокси: {response.json()['origin']}")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при подключении через прокси: {e}")
        
        
if __name__ == '__main__':


    port = get_free_port()
    print(f'local proxy port: {port}')
    pid = run_pproxy(
        listen_port=port, 
        host='185.21.60.181:9999',
        username='dlu75iwfeh-mobile-country-US-state-5037779-city-5037649-hold-session-session-66c5af86f02ea',
        password='0N5oOVQ20ad0bkKd',
    )
    print(pid)
    check_proxy_ip(port)
    time.sleep(12)
    kill_pproxy(port)