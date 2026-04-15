# uncompyle6 version 3.9.3
# Python bytecode version base 3.7.0
# Decompiled from: Python 3.9.6 (default, Nov 11 2024, 03:15:38) 
# [Clang 16.0.0 (clang-1600.0.26.6)]
# Embedded file name: MoryandCpuTset.py
import sys, subprocess, threading, warnings
import shutil
import matplotlib.pyplot as plt
from datetime import datetime
import time, os, re
QT_API = None
try:
    from PyQt5 import QtWidgets, QtCore
    from PyQt5.QtGui import QPixmap
    from PyQt5.QtCore import pyqtSignal as Signal
    QT_API = "PyQt5"
except ImportError:
    from PySide6 import QtWidgets, QtCore
    from PySide6.QtGui import QPixmap
    from PySide6.QtCore import Signal
    QT_API = "PySide6"
warnings.filterwarnings("ignore")

if os.name == "nt":
    CREATE_NO_WINDOW = 134217728
else:
    CREATE_NO_WINDOW = 0


def run_subprocess(command, **kwargs):
    kwargs.setdefault("creationflags", CREATE_NO_WINDOW)
    return subprocess.run(command, **kwargs)


def popen_subprocess(command, **kwargs):
    kwargs.setdefault("creationflags", CREATE_NO_WINDOW)
    return subprocess.Popen(command, **kwargs)

class MonitorApp(QtWidgets.QWidget):
    log_signal = Signal(str)
    cpu_plot_signal = Signal(str)
    memory_plot_signal = Signal(str)
    monitoring_finished_signal = Signal()

    def __init__(self):
        self.monitoring = False
        self.trace_thread = None
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("cpu&ram监测 @yw0107340")
        self.setGeometry(100, 100, 800, 600)
        self.package_name_input = QtWidgets.QComboBox(self)
        self.package_name_input.addItems([
         "com.hihonor.mms"])
        self.package_name_input.setCurrentText("com.hihonor.mms")
        self.cpu_threshold_input = QtWidgets.QComboBox(self)
        self.cpu_threshold_input.addItems([str(i) for i in range(0, 101)])
        self.cpu_threshold_input.setCurrentText("5")
        self.memory_threshold_input = QtWidgets.QComboBox(self)
        self.memory_threshold_input.addItems([str(i) for i in range(0, 501, 50)])
        self.memory_threshold_input.setCurrentText("100")
        self.duration_input = QtWidgets.QComboBox(self)
        self.duration_input.addItems([str(i) for i in range(1, 25)])
        self.duration_input.setCurrentText("1")
        self.start_button = QtWidgets.QPushButton("开始监测", self)
        self.start_button.clicked.connect(self.start_monitoring)
        self.output_area = QtWidgets.QTextEdit(self)
        self.output_area.setReadOnly(True)
        self.chart_label = QtWidgets.QLabel(self)
        self.chart_label.setFixedSize(800, 400)
        self.chart_label2 = QtWidgets.QLabel(self)
        self.chart_label2.setFixedSize(800, 400)
        chart_layout = QtWidgets.QHBoxLayout()
        chart_layout.addWidget(self.chart_label)
        chart_layout.addWidget(self.chart_label2)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.package_name_input)
        layout.addWidget(QtWidgets.QLabel("CPU 占用阈值（%）:"))
        layout.addWidget(self.cpu_threshold_input)
        layout.addWidget(QtWidgets.QLabel("内存骤降监测值（MB）:"))
        layout.addWidget(self.memory_threshold_input)
        layout.addWidget(QtWidgets.QLabel("工具执行时间（小时）:"))
        layout.addWidget(self.duration_input)
        layout.addWidget(self.start_button)
        layout.addWidget(self.output_area)
        layout.addLayout(chart_layout)
        self.setLayout(layout)
        self.log_signal.connect(self.output_area.append)
        self.cpu_plot_signal.connect(self.display_plot_cpu)
        self.memory_plot_signal.connect(self.display_plot_ram)
        self.monitoring_finished_signal.connect(lambda: self.start_button.setEnabled(True))

    def start_monitoring(self):
        if self.monitoring:
            self.log_signal.emit("监控已在运行中。")
            return
        if shutil.which("adb") is None:
            self.log_signal.emit("未检测到 adb，请先安装 Android platform-tools 并加入 PATH。")
            return
        package_name = self.package_name_input.currentText()
        cpu_threshold = float(self.cpu_threshold_input.currentText())
        memory_threshold = float(self.memory_threshold_input.currentText())
        duration_hours = float(self.duration_input.currentText())
        self.monitoring = True
        self.start_button.setEnabled(False)
        self.log_signal.emit(f"开始监控应用: {package_name}")
        self.monitor_thread = threading.Thread(target=(self.monitor_app), args=(
         package_name, cpu_threshold, memory_threshold, duration_hours), daemon=True)
        self.monitor_thread.start()

    def closeEvent(self, event):
        self.monitoring = False
        super().closeEvent(event)

    def disable_screen_lock(self):
        run_subprocess(['adb', 'shell', 'svc', 'power', 'stayon', 'true'])

    def pull_systrace_file(self, output_file, script_dir):
        cpuinfo_dir = os.path.join(script_dir, "cpuinfo")
        os.makedirs(cpuinfo_dir, exist_ok=True)
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        local_file = os.path.join(cpuinfo_dir, f"trace_output_{timestamp_str}")
        run_subprocess(["adb", "pull", output_file, local_file])

    def delete_systrace_file(self, output_file):
        run_subprocess(["adb", "shell", "rm", output_file])

    def run_atrace(self, duration, script_dir):
        while self.monitoring:
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"/sdcard/trace_output_{timestamp_str}"
            atrace_command = (
                f"atrace -z -b 8192 video gfx input view wm rs hal "
                f"sched freq idle irq -t {duration} > {output_file}"
            )
            run_subprocess(["adb", "shell", atrace_command], stdout=(subprocess.PIPE), text=True, errors="ignore")
            self.pull_systrace_file(output_file, script_dir=script_dir)
            time.sleep(2)
            self.delete_systrace_file(output_file)

    def dump_android_heap(self, package_name):
        try:
            pid_result = run_subprocess(['adb', 'shell', 'ps -ef | grep', package_name], stdout=(subprocess.PIPE), text=True,
              errors="ignore")
            if pid_result.returncode != 0:
                self.log_signal.emit("无法获取应用的 PID，请确保应用正在运行。")
                return
            else:
                for line in pid_result.stdout.strip().splitlines():
                    if package_name in line and "grep" not in line:
                        pid_match = re.search("\\b(\\d+)\\b", line)
                        if pid_match:
                            pid = pid_match.group(1)
                            self.log_signal.emit(f"找到的 PID: {pid}")
                            break
                else:
                    self.log_signal.emit("未能找到有效的 PID。")
                    return

                run_subprocess(["adb", "shell", "am", "dumpheap", pid, "/data/local/tmp/heapdump.hprof"])
                if getattr(sys, "frozen", False):
                    current_dir = os.path.dirname(os.path.abspath(sys.executable))
                else:
                    current_dir = os.path.dirname(os.path.abspath(__file__))
            raminfo_dir = os.path.join(current_dir, "raminfo")
            os.makedirs(raminfo_dir, exist_ok=True)
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(raminfo_dir, f"heapdump_{current_time}.hprof")
            run_subprocess(["adb", "pull", "/data/local/tmp/heapdump.hprof", output_file])
            self.log_signal.emit(f"Heap Dump 已成功生成并保存到 {output_file}")
        except Exception as e:
            try:
                self.log_signal.emit(f"发生错误: {e}")
            finally:
                e = None
                del e

    def save_memory_plot(self, time_stamps, total_pss_usage, drop_times, avg_memory, file_path, package_name):
        plt.figure(figsize=(10, 5))
        plt.xlabel("Time")
        plt.ylabel("Memory Usage (MB)", color="b")
        plt.plot([ts.timestamp() for ts in time_stamps], total_pss_usage, marker="o", linestyle="-", color="b", markersize=5)
        plt.title("Memory Usage Over Time")
        plt.grid(True)
        plt.xticks(rotation=45)
        for drop_time in drop_times:
            plt.axvline(x=(drop_time.timestamp()), color="r", linestyle="--")
            plt.text((drop_time.timestamp()), (max(total_pss_usage)), (drop_time.strftime("%H:%M:%S")), rotation=45, verticalalignment="bottom",
              color="r")

        plt.figtext(0.15, 0.01, f"Average Memory Usage: {avg_memory:.2f} MB", fontsize=10, ha="left")
        plt.savefig(file_path)
        plt.close()
        self.memory_plot_signal.emit(file_path)

    def save_cpu_plot(self, time_stamps, cpu_usage, high_cpu_times, avg_cpu, file_path):
        plt.figure(figsize=(10, 5))
        plt.xlabel("Time")
        plt.ylabel("CPU Usage (%)", color="r")
        plt.plot([ts.timestamp() for ts in time_stamps], cpu_usage, marker="x", linestyle="-", color="r", markersize=5)
        plt.title("CPU Usage Over Time")
        plt.grid(True)
        plt.xticks(rotation=45)
        for high_cpu_time in high_cpu_times:
            plt.axvline(x=(high_cpu_time.timestamp()), color="b", linestyle="--")
            plt.text((high_cpu_time.timestamp()), (max(cpu_usage)), (high_cpu_time.strftime("%H:%M:%S")), rotation=45, verticalalignment="bottom",
              color="b")

        plt.figtext(0.15, 0.01, f"Average CPU Usage: {avg_cpu:.2f} %", fontsize=10, ha="left")
        plt.savefig(file_path)
        plt.close()
        self.cpu_plot_signal.emit(file_path)

    def display_plot_cpu(self, file_path):
        pixmap = QPixmap(file_path)
        self.chart_label.setPixmap(pixmap.scaled(self.chart_label.size(), QtCore.Qt.KeepAspectRatio))

    def display_plot_ram(self, file_path):
        pixmap = QPixmap(file_path)
        self.chart_label2.setPixmap(pixmap.scaled(self.chart_label2.size(), QtCore.Qt.KeepAspectRatio))

    def monitor_app(self, package_name, cpu_threshold, memory_threshold, duration_hours):
        try:
            time_stamps = []
            total_pss_usage = []
            cpu_usage = []
            drop_times = []
            high_cpu_times = []
            start_time = time.time()
            self.disable_screen_lock()
            if getattr(sys, "frozen", False):
                script_dir = os.path.dirname(os.path.abspath(sys.executable))
            else:
                script_dir = os.path.dirname(os.path.abspath(__file__))
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            memory_plot_file_path = os.path.join(script_dir, f"memory_usage_over_time_{timestamp_str}.png")
            cpu_plot_file_path = os.path.join(script_dir, f"cpu_usage_over_time_{timestamp_str}.png")
            end_time = start_time + duration_hours * 60 * 60
            previous_pss_mb = None
            self.trace_thread = threading.Thread(target=(self.run_atrace), args=(10, script_dir), daemon=True)
            self.trace_thread.start()
            while self.monitoring and time.time() < end_time:
                current_time = datetime.now()
                total_pss_kb = self.get_process_memory_info(package_name)
                total_pss_mb = total_pss_kb / 1024
                cpu_percent = self.get_process_cpu_info(package_name)
                if previous_pss_mb is not None:
                    if previous_pss_mb - total_pss_mb > memory_threshold:
                        self.dump_android_heap(package_name)
                        drop_times.append(current_time)
                previous_pss_mb = total_pss_mb
                if cpu_percent > cpu_threshold:
                    high_cpu_times.append(current_time)
                time_stamps.append(current_time)
                total_pss_usage.append(total_pss_mb)
                cpu_usage.append(cpu_percent)
                if len(time_stamps) % 360 == 0:
                    avg_memory = sum(total_pss_usage[-360:]) / 360
                    avg_cpu = sum(cpu_usage[-360:]) / 360
                    self.log_signal.emit(f"Average Memory Usage (last hour): {avg_memory:.2f} MB")
                    self.log_signal.emit(f"Average CPU Usage (last hour): {avg_cpu:.2f} %")
                avg_memory = sum(total_pss_usage) / len(total_pss_usage) if total_pss_usage else 0
                avg_cpu = sum(cpu_usage) / len(cpu_usage) if cpu_usage else 0
                self.save_memory_plot(time_stamps, total_pss_usage, drop_times, avg_memory, memory_plot_file_path, package_name)
                self.save_cpu_plot(time_stamps, cpu_usage, high_cpu_times, avg_cpu, cpu_plot_file_path)
                execution_time = datetime.now().strftime("%H:%M:%S")
                elapsed_time = time.time() - start_time
                elapsed_hours = round(elapsed_time / 3600, 2)
                self.log_signal.emit(f"Execution time: {execution_time}, Elapsed time: {elapsed_hours:.2f} hours")
                time.sleep(10)
        finally:
            self.monitoring = False
            self.monitoring_finished_signal.emit()

    def get_process_memory_info(self, package_name):
        result = run_subprocess(['adb', 'shell', 'dumpsys', 'meminfo', package_name], stdout=(subprocess.PIPE))
        output = result.stdout.decode("utf-8")
        memory_info = {}
        for line in output.split("\n"):
            if "TOTAL PSS" in line:
                parts = line.split()
                memory_info["TOTAL PSS"] = int(parts[2])
                break

        return memory_info.get("TOTAL PSS", 0)

    def get_process_cpu_info(self, package_name):
        """
        计算某进程的cpu使用率
        100*( processCpuTime2 – processCpuTime1) / (totalCpuTime2 – totalCpuTime1) (按100%计算，如果是多核情况下还需乘以cpu的个数);
        cpukel cpu几核
        pid 进程id
        """
        try:
            cpukel = self.get_cpu_cores()
            pid = str(self.get_pid(package_name))
            processCpuTime1 = self.processCpuTime(pid)
            time.sleep(1)
            processCpuTime2 = self.processCpuTime(pid)
            processCpuTime3 = processCpuTime2 - processCpuTime1
            totalCpuTime1 = self.totalCpuTime()
            time.sleep(1)
            totalCpuTime2 = self.totalCpuTime()
            totalCpuTime3 = (totalCpuTime2 - totalCpuTime1) * cpukel
            cpu = 100 * processCpuTime3 / totalCpuTime3
            return cpu
        except Exception as e:
            try:
                self.log_signal.emit(f"发生错误: {e}")
                return 0
            finally:
                e = None
                del e

    def get_cpu_cores(self):
        result = run_subprocess(['adb', 'shell', 'grep -c ^processor /proc/cpuinfo'], stdout=(subprocess.PIPE),
          stderr=(subprocess.PIPE),
          text=True)
        if result.returncode == 0:
            return int(result.stdout.strip())
        self.log_signal.emit(f"Error getting CPU cores:{result.stderr}")
        return 1

    def get_pid(self, pkg_name):
        result = run_subprocess(["adb", "shell", "pidof", pkg_name], stdout=(subprocess.PIPE),
          stderr=(subprocess.PIPE),
          text=True)
        if result.returncode == 0 and result.stdout.strip():
            return int(result.stdout.strip())
        print("Error getting PID for package:", pkg_name, result.stderr)
        return

    def processCpuTime(self, pid):
        """

        pid     进程号
        utime   该任务在用户态运行的时间，单位为jiffies
        stime   该任务在核心态运行的时间，单位为jiffies
        cutime  所有已死线程在用户态运行的时间，单位为jiffies
        cstime  所有已死在核心态运行的时间，单位为jiffies
        """
        utime = stime = cutime = cstime = 0
        p = popen_subprocess(["adb", "shell", "cat", f"/proc/{pid}/stat"], stdout=(subprocess.PIPE), stderr=(subprocess.PIPE),
          stdin=(subprocess.PIPE))
        output, err = p.communicate()
        res = output.split()
        if len(res) < 17:
            return 0
        utime = res[13].decode()
        stime = res[14].decode()
        cutime = res[15].decode()
        cstime = res[16].decode()
        result = int(utime) + int(stime) + int(cutime) + int(cstime)
        return result

    def totalCpuTime(self):
        user = nice = system = idle = iowait = irq = softirq = 0
        p = popen_subprocess(["adb", "shell", "cat", "/proc/stat"], stdout=(subprocess.PIPE), stderr=(subprocess.PIPE),
          stdin=(subprocess.PIPE))
        output, err = p.communicate()
        res = output.split()
        if len(res) < 8:
            return 0
        for info in res:
            if info.decode() == "cpu":
                user = res[1].decode()
                nice = res[2].decode()
                system = res[3].decode()
                idle = res[4].decode()
                iowait = res[5].decode()
                irq = res[6].decode()
                softirq = res[7].decode()
                result = int(user) + int(nice) + int(system) + int(idle) + int(iowait) + int(irq) + int(softirq)
                return result


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    ex = MonitorApp()
    ex.show()
    if QT_API == "PyQt5":
        sys.exit(app.exec_())
    sys.exit(app.exec())
