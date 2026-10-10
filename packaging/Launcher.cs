using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Text;
using System.Windows.Forms;

class Launcher : Form {
    readonly string root = AppDomain.CurrentDomain.BaseDirectory;
    readonly TextBox output = new TextBox();
    readonly Label status = new Label();
    Process worker;
    bool busy;
    string Python { get { return Path.Combine(root, "runtime", "python.exe"); } }
    string Script { get { return Path.Combine(root, "desktop_launcher.py"); } }

    Launcher() {
        Text = "VideoSummarizer"; Width = 780; Height = 500;
        StartPosition = FormStartPosition.CenterScreen;
        status.Text = "正在檢查本機環境…"; status.Dock = DockStyle.Top; status.Height = 38;
        output.Multiline = true; output.ReadOnly = true; output.ScrollBars = ScrollBars.Both;
        output.WordWrap = false; output.Dock = DockStyle.Fill;
        output.Font = new Font("Consolas", 10);
        Controls.Add(output); Controls.Add(status);
        Shown += delegate { Begin(); };
        FormClosing += delegate(object sender, FormClosingEventArgs e) {
            if (busy) {
                MessageBox.Show(this, "配置或啟動仍在進行，請等待下方進度完成後再關閉。", Text);
                e.Cancel = true;
            }
        };
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
            if (!File.Exists(Python)) throw new Exception("找不到內置 Python，請完整解壓 ZIP，保留 runtime 資料夾。");
            Directory.CreateDirectory(Path.Combine(root, "logs"));
            // Verify write access before downloading or starting background processes.
            File.AppendAllText(Path.Combine(root, "logs", "desktop.log"), DateTime.Now.ToString("s") + " 啟動\n");
            int code;
            using (var check = Process.Start(Command("--check"))) { check.WaitForExit(); code = check.ExitCode; }
            if (code != 0 && code != 10) throw new Exception("環境檢查失敗，請完整重新解壓或查看日誌。");
            if (code == 10 && MessageBox.Show(this,
                "首次使用需下載尚未內置的免費影片/語音依賴、工具與本機 AI 模型，約需數 GB 流量，建議預留 15 GB。已內置的 Whisper / Ollama 會直接使用。\n\n僅寫入本軟體資料夾，不安裝系統 Python、不改全域 PATH，不使用付費 API 或 cloud。\n\n是否允許下載？",
                Text, MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes) {
                status.Text = "已取消首次配置，尚未下載。"; return;
            }
            busy = true;
            status.Text = code == 10 ? "首次配置中，請保持此視窗開啟…" : "正在啟動本機服務…";
            worker = new Process(); worker.StartInfo = Command(code == 10 ? "--setup" : "");
            worker.EnableRaisingEvents = true;
            worker.OutputDataReceived += delegate(object s, DataReceivedEventArgs e) { Add(e.Data); };
            worker.ErrorDataReceived += delegate(object s, DataReceivedEventArgs e) { Add(e.Data); };
            worker.Exited += delegate {
                if (IsDisposed) return;
                BeginInvoke(new Action(delegate {
                    busy = false;
                    status.Text = worker.ExitCode == 0 ? "已開啟網頁，可關閉此視窗。背景服務會繼續運行。" : "啟動失敗：請查看下方錯誤，修正後重新雙擊啟動。";
                    File.AppendAllText(Path.Combine(root, "logs", "desktop.log"), output.Text, Encoding.UTF8);
                }));
            };
            worker.Start(); worker.BeginOutputReadLine(); worker.BeginErrorReadLine();
        } catch (Exception exc) { busy = false; status.Text = "啟動失敗"; Add(exc.Message); }
    }

    [STAThread] static int Main(string[] args) {
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
        if (args.Length != 0) return 2;
        Application.EnableVisualStyles(); Application.SetCompatibleTextRenderingDefault(false);
        Application.Run(new Launcher()); return 0;
    }
}
