"""Standard-library-only startup lock, usable before pip dependencies exist."""
import ctypes
from ctypes import wintypes
import hashlib
from config import ROOT


class StartupMutex:
    def __enter__(self):
        kernel = ctypes.windll.kernel32
        kernel.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
        kernel.CreateMutexW.restype = wintypes.HANDLE
        kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel.WaitForSingleObject.restype = wintypes.DWORD
        kernel.ReleaseMutex.argtypes = [wintypes.HANDLE]
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        name = 'Local\\VideoSummarizerBookmark-' + hashlib.sha256(str(ROOT).encode()).hexdigest()[:16]
        self.kernel = kernel
        self.handle = kernel.CreateMutexW(None, False, name)
        if not self.handle:
            raise ctypes.WinError()
        status = kernel.WaitForSingleObject(self.handle, 300000)
        if status not in (0, 0x80):
            kernel.CloseHandle(self.handle)
            self.handle = None
            raise RuntimeError('另一个配置或启动正在进行；等待超时，请稍后重试。')
        return self

    def __exit__(self, *args):
        self.kernel.ReleaseMutex(self.handle)
        self.kernel.CloseHandle(self.handle)
