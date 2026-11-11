import customtkinter as ctk
import psutil
import GPUtil
import time
import datetime
import subprocess
import threading

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
ALTURA = 680 # Altura aumentada para caber os cards de temperatura
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

# --- Variáveis e Thread de Temperatura ---
temp_cpu_atual = "N/A"
temp_cpu_float = 0.0

def atualizar_temp_cpu_background():
    global temp_cpu_atual, temp_cpu_float
    while True:
        try:
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            output = subprocess.check_output(
                ["powershell", "-NoProfile", "-Command", 
                 "(Get-WmiObject MSAcpi_ThermalZoneTemperature -Namespace 'root/wmi').CurrentTemperature"],
                startupinfo=si, text=True, stderr=subprocess.DEVNULL
            ).strip()
            
            if output:
                temp_c = (int(output) / 10.0) - 273.15
                temp_cpu_float = temp_c
                temp_cpu_atual = f"{temp_c:.1f}°C"
            else:
                temp_cpu_atual = "N/A"
                temp_cpu_float = 0.0
        except:
            temp_cpu_atual = "N/A"
            temp_cpu_float = 0.0
        
        time.sleep(5)

threading.Thread(target=atualizar_temp_cpu_background, daemon=True).start()

# --- Função Auxiliar de Formatação de Rede ---
def formatar_tamanho(tamanho_em_bytes):
    for unidade in ['B/s', 'KB/s', 'MB/s', 'GB/s']:
        if tamanho_em_bytes < 1024.0:
            return f"{tamanho_em_bytes:.1f} {unidade}"
        tamanho_em_bytes /= 1024.0
    return f"{tamanho_em_bytes:.1f} TB/s"

# --- Função Auxiliar para Mini Cards ---
def criar_mini_card(master, nome_padrao, mostrar_barra=True):
    frame = ctk.CTkFrame(master, corner_radius=8)
    frame.pack(pady=4, padx=10, fill="x")
    
    lbl_info = ctk.CTkLabel(frame, text=f"{nome_padrao}: --", font=("Arial", 12, "bold"))
    lbl_info.pack(pady=(5, 5 if not mostrar_barra else 0), padx=10, anchor="w")
    
    pb = None
    if mostrar_barra:
        pb = ctk.CTkProgressBar(frame, height=8)
        pb.pack(pady=(5, 8), padx=10, fill="x")
        pb.set(0)
    
    return lbl_info, pb

# Função de cores dinâmicas para temperatura
def atualizar_cor_temp(pb, valor_temp):
    if valor_temp < 65:
        pb.configure(progress_color=["#1f6aa5", "#1f538d"]) # Azul padrão
    elif valor_temp < 80:
        pb.configure(progress_color="#e67e22") # Laranja (Atenção)
    else:
        pb.configure(progress_color="#C62828") # Vermelho (Perigo)

# --- Interface ---
titulo = ctk.CTkLabel(janela, text="Sistema", font=("Arial", 14, "bold"))
titulo.pack(pady=(10, 0))

lbl_uptime = ctk.CTkLabel(janela, text="Ligado há: --", font=("Arial", 11, "italic"), text_color="gray")
lbl_uptime.pack(pady=(0, 5))

lbl_cpu, pb_cpu = criar_mini_card(janela, "CPU (Uso)")
lbl_temp_cpu, pb_temp_cpu = criar_mini_card(janela, "Temp CPU")

lbl_gpu, pb_gpu = criar_mini_card(janela, "GPU (Uso)")
lbl_temp_gpu, pb_temp_gpu = criar_mini_card(janela, "Temp GPU")

lbl_ram, pb_ram = criar_mini_card(janela, "RAM")
lbl_disco, pb_disco = criar_mini_card(janela, "Disco")
lbl_rede, _ = criar_mini_card(janela, "Rede", mostrar_barra=False) 
lbl_bateria, pb_bateria = criar_mini_card(janela, "Bateria")

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

# --- Variáveis globais de controle ---
last_disk_io = psutil.disk_io_counters()
last_net_io = psutil.net_io_counters()
last_time = time.time()
psutil.cpu_percent(interval=None)

# --- Função de Atualização Contínua ---
def atualizar_dados():
    global last_disk_io, last_net_io, last_time, temp_cpu_atual, temp_cpu_float

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

    # CPU (Uso e Temp)
    uso_cpu = psutil.cpu_percent(interval=None)
    lbl_cpu.configure(text=f"CPU: {uso_cpu}%")
    pb_cpu.set(uso_cpu / 100)

    lbl_temp_cpu.configure(text=f"Temp CPU: {temp_cpu_atual}")
    pb_temp_cpu.set(min(temp_cpu_float / 100.0, 1.0)) # Máximo visual de 100°C
    atualizar_cor_temp(pb_temp_cpu, temp_cpu_float)

    # GPU (Uso e Temp)
    gpus = GPUtil.getGPUs()
    if gpus:
        gpu = gpus[0]
        lbl_gpu.configure(text=f"GPU: {gpu.load * 100:.1f}%")
        pb_gpu.set(gpu.load)

        lbl_temp_gpu.configure(text=f"Temp GPU: {gpu.temperature:.1f}°C")
        pb_temp_gpu.set(min(gpu.temperature / 100.0, 1.0))
        atualizar_cor_temp(pb_temp_gpu, gpu.temperature)
    else:
        lbl_gpu.configure(text="GPU: N/A")
        pb_gpu.set(0)
        lbl_temp_gpu.configure(text="Temp GPU: N/A")
        pb_temp_gpu.set(0)

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

    # BATERIA
    bateria = psutil.sensors_battery()
    if bateria:
        percentual = bateria.percent
        conectado = " (Tomada)" if bateria.power_plugged else ""
        lbl_bateria.configure(text=f"Bateria: {percentual:.1f}%{conectado}")
        pb_bateria.set(percentual / 100)
        
        if percentual <= 20 and not bateria.power_plugged:
            pb_bateria.configure(progress_color="#C62828") 
        else:
            pb_bateria.configure(progress_color=["#1f6aa5", "#1f538d"])
    else:
        lbl_bateria.configure(text="Bateria: Não detectada")
        pb_bateria.set(0)

    last_time = current_time
    janela.after(1000, atualizar_dados)

# Inicia o loop
atualizar_dados()
janela.mainloop()