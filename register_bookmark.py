"""Install a current-user protocol handler; never overwrite a different app."""
from pathlib import Path
import subprocess
import sys
import winreg
from config import PYTHONW

ROOT = Path(__file__).resolve().parent
KEY = r'Software\Classes\videosummarizer'
COMMAND_KEY = KEY + r'\shell\open\command'
COMMAND = subprocess.list2cmdline([str(PYTHONW),
                                  str(ROOT / 'bookmark_launcher.py')]) + ' "%1"'


def existing_command():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, COMMAND_KEY) as key:
            return winreg.QueryValueEx(key, '')[0]
    except FileNotFoundError:
        return None


def install():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, KEY):
            if existing_command() != COMMAND:
                raise RuntimeError('videosummarizer 协议已被其他设置使用；未覆盖。')
    except FileNotFoundError:
        pass
    for file in (PYTHONW, ROOT / 'bookmark_launcher.py'):
        if not file.is_file():
            raise RuntimeError('缺少必要文件：' + str(file))
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, KEY) as key:
        winreg.SetValueEx(key, '', 0, winreg.REG_SZ, 'URL:VideoSummarizer')
        winreg.SetValueEx(key, 'URL Protocol', 0, winreg.REG_SZ, '')
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, COMMAND_KEY) as key:
        winreg.SetValueEx(key, '', 0, winreg.REG_SZ, COMMAND)
    assert existing_command() == COMMAND
    print('已注册目前 Windows 用户的 videosummarizer://open 链接。')


def remove():
    if existing_command() is None:
        print('没有本项目的协议注册。')
        return
    if existing_command() != COMMAND:
        raise RuntimeError('协议已由其他设置接管；未删除。')
    for key in (COMMAND_KEY, KEY + r'\shell\open', KEY + r'\shell', KEY):
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key)
    print('已移除本项目的链接注册；模型及摘要文件保留。')


if __name__ == '__main__':
    try:
        if sys.argv[1:] == ['--remove']:
            remove()
        elif not sys.argv[1:]:
            install()
        else:
            raise ValueError('只接受 --remove 或不带参数。')
    except Exception as exc:
        print('注册失败：' + str(exc))
        sys.exit(1)
