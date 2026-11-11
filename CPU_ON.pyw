import customtkinter as ctk
import psutil
import time
import datetime
import subprocess
import threading
import wmi
import pythoncom

# --- Configuração Inicial ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

janela = ctk.CTk()
janela.title("Monitor")

try:
    janela.iconbitmap("icone.ico")
except:
    pass

# --- Configuração de Tamanho e Posição ---
LARGURA = 220
ALTURA = 700
largura_tela = janela.winfo_screenwidth()
pos_x = largura_tela - LARGURA - 20
pos_y = 50 

janela.geometry(f"{LARGURA}x{ALTURA}+{pos_x}+{pos_y}")
janela.attributes('-alpha', 0.85)
janela.overrideredirect(True)

# --- Funções para Mover a Janela (Drag & Drop) ---
def iniciar_arrasto(event):
    janela.start_x = event.x
    janela.start_y = event.y

def arrastar(event):
    x = janela.winfo_x() - janela.start_x + event.x
    y = janela.winfo_y() - janela.start_y + event.y
    janela.geometry(f"+{x}+{y}")

janela.bind('<ButtonPress-1>', iniciar_arrasto)
janela.bind('<B1-Motion>', arrastar)

# --- Botão de Fechar Customizado ---
def fechar_app():
    janela.destroy()

btn_fechar = ctk.CTkButton(janela, text="X", width=25, height=25, 
                           corner_radius=5, fg_color="#C62828", hover_color="#b71c1c",
                           command=fechar_app)
btn_fechar.place(x=LARGURA - 30, y=5)

# --- Variáveis Globais de Sensores ---
temp_cpu_atual = "N/A"
temp_cpu_float = 0.0
temp_gpu_atual = "N/A"
temp_gpu_float = 0.0
uso_gpu_global = "N/A"

# --- Thread: Temperaturas (OpenHardwareMonitor) ---
def atualizar_temperaturas_ohm():
    global temp_cpu_atual, temp_cpu_float, temp_gpu_atual, temp_gpu_float
    pythoncom.CoInitialize() # Necessário para rodar WMI em threads
    
    while True:
        try:
            w = wmi.WMI(namespace=r"root\OpenHardwareMonitor")
            sensores = w.Sensor(SensorType="Temperature")
            
            cpu_temps = []
            gpu_temps = []
            
            for sensor in sensores:
                identificador = str(sensor.Identifier).lower()
                if "cpu" in identificador:
                    cpu_temps.append(float(sensor.Value))
                elif "gpu" in identificador:
                    gpu_temps.append(float(sensor.Value))
            
            if cpu_temps:
                temp_cpu_float = max(cpu_temps)
                temp_cpu_atual = f"{temp_cpu_float:.1f}°C"
            else:
                temp_cpu_atual = "N/A"
            
            if gpu_temps:
                temp_gpu_float = max(gpu_temps)
                temp_gpu_atual = f"{temp_gpu_float:.1f}°C"
            else:
                temp_gpu_atual = "N/A"
                
        except Exception:
            temp_cpu_atual = "N/A"
            temp_gpu_atual = "N/A"
        
        time.sleep(2)

threading.Thread(target=atualizar_temperaturas_ohm, daemon=True).start()

# --- Thread: Uso de GPU Universal (PowerShell) ---
def atualizar_uso_gpu_background():
    global uso_gpu_global
    cmd_gpu = '(((Get-Counter "\\GPU Engine(*engtype_3D)\\Utilization Percentage" -ErrorAction SilentlyContinue).CounterSamples | Measure-Object -Property CookedValue -Sum).Sum)'
    
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    
    while True:
        try:
            output = subprocess.check_output(
                ["powershell", "-NoProfile", "-Command", cmd_gpu],
                startupinfo=si, text=True, stderr=subprocess.DEVNULL
            ).strip()
            
            if output:
                valor = float(output.replace(',', '.'))
                uso_gpu_global = min(valor, 100.0) # Garante que não passe de 100%
            else:
                uso_gpu_global = "N/A"
        except Exception:
            uso_gpu_global = "N/A"
            
        time.sleep(1.5)

threading.Thread(target=atualizar_uso_gpu_background, daemon=True).start()

# --- Função Auxiliar de Formatação de Rede ---
def formatar_tamanho(tamanho_em_bytes):
    for unidade in ['B/s', 'KB/s', 'MB/s', 'GB/s']:
        if tamanho_em_bytes < 1024.0:
            return f"{tamanho_em_bytes:.1f} {unidade}"
        tamanho_em_bytes /= 1024.0
    return f"{tamanho_em_bytes:.1f} TB/s"

# --- Interface Base ---
titulo = ctk.CTkLabel(janela, text="Sistema", font=("Arial", 14, "bold"))
titulo.pack(pady=(10, 0))

lbl_uptime = ctk.CTkLabel(janela, text="Ligado há: --", font=("Arial", 11, "italic"), text_color="gray")
lbl_uptime.pack(pady=(0, 5))

# Container para os cards suportar ocultação (grid)
frame_cards = ctk.CTkFrame(janela, fg_color="transparent")
frame_cards.pack(fill="both", expand=True)
frame_cards.grid_columnconfigure(0, weight=1)

# --- Função Auxiliar para Mini Cards (Agora com Grid) ---
def criar_mini_card(master, nome_padrao, linha, mostrar_barra=True):
    frame = ctk.CTkFrame(master, corner_radius=8)
    frame.grid(row=linha, column=0, pady=4, padx=10, sticky="ew")
    
    lbl_info = ctk.CTkLabel(frame, text=f"{nome_padrao}: --", font=("Arial", 12, "bold"))
    lbl_info.pack(pady=(5, 5 if not mostrar_barra else 0), padx=10, anchor="w")
    
    pb = None
    if mostrar_barra:
        pb = ctk.CTkProgressBar(frame, height=8)
        pb.pack(pady=(5, 8), padx=10, fill="x")
        pb.set(0)
    
    return frame, lbl_info, pb

def atualizar_cor_temp(pb, valor_temp):
    if valor_temp < 65:
        pb.configure(progress_color=["#1f6aa5", "#1f538d"])
    elif valor_temp < 80:
        pb.configure(progress_color="#e67e22")
    else:
        pb.configure(progress_color="#C62828")

# --- Criação dos Cards ---
frm_cpu, lbl_cpu, pb_cpu = criar_mini_card(frame_cards, "CPU (Uso)", 0)
frm_temp_cpu, lbl_temp_cpu, pb_temp_cpu = criar_mini_card(frame_cards, "Temp CPU", 1)
frm_gpu, lbl_gpu, pb_gpu = criar_mini_card(frame_cards, "GPU (Uso)", 2)
frm_temp_gpu, lbl_temp_gpu, pb_temp_gpu = criar_mini_card(frame_cards, "Temp GPU", 3)
frm_ram, lbl_ram, pb_ram = criar_mini_card(frame_cards, "RAM", 4)
frm_disco, lbl_disco, pb_disco = criar_mini_card(frame_cards, "Disco", 5)
frm_rede, lbl_rede, _ = criar_mini_card(frame_cards, "Rede", 6, mostrar_barra=False) 
frm_bateria, lbl_bateria, pb_bateria = criar_mini_card(frame_cards, "Bateria", 7)

# Toggle de Visualização (Tema)
frame_opcoes = ctk.CTkFrame(janela, fg_color="transparent")
frame_opcoes.pack(pady=5, fill="x", padx=10)

ctk.CTkLabel(frame_opcoes, text="Tema:", font=("Arial", 11)).pack(side="left", padx=5)

def mudar_tema(novo_tema):
    if novo_tema == "Escuro":
        ctk.set_appearance_mode("dark")
    else:
        ctk.set_appearance_mode("light")

menu_tema = ctk.CTkOptionMenu(frame_opcoes, values=["Escuro", "Claro"], 
                              command=mudar_tema, width=80, height=24)
menu_tema.pack(side="right", padx=5)

# --- Variáveis globais de controle do loop ---
last_disk_io = psutil.disk_io_counters()
last_net_io = psutil.net_io_counters()
last_time = time.time()
psutil.cpu_percent(interval=None)

# --- Função de Atualização Contínua (Main Thread) ---
def atualizar_dados():
    global last_disk_io, last_net_io, last_time

    current_time = time.time()
    delta_time = current_time - last_time

    # UPTIME
    uptime_segundos = current_time - psutil.boot_time()
    td = datetime.timedelta(seconds=uptime_segundos)
    dias = td.days
    horas, resto = divmod(td.seconds, 3600)
    minutos, segundos = divmod(resto, 60)
    
    if dias > 0:
        lbl_uptime.configure(text=f"Ligado há: {dias}d {horas}h {minutos}m")
    else:
        lbl_uptime.configure(text=f"Ligado há: {horas}h {minutos}m {segundos}s")

    # CPU (Uso)
    uso_cpu = psutil.cpu_percent(interval=None)
    lbl_cpu.configure(text=f"CPU: {uso_cpu}%")
    pb_cpu.set(uso_cpu / 100)

    # TEMP CPU (Oculta se não lido)
    if temp_cpu_atual == "N/A":
        frm_temp_cpu.grid_remove()
    else:
        frm_temp_cpu.grid()
        lbl_temp_cpu.configure(text=f"Temp CPU: {temp_cpu_atual}")
        pb_temp_cpu.set(min(temp_cpu_float / 100.0, 1.0))
        atualizar_cor_temp(pb_temp_cpu, temp_cpu_float)

    # GPU USO (Oculta se não lido)
    if uso_gpu_global == "N/A":
        frm_gpu.grid_remove()
    else:
        frm_gpu.grid()
        lbl_gpu.configure(text=f"GPU: {uso_gpu_global:.1f}%")
        pb_gpu.set(uso_gpu_global / 100.0)

    # TEMP GPU (Oculta se não lido)
    if temp_gpu_atual == "N/A":
        frm_temp_gpu.grid_remove()
    else:
        frm_temp_gpu.grid()
        lbl_temp_gpu.configure(text=f"Temp GPU: {temp_gpu_atual}")
        pb_temp_gpu.set(min(temp_gpu_float / 100.0, 1.0))
        atualizar_cor_temp(pb_temp_gpu, temp_gpu_float)

    # RAM
    ram = psutil.virtual_memory()
    lbl_ram.configure(text=f"RAM: {ram.percent}%")
    pb_ram.set(ram.percent / 100)

    # DISCO
    current_disk_io = psutil.disk_io_counters()
    if current_disk_io and last_disk_io and delta_time > 0:
        delta_read_time = current_disk_io.read_time - last_disk_io.read_time
        delta_write_time = current_disk_io.write_time - last_disk_io.write_time
        
        active_time_seconds = (delta_read_time + delta_write_time) / 1000
        uso_disco = (active_time_seconds / delta_time) * 100
        uso_disco = min(uso_disco, 100.0)
        
        lbl_disco.configure(text=f"Disco: {uso_disco:.1f}%")
        pb_disco.set(uso_disco / 100)
        last_disk_io = current_disk_io

    # REDE
    current_net_io = psutil.net_io_counters()
    if current_net_io and last_net_io and delta_time > 0:
        down_speed = (current_net_io.bytes_recv - last_net_io.bytes_recv) / delta_time
        up_speed = (current_net_io.bytes_sent - last_net_io.bytes_sent) / delta_time
        lbl_rede.configure(text=f"Rede: ↓ {formatar_tamanho(down_speed)} | ↑ {formatar_tamanho(up_speed)}")
        last_net_io = current_net_io

    # BATERIA (Oculta se não detectada, ex: Desktops)
    bateria = psutil.sensors_battery()
    if bateria:
        frm_bateria.grid()
        percentual = bateria.percent
        conectado = " (Tomada)" if bateria.power_plugged else ""
        lbl_bateria.configure(text=f"Bateria: {percentual:.1f}%{conectado}")
        pb_bateria.set(percentual / 100)
        
        if percentual <= 20 and not bateria.power_plugged:
            pb_bateria.configure(progress_color="#C62828") 
        else:
            pb_bateria.configure(progress_color=["#1f6aa5", "#1f538d"])
    else:
        frm_bateria.grid_remove()

    last_time = current_time
    janela.after(1000, atualizar_dados)

# Inicia o loop
atualizar_dados()
janela.mainloop()