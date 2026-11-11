# 🖥️ Monitor de Sistema (Floating System Monitor)

Um widget de monitoramento de sistema minimalista, flutuante e de código aberto desenvolvido em Python. Ele fornece informações em tempo real sobre o uso de hardware e rede, com uma interface limpa feita em `customtkinter`.

Diferente de monitores travados a uma marca específica, este projeto é **Universal**, suportando leitura de uso e temperatura para placas de vídeo **NVIDIA, AMD e Intel**.

## ✨ Funcionalidades

- **Monitoramento Completo:** Uso de CPU, GPU, Memória RAM, Atividade de Disco, Tráfego de Rede e Status da Bateria.
- **Universal (Cross-Vendor GPU):** Compatível com qualquer placa de vídeo dedicada ou integrada no Windows (AMD, Intel, NVIDIA) através de contadores nativos do PowerShell.
- **Leitura Precisa de Temperatura:** Integração via WMI com o OpenHardwareMonitor para leituras reais e dinâmicas dos sensores térmicos.
- **UI Inteligente e Otimizada:** Sensores não detectados (ex: falta de bateria em um desktop ou software de temperatura fechado) são ocultados automaticamente da interface, mantendo o visual limpo.
- **Alta Performance:** Requisições pesadas (WMI e PowerShell) rodam em threads dedicadas (*background*), garantindo que a interface gráfica nunca congele ou apresente lentidão (Zero-Lag UI).
- **Personalizável:** Suporte a arrastar-e-soltar (*Drag & Drop*) pela tela, transparência inteligente e temas (Claro/Escuro).

---

## ⚙️ Pré-requisitos

Para que o monitor funcione corretamente (especialmente a leitura de temperaturas), você precisará de:

1. **Python 3.8+** instalado no sistema.
2. **OpenHardwareMonitor**: Este script consome os dados do servidor WMI gerado por ele.
   - Baixe gratuitamente em: [openhardwaremonitor.org](https://openhardwaremonitor.org/)
   - Extraia e execute o `OpenHardwareMonitor.exe`.
   - **Recomendação:** Vá em `Options` no aplicativo e marque as caixas `Run On Windows Startup` e `Minimize To Tray`.

---

## 🚀 Instalação e Execução

**1. Clone este repositório:**
```bash
git clone [https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git](https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git)
cd SEU_REPOSITORIO