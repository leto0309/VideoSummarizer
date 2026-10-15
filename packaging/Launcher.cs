using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Text;
using System.Text.RegularExpressions;
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
    string lang;
    static readonly string[] Languages = { "zh-CN", "zh-TW", "en" };
    static readonly string[] LanguageNames = { "简体中文", "繁體中文", "English" };
    // Simplified Chinese, Traditional Chinese (OpenCC s2twp of the first, as the page converts), English.
    static readonly Dictionary<string, string[]> Messages = new Dictionary<string, string[]> {
        { "title_gpu", new[] { "VideoSummarizer - 可选 GPU 加速",
            "VideoSummarizer - 可選 GPU 加速",
            "VideoSummarizer - Optional GPU acceleration" } },
        { "checking", new[] { "正在检查本机环境…",
            "正在檢查本機環境…",
            "Checking this computer…" } },
        { "cancel_setup", new[] { "取消配置",
            "取消配置",
            "Cancel setup" } },
        { "still_starting", new[] { "启动仍在进行，请等待下方进度完成后再关闭。",
            "啟動仍在進行，請等待下方進度完成後再關閉。",
            "Startup is still in progress; wait for the progress below to finish before closing." } },
        { "job_failed", new[] { "无法建立可取消的安装进程组，已停止本次配置。",
            "無法建立可取消的安裝程序組，已停止本次配置。",
            "Could not create a cancellable installer process group; setup was stopped." } },
        { "confirm_cancel", new[] { "停止本次配置？已安装的依赖、模型和摘要会保留，可稍后重试。",
            "停止本次配置？已安裝的依賴、模型和摘要會保留，可稍後重試。",
            "Stop this setup? Installed dependencies, models and summaries are kept, and you can retry later." } },
        { "stopping", new[] { "正在停止本次安装进程…",
            "正在停止本次安裝程序…",
            "Stopping the installer…" } },
        { "no_python", new[] { "找不到内置 Python，请完整解压 ZIP，保留 runtime 文件夹。",
            "找不到內建 Python，請完整解壓 ZIP，保留 runtime 資料夾。",
            "The bundled Python is missing. Extract the whole ZIP and keep the runtime folder." } },
        { "check_failed", new[] { "环境检查失败，请完整重新解压或查看日志。",
            "環境檢查失敗，請完整重新解壓或檢視日誌。",
            "The environment check failed. Extract the ZIP again completely, or check the logs." } },
        { "gpu_before_setup", new[] { "请先打开 VideoSummarizer.exe 完成首次配置，再运行 install-gpu.bat。",
            "請先開啟 VideoSummarizer.exe 完成首次配置，再執行 install-gpu.bat。",
            "Open VideoSummarizer.exe and complete first-time setup before running install-gpu.bat." } },
        { "consent_gpu", new[] { "可选 GPU 加速将下载 CUDA 运行库，可能超过 1 GB，总时限 20 分钟。\n\n只安装到本软件文件夹。取消或失败后，CPU 模式仍可使用。请先等待摘要任务完成。\n\n是否允许下载？",
            "可選 GPU 加速將下載 CUDA 執行庫，可能超過 1 GB，總時限 20 分鐘。\n\n只安裝到本軟體資料夾。取消或失敗後，CPU 模式仍可使用。請先等待摘要任務完成。\n\n是否允許下載？",
            "Optional GPU acceleration downloads the CUDA runtime, possibly over 1 GB, with a 20-minute overall limit.\n\nIt is installed only in this program folder. After cancelling or a failure, CPU mode still works. Wait for any running summary to finish first.\n\nAllow the download?" } },
        { "consent_setup", new[] { "首次使用需下载尚未内置的免费依赖、工具与本机 AI 模型，建议预留 15 GB 空间。已内置的 Whisper / Ollama 会直接使用。\n\n默认跳过可选 CUDA 库，先使用 CPU 转录；GPU 加速可稍后通过 install-gpu.bat 单独安装。\n\n仅写入本软件文件夹，不安装系统 Python、不改全局 PATH，不使用付费 API 或 cloud。\n\n选择的语言也用于网页，之后可在网页上更改。\n\n是否允许下载？",
            "首次使用需下載尚未內建的免費依賴、工具與本機 AI 模型，建議預留 15 GB 空間。已內建的 Whisper / Ollama 會直接使用。\n\n預設跳過可選 CUDA 庫，先使用 CPU 轉錄；GPU 加速可稍後透過 install-gpu.bat 單獨安裝。\n\n僅寫入本軟體資料夾，不安裝系統 Python、不改全域性 PATH，不使用付費 API 或 cloud。\n\n選擇的語言也用於網頁，之後可在網頁上更改。\n\n是否允許下載？",
            "First use downloads the free dependencies, tools and local AI models that are not bundled; keep about 15 GB free. A bundled Whisper / Ollama is used directly.\n\nThe optional CUDA libraries are skipped and transcription starts on the CPU; GPU acceleration can be installed later with install-gpu.bat.\n\nEverything is written only to this program folder: no system Python, no global PATH change, no paid API or cloud.\n\nThe language you choose is also used for the web page; you can change it there later.\n\nAllow the downloads?" } },
        { "language_label", new[] { "语言：",
            "語言：",
            "Language:" } },
        { "allow", new[] { "允许下载",
            "允許下載",
            "Allow downloads" } },
        { "deny", new[] { "取消",
            "取消",
            "Cancel" } },
        { "setup_declined", new[] { "已取消首次配置，尚未下载。",
            "已取消首次配置，尚未下載。",
            "First-time setup was cancelled; nothing was downloaded." } },
        { "installing_gpu", new[] { "正在安装可选 GPU 加速，可随时取消…",
            "正在安裝可選 GPU 加速，可隨時取消…",
            "Installing optional GPU acceleration; you can cancel at any time…" } },
        { "setting_up", new[] { "首次配置中，可查看下载进度或取消…",
            "首次配置中，可檢視下載進度或取消…",
            "First-time setup in progress; follow the download progress below, or cancel…" } },
        { "starting", new[] { "正在启动本机服务…",
            "正在啟動本機服務…",
            "Starting the local service…" } },
        { "cancelled", new[] { "已取消配置。现有模型和摘要保留，可稍后重新打开。",
            "已取消配置。現有模型和摘要保留，可稍後重新開啟。",
            "Setup cancelled. Existing models and summaries are kept; open the program again later." } },
        { "gpu_done", new[] { "GPU 库安装完成，兼容性需通过转录确认。可关闭此窗口。",
            "GPU 庫安裝完成，相容性需透過轉錄確認。可關閉此視窗。",
            "The GPU libraries are installed; only a transcription confirms compatibility. You can close this window." } },
        { "opened", new[] { "已打开网页，可关闭此窗口。背景服务会继续运行。",
            "已開啟網頁，可關閉此視窗。背景服務會繼續執行。",
            "The web page is open; you can close this window. The background service keeps running." } },
        { "gpu_failed", new[] { "GPU 安装未完成，仍可使用 CPU。请查看下方错误。",
            "GPU 安裝未完成，仍可使用 CPU。請檢視下方錯誤。",
            "GPU installation did not finish; the CPU still works. See the error below." } },
        { "start_failed_detail", new[] { "启动失败：请查看下方错误，修正后重新双击启动。",
            "啟動失敗：請檢視下方錯誤，修正後重新雙擊啟動。",
            "Start failed: see the error below, fix it and double-click again." } },
        { "start_failed", new[] { "启动失败",
            "啟動失敗",
            "Start failed" } },
    };
    string T(string key) { return Messages[key][Array.IndexOf(Languages, lang)]; }

    // The page-language preference (language-settings.json); the first-run window lets the user choose it.
    string SavedLanguage() {
        try {
            var match = Regex.Match(File.ReadAllText(Path.Combine(root, "language-settings.json")),
                "\"ui_language\"\\s*:\\s*\"(zh-CN|zh-TW|en)\"");
            if (match.Success) return match.Groups[1].Value;
        } catch (IOException) { } catch (UnauthorizedAccessException) { }
        return Languages[0];
    }

    void ApplyLanguage() {
        Text = gpuMode ? T("title_gpu") : "VideoSummarizer";
        cancel.Text = T("cancel_setup");
    }
    string Python { get { return Path.Combine(root, "runtime", "python.exe"); } }
    string Script { get { return Path.Combine(root, "desktop_launcher.py"); } }

    Launcher(bool installGpu = false) {
        gpuMode = installGpu; lang = SavedLanguage();
        Width = 780; Height = 500;
        StartPosition = FormStartPosition.CenterScreen;
        status.Text = T("checking"); status.Dock = DockStyle.Top; status.Height = 38;
        output.Multiline = true; output.ReadOnly = true; output.ScrollBars = ScrollBars.Both;
        output.WordWrap = false; output.Dock = DockStyle.Fill;
        output.Font = new Font("Consolas", 10);
        cancel.Dock = DockStyle.Bottom; cancel.Height = 34; cancel.Enabled = false;
        cancel.Click += delegate { CancelWorker(false); };
        Controls.Add(output); Controls.Add(status); Controls.Add(cancel);
        ApplyLanguage();
        Shown += delegate { Begin(); };
        FormClosing += delegate(object sender, FormClosingEventArgs e) {
            if (busy) {
                e.Cancel = true;
                if (canCancel) CancelWorker(true);
                else MessageBox.Show(this, T("still_starting"), Text);
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

    static IntPtr CreateInstallerJob(Process process, string failure) {
        var job = CreateJobObject(IntPtr.Zero, null);
        if (job == IntPtr.Zero) throw new Win32Exception(Marshal.GetLastWin32Error());
        if (!AssignProcessToJobObject(job, process.Handle)) {
            int error = Marshal.GetLastWin32Error();
            CloseHandle(job);
            if (!process.HasExited) process.Kill();
            throw new Win32Exception(error, failure);
        }
        // No KILL_ON_JOB_CLOSE: successful setup may leave owned services running.
        return job;
    }

    void CancelWorker(bool close) {
        if (!busy || !canCancel || worker == null || worker.HasExited) return;
        if (MessageBox.Show(this, T("confirm_cancel"),
            Text, MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes) return;
        cancelled = true; closeWhenDone = close; cancel.Enabled = false;
        status.Text = T("stopping");
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
        info.EnvironmentVariables["VIDEOSUMMARIZER_LANGUAGE"] = lang;
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
            if (!File.Exists(Python)) throw new Exception(T("no_python"));
            Directory.CreateDirectory(Path.Combine(root, "logs"));
            // Verify write access before downloading or starting background processes.
            File.AppendAllText(Path.Combine(root, "logs", "desktop.log"), DateTime.Now.ToString("s") + " start\n");
            int code;
            using (var check = Process.Start(Command("--check"))) { check.WaitForExit(); code = check.ExitCode; }
            if (code != 0 && code != 10) throw new Exception(T("check_failed"));
            if (gpuMode && code == 10) throw new Exception(T("gpu_before_setup"));
            bool agreed = !(code == 10 || gpuMode) || (gpuMode
                ? MessageBox.Show(this, T("consent_gpu"), Text, MessageBoxButtons.YesNo, MessageBoxIcon.Question) == DialogResult.Yes
                : AskSetupConsent());
            if (!agreed) { status.Text = T("setup_declined"); return; }
            busy = true;
            canCancel = code == 10 || gpuMode; cancel.Enabled = canCancel;
            status.Text = gpuMode ? T("installing_gpu") : code == 10 ? T("setting_up") : T("starting");
            worker = new Process(); worker.StartInfo = Command(gpuMode ? "--install-gpu" : code == 10 ? "--setup --language " + lang : "");
            worker.EnableRaisingEvents = true;
            worker.OutputDataReceived += delegate(object s, DataReceivedEventArgs e) { Add(e.Data); };
            worker.ErrorDataReceived += delegate(object s, DataReceivedEventArgs e) { Add(e.Data); };
            worker.Exited += delegate {
                if (IsDisposed) return;
                BeginInvoke(new Action(delegate {
                    busy = false;
                    if (installJob != IntPtr.Zero) { CloseHandle(installJob); installJob = IntPtr.Zero; }
                    cancel.Enabled = false;
                    status.Text = cancelled ? T("cancelled") : worker.ExitCode == 0 ?
                        (gpuMode ? T("gpu_done") : T("opened")) :
                        (gpuMode ? T("gpu_failed") : T("start_failed_detail"));
                    File.AppendAllText(Path.Combine(root, "logs", "desktop.log"), output.Text, Encoding.UTF8);
                    if (closeWhenDone) Close();
                }));
            };
            worker.Start();
            if (canCancel) installJob = CreateInstallerJob(worker, T("job_failed"));
            worker.BeginOutputReadLine(); worker.BeginErrorReadLine();
        } catch (Exception exc) { busy = false; status.Text = T("start_failed"); Add(exc.Message); }
    }

    // First-run consent with a language choice; the choice applies at once and is saved by --setup --language.
    bool AskSetupConsent() {
        using (var dialog = new Form()) {
            dialog.FormBorderStyle = FormBorderStyle.FixedDialog; dialog.MinimizeBox = false; dialog.MaximizeBox = false;
            dialog.ShowInTaskbar = false; dialog.StartPosition = FormStartPosition.CenterParent;
            dialog.ClientSize = new Size(580, 360);
            var message = new Label(); message.SetBounds(16, 16, 548, 270);
            var caption = new Label(); caption.SetBounds(16, 320, 100, 24); caption.TextAlign = ContentAlignment.MiddleLeft;
            var choice = new ComboBox(); choice.DropDownStyle = ComboBoxStyle.DropDownList; choice.SetBounds(120, 320, 150, 24);
            choice.Items.AddRange(LanguageNames); choice.SelectedIndex = Array.IndexOf(Languages, lang);
            var allow = new Button(); allow.SetBounds(316, 316, 140, 30); allow.DialogResult = DialogResult.Yes;
            var deny = new Button(); deny.SetBounds(464, 316, 100, 30); deny.DialogResult = DialogResult.No;
            Action refresh = delegate {
                lang = Languages[choice.SelectedIndex]; ApplyLanguage(); status.Text = T("checking");
                dialog.Text = Text; message.Text = T("consent_setup"); caption.Text = T("language_label");
                allow.Text = T("allow"); deny.Text = T("deny");
            };
            choice.SelectedIndexChanged += delegate { refresh(); };
            refresh();
            dialog.Controls.AddRange(new Control[] { message, caption, choice, allow, deny });
            dialog.AcceptButton = allow; dialog.CancelButton = deny;
            return dialog.ShowDialog(this) == DialogResult.Yes;
        }
    }

    [STAThread] static int Main(string[] args) {
        if (args.Length == 1 && args[0] == "--self-test-cancel") {
            var testRoot = AppDomain.CurrentDomain.BaseDirectory;
            try {
                var info = new ProcessStartInfo(Path.Combine(testRoot, "runtime", "python.exe"),
                    "-s -u -c \"import subprocess,sys,time;p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)']);print(p.pid,flush=True);time.sleep(60)\"");
                info.UseShellExecute = false; info.CreateNoWindow = true; info.RedirectStandardOutput = true;
                using (var parent = Process.Start(info)) {
                    var job = CreateInstallerJob(parent, "Native installer job could not be created.");
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
