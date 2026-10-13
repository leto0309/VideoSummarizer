using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Text;
using System.Windows.Forms;

class Launcher : Form {
    readonly string root = AppDomain.CurrentDomain.BaseDirectory;
    readonly TextBox output = new TextBox();
    readonly Label status = new Label();
    readonly Button cancel = new Button();
    readonly bool gpuMode;
    Process worker;
    bool busy;
    bool canCancel, cancelled, closeWhenDone;
    IntPtr installJob;
    string Python { get { return Path.Combine(root, "runtime", "python.exe"); } }
    string Script { get { return Path.Combine(root, "desktop_launcher.py"); } }

    Launcher(bool installGpu = false) {
        gpuMode = installGpu;
        Text = installGpu ? "VideoSummarizer - 可选 GPU 加速" : "VideoSummarizer"; Width = 780; Height = 500;
        StartPosition = FormStartPosition.CenterScreen;
        status.Text = "正在检查本机环境…"; status.Dock = DockStyle.Top; status.Height = 38;
        output.Multiline = true; output.ReadOnly = true; output.ScrollBars = ScrollBars.Both;
        output.WordWrap = false; output.Dock = DockStyle.Fill;
        output.Font = new Font("Consolas", 10);
        cancel.Text = "取消配置"; cancel.Dock = DockStyle.Bottom; cancel.Height = 34; cancel.Enabled = false;
        cancel.Click += delegate { CancelWorker(false); };
        Controls.Add(output); Controls.Add(status); Controls.Add(cancel);
        Shown += delegate { Begin(); };
        FormClosing += delegate(object sender, FormClosingEventArgs e) {
            if (busy) {
                e.Cancel = true;
                if (canCancel) CancelWorker(true);
                else MessageBox.Show(this, "启动仍在进行，请等待下方进度完成后再关闭。", Text);
            }
        };
    }

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    static extern IntPtr CreateJobObject(IntPtr attributes, string name);
    [DllImport("kernel32.dll", SetLastError = true)]
    static extern bool AssignProcessToJobObject(IntPtr job, IntPtr process);
    [DllImport("kernel32.dll", SetLastError = true)]
    static extern bool TerminateJobObject(IntPtr job, uint exitCode);
    [DllImport("kernel32.dll")]
    static extern bool CloseHandle(IntPtr handle);

    static IntPtr CreateInstallerJob(Process process) {
        var job = CreateJobObject(IntPtr.Zero, null);
        if (job == IntPtr.Zero) throw new Win32Exception(Marshal.GetLastWin32Error());
        if (!AssignProcessToJobObject(job, process.Handle)) {
            int error = Marshal.GetLastWin32Error();
            CloseHandle(job);
            if (!process.HasExited) process.Kill();
            throw new Win32Exception(error, "无法建立可取消的安装进程组，已停止本次配置。");
        }
        // No KILL_ON_JOB_CLOSE: successful setup may leave owned services running.
        return job;
    }

    void CancelWorker(bool close) {
        if (!busy || !canCancel || worker == null || worker.HasExited) return;
        if (MessageBox.Show(this, "停止本次配置？已安装的依赖、模型和摘要会保留，可稍后重试。",
            Text, MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes) return;
        cancelled = true; closeWhenDone = close; cancel.Enabled = false;
        status.Text = "正在停止本次安装进程…";
        System.Threading.ThreadPool.QueueUserWorkItem(delegate {
            try { if (!worker.HasExited && !TerminateJobObject(installJob, 1)) throw new Win32Exception(Marshal.GetLastWin32Error()); }
            catch (Exception exc) {
                Add(exc.Message);
                if (!IsDisposed) BeginInvoke(new Action(delegate { cancel.Enabled = busy; closeWhenDone = false; }));
            }
        });
    }

    ProcessStartInfo Command(string argument) {
        var info = new ProcessStartInfo(Python, "-s -u \"" + Script + "\" " + argument);
        info.WorkingDirectory = root; info.UseShellExecute = false; info.CreateNoWindow = true;
        info.RedirectStandardOutput = true; info.RedirectStandardError = true;
        info.StandardOutputEncoding = Encoding.UTF8; info.StandardErrorEncoding = Encoding.UTF8;
        info.EnvironmentVariables.Remove("PYTHONHOME"); info.EnvironmentVariables.Remove("PYTHONPATH");
        info.EnvironmentVariables["PYTHONIOENCODING"] = "utf-8";
        info.EnvironmentVariables["PYTHONNOUSERSITE"] = "1";
        info.EnvironmentVariables["OLLAMA_NO_CLOUD"] = "1";
        var temporary = Path.Combine(root, "tools", "install-temp");
        Directory.CreateDirectory(temporary);
        info.EnvironmentVariables["TEMP"] = temporary;
        info.EnvironmentVariables["TMP"] = temporary;
        return info;
    }

    void Add(string line) {
        if (line == null || IsDisposed) return;
        if (InvokeRequired) { BeginInvoke(new Action<string>(Add), line); return; }
        output.AppendText(line + Environment.NewLine);
    }

    void Begin() {
        try {
            if (!File.Exists(Python)) throw new Exception("找不到内置 Python，请完整解压 ZIP，保留 runtime 文件夹。");
            Directory.CreateDirectory(Path.Combine(root, "logs"));
            // Verify write access before downloading or starting background processes.
            File.AppendAllText(Path.Combine(root, "logs", "desktop.log"), DateTime.Now.ToString("s") + " 启动\n");
            int code;
            using (var check = Process.Start(Command("--check"))) { check.WaitForExit(); code = check.ExitCode; }
            if (code != 0 && code != 10) throw new Exception("环境检查失败，请完整重新解压或查看日志。");
            if (gpuMode && code == 10) throw new Exception("请先打开 VideoSummarizer.exe 完成首次配置，再运行 install-gpu.bat。");
            var consent = gpuMode ? "可选 GPU 加速将下载 CUDA 运行库，可能超过 1 GB，总时限 20 分钟。\n\n只安装到本软件文件夹。取消或失败后，CPU 模式仍可使用。请先等待摘要任务完成。\n\n是否允许下载？" :
                "首次使用需下载尚未内置的免费依赖、工具与本机 AI 模型，建议预留 15 GB 空间。已内置的 Whisper / Ollama 会直接使用。\n\n默认跳过可选 CUDA 库，先使用 CPU 转录；GPU 加速可稍后通过 install-gpu.bat 单独安装。\n\n仅写入本软件文件夹，不安装系统 Python、不改全局 PATH，不使用付费 API 或 cloud。\n\n是否允许下载？";
            if ((code == 10 || gpuMode) && MessageBox.Show(this, consent,
                Text, MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes) {
                status.Text = "已取消首次配置，尚未下载。"; return;
            }
            busy = true;
            canCancel = code == 10 || gpuMode; cancel.Enabled = canCancel;
            status.Text = gpuMode ? "正在安装可选 GPU 加速，可随时取消…" : code == 10 ? "首次配置中，可查看下载进度或取消…" : "正在启动本机服务…";
            worker = new Process(); worker.StartInfo = Command(gpuMode ? "--install-gpu" : code == 10 ? "--setup" : "");
            worker.EnableRaisingEvents = true;
            worker.OutputDataReceived += delegate(object s, DataReceivedEventArgs e) { Add(e.Data); };
            worker.ErrorDataReceived += delegate(object s, DataReceivedEventArgs e) { Add(e.Data); };
            worker.Exited += delegate {
                if (IsDisposed) return;
                BeginInvoke(new Action(delegate {
                    busy = false;
                    if (installJob != IntPtr.Zero) { CloseHandle(installJob); installJob = IntPtr.Zero; }
                    cancel.Enabled = false;
                    status.Text = cancelled ? "已取消配置。现有模型和摘要保留，可稍后重新打开。" : worker.ExitCode == 0 ?
                        (gpuMode ? "GPU 库安装完成，兼容性需通过转录确认。可关闭此窗口。" : "已打开网页，可关闭此窗口。背景服务会继续运行。") :
                        (gpuMode ? "GPU 安装未完成，仍可使用 CPU。请查看下方错误。" : "启动失败：请查看下方错误，修正后重新双击启动。");
                    File.AppendAllText(Path.Combine(root, "logs", "desktop.log"), output.Text, Encoding.UTF8);
                    if (closeWhenDone) Close();
                }));
            };
            worker.Start();
            if (canCancel) installJob = CreateInstallerJob(worker);
            worker.BeginOutputReadLine(); worker.BeginErrorReadLine();
        } catch (Exception exc) { busy = false; status.Text = "启动失败"; Add(exc.Message); }
    }

    [STAThread] static int Main(string[] args) {
        if (args.Length == 1 && args[0] == "--self-test-cancel") {
            var testRoot = AppDomain.CurrentDomain.BaseDirectory;
            try {
                var info = new ProcessStartInfo(Path.Combine(testRoot, "runtime", "python.exe"),
                    "-s -u -c \"import subprocess,sys,time;p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)']);print(p.pid,flush=True);time.sleep(60)\"");
                info.UseShellExecute = false; info.CreateNoWindow = true; info.RedirectStandardOutput = true;
                using (var parent = Process.Start(info)) {
                    var job = CreateInstallerJob(parent);
                    try {
                        int childPid = int.Parse(parent.StandardOutput.ReadLine());
                        if (!TerminateJobObject(job, 1)) throw new Win32Exception(Marshal.GetLastWin32Error());
                        if (!parent.WaitForExit(10000)) return 1;
                        try { using (var child = Process.GetProcessById(childPid)) { if (!child.WaitForExit(5000)) return 1; } }
                        catch (ArgumentException) { }
                        File.WriteAllText(Path.Combine(testRoot, "cancel-test.log"), "Native installer cancellation tree test passed (Windows Job Object).\n");
                        return 0;
                    } finally { CloseHandle(job); }
                }
            }
            catch (Exception exc) { File.WriteAllText(Path.Combine(testRoot, "cancel-test.log"), exc.ToString()); return 1; }
        }
        if (args.Length == 1 && args[0] == "--self-test") {
            using (var window = new Launcher()) {
                var info = window.Command("--self-test");
                using (var process = new Process()) {
                    process.StartInfo = info;
                    var stdout = new StringBuilder(); var stderr = new StringBuilder();
                    process.OutputDataReceived += delegate(object s, DataReceivedEventArgs e) { if(e.Data != null) stdout.AppendLine(e.Data); };
                    process.ErrorDataReceived += delegate(object s, DataReceivedEventArgs e) { if(e.Data != null) stderr.AppendLine(e.Data); };
                    process.Start(); process.BeginOutputReadLine(); process.BeginErrorReadLine(); process.WaitForExit();
                    File.WriteAllText(Path.Combine(window.root, "portable-test.log"), stdout.ToString() + stderr.ToString(), Encoding.UTF8);
                    return process.ExitCode;
                }
            }
        }
        bool installGpu = args.Length == 1 && args[0] == "--install-gpu";
        if (args.Length != 0 && !installGpu) return 2;
        Application.EnableVisualStyles(); Application.SetCompatibleTextRenderingDefault(false);
        Application.Run(new Launcher(installGpu)); return 0;
    }
}
