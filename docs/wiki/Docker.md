# Docker

## GPU-окружение

Проект поддерживает запуск в Docker-контейнере с GPU для Sionna ray-tracing.

### Dockerfile

Расположение: `docker/Dockerfile.gpu`

### Docker Compose

Файл: `docker-compose.gpu.yml`

```yaml
services:
  van3t-gpu:
    build:
      context: .
      dockerfile: docker/Dockerfile.gpu
    image: van3t-gpu:local
    working_dir: /workspace
    network_mode: host
    ipc: host
    shm_size: "8gb"
    gpus: all
    environment:
      HOME: /tmp/van3t-home
      NVIDIA_VISIBLE_DEVICES: all
      NVIDIA_DRIVER_CAPABILITIES: compute,utility,graphics
    volumes:
      - ./:/workspace
    stdin_open: true
    tty: true
```

### Запуск

```bash
# Сборка образа
docker compose -f docker-compose.gpu.yml build

# Запуск контейнера
docker compose -f docker-compose.gpu.yml run van3t-gpu

# Внутри контейнера — стандартная сборка и запуск
./sandbox_builder.sh
cd ns-3-dev
./ns3 configure --build-profile=optimized --enable-examples --enable-tests --disable-python --disable-werror
./ns3 build -j 2
```

### Требования

- Docker с поддержкой NVIDIA GPU (nvidia-docker2 или nvidia-container-toolkit)
- NVIDIA драйвер с поддержкой CUDA
- Минимум 8 GB shared memory (`shm_size: "8gb"`)

### Особенности

- `network_mode: host` — контейнер использует сеть хоста (для Sionna-сервера)
- `gpus: all` — доступ ко всем GPU
- Рабочая директория монтируется как `/workspace`
- `HOME` установлен в `/tmp/van3t-home` для изоляции

## V2X Emulator (опционально)

В `emulation-support/` находятся инструменты для V2X emulation:

| Компонент | Описание |
|---|---|
| `AMQP-client/` | AMQP клиент для обмена сообщениями |
| `PCAP-AMQP-relayer/` | Ретрансляция PCAP → AMQP |
| `UDP-AMQP-relayer/` | Ретрансляция UDP → AMQP |
| `enable_v2x_emulator.sh` | Скрипт включения V2X эмулятора |
| `ms-van3t-namespace-creator.sh` | Создание network namespace |

Активация:
```bash
./enable_v2x_emulator.sh
```
