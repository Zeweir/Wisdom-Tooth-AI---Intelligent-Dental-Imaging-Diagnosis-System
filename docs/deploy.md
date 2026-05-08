# 服务器部署文档

本文档面向“项目已经拷到一台有公网 IP 的 Linux 服务器上”的场景。

当前仓库已经调整为可直接通过 `docker compose up -d --build` 部署，但前提是先准备好根目录 `.env`。

当前默认部署拓扑：

- `gateway` 对外暴露 `80`、`443`、`3001`、`3002`
- `frontend`、`backend`、`logto`、`postgres`、`redis`、`minio` 默认只绑定本机或容器网络
- 浏览器访问应用统一走 `https://公网IP/`

## 一、部署前准备

服务器建议至少具备：

- Docker Engine
- Docker Compose Plugin
- 2 核 CPU / 4 GB 内存起步
- 能访问 Docker Hub

如果你要启用真实推理，还需要额外确认：

- `models/dental-yolo.pt` 已存在
- `OLLAMA_BASE_URL` 指向的服务从服务器可访问

如果服务器在中国大陆，建议一开始就把 Docker、`apt`、`pip`、`npm` 的拉取源切到国内镜像，否则最容易卡在构建阶段。

## 二、初始化环境变量

在仓库根目录执行：

```bash
cp .env.example .env
```

然后至少修改下面这些值：

```env
PUBLIC_SCHEME=https
PUBLIC_HOST=你的公网IP

VITE_LOGTO_APP_ID=先留空，等 Logto 里创建 SPA 应用后再填
ALLOWED_ORIGINS=https://你的公网IP,http://你的公网IP,https://127.0.0.1,http://127.0.0.1,https://localhost,http://localhost,http://127.0.0.1:5173,http://localhost:5173
POSTGRES_PASSWORD=改成强密码
LOGTO_POSTGRES_PASSWORD=改成强密码
MINIO_ROOT_PASSWORD=改成强密码
```

如果是国内服务器，建议额外把下面这些值改掉：

```env
APT_MIRROR=https://mirrors.tuna.tsinghua.edu.cn/debian
APT_SECURITY_MIRROR=https://mirrors.tuna.tsinghua.edu.cn/debian-security
PIP_INDEX_URL=https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple
TORCH_INDEX_URL=https://download.pytorch.org/whl/cpu
NPM_REGISTRY=https://registry.npmmirror.com/
```

说明：

- `APT_MIRROR` / `APT_SECURITY_MIRROR` 会在后端镜像构建时改写 Debian 源
- `PIP_INDEX_URL` / `PIP_EXTRA_INDEX_URL` 会用于安装 `requirements.txt`
- `TORCH_INDEX_URL` 单独控制 `torch` / `torchvision` 下载地址
- `NPM_REGISTRY` 会用于前端 `npm ci`

如果 `TORCH_INDEX_URL` 仍然慢，先不要动它，优先观察是不是 Docker Hub、Debian 源或 PyPI 先超时

然后先生成自签证书：

```bash
chmod +x deploy/nginx/generate-self-signed-cert.sh
./deploy/nginx/generate-self-signed-cert.sh 你的公网IP
```

脚本会生成：

- `deploy/nginx/certs/server.crt`
- `deploy/nginx/certs/server.key`

如果浏览器或系统需要信任它，请把 `server.crt` 导入到受信任根证书列表。

端口暴露默认策略如下：

- `80`：对公网开放，自动跳转到 `443`
- `443`：对公网开放，作为应用统一 HTTPS 入口
- `3001`：对公网开放，作为 Logto OIDC HTTPS 入口
- `3002`：默认也对公网开放，作为 Logto Admin HTTPS 入口，初始化完成后建议改回 `127.0.0.1`
- PostgreSQL / Redis / MinIO / Backend：默认只绑定 `127.0.0.1`

如果你希望初始化完成后关闭 Logto 管理台公网访问，把：

```env
GATEWAY_LOGTO_ADMIN_BIND_HOST=127.0.0.1
```

改好后重新执行一次 `docker compose up -d` 即可。

## 三、首次启动 Logto

第一次部署建议先只启动 Logto 相关服务：

```bash
docker compose up -d logto-postgres logto
```

访问：

- OIDC 服务：`https://你的公网IP:3001`
- 管理台：`https://你的公网IP:3002`

在 Logto 管理台中完成以下配置：

1. 创建一个 `SPA Application`
2. Redirect URI 填 `https://你的公网IP/callback`
3. Post sign-out redirect URI 填 `https://你的公网IP/`
4. 创建 API Resource：`https://api.wisdom-tooth-ai.local`
5. 创建 scopes：
   - `read:images`
   - `upload:images`
   - `review:reports`
   - `finalize:reports`
6. 创建角色：
   - `radiologist`
   - `doctor`
   - `chief_doctor`
7. 给角色分配 scopes
8. 给测试用户分配角色

完成后，把 SPA App ID 写回根目录 `.env`：

```env
VITE_LOGTO_APP_ID=你的Logto SPA App ID
```

## 四、完整启动项目

执行：

```bash
docker compose up -d --build
```

说明：

- 后端容器启动时会自动执行 `alembic upgrade head`
- 前端镜像会在构建阶段读取根目录 `.env` 中的 `VITE_*` 变量
- `gateway` 会把 `80` 跳转到 `443`
- `gateway` 会把 `443` 端口的 `/`、`/api`、`/ws` 统一转发到前端和后端
- `gateway` 会把 `3001`、`3002` 作为独立 HTTPS 入口分别转发到 Logto OIDC 和 Logto Admin
- 不需要额外暴露后端给公网

## 五、访问地址

启动成功后：

- 前端：`https://你的公网IP/`
- 后端健康检查：`http://127.0.0.1:8000/health`
- Logto OIDC：`https://你的公网IP:3001`
- Logto Admin：`https://你的公网IP:3002`
- Swagger：`http://127.0.0.1:8000/docs`

如果你通过 SSH 登录服务器，也可以本机检查：

```bash
curl http://127.0.0.1:8000/health
docker compose ps
docker compose logs -f backend frontend logto celery-worker
```

## 六、生产建议

上线前建议至少做这几件事：

1. 修改所有默认密码，尤其是 PostgreSQL、Logto PostgreSQL、MinIO。
2. 初始化完成后收紧 `3002` 管理台访问，至少改成仅本机可访问。
3. 不要把 `5173`、`5432`、`5433`、`6379`、`8000`、`9000`、`9001` 开到公网安全组。
4. 当前方案使用自签证书，浏览器首次访问会有证书警告；要消除告警，需要把 `server.crt` 导入客户端受信任根证书列表。
5. 如果服务器访问不到外部 Ollama，把 `OLLAMA_ENABLED=false`，避免分析任务长时间超时。
6. 如果没有 YOLO 权重，把 `YOLO_ENABLED=false`。

## 七、常见问题

### 1. 页面能打开，但点登录后失败

优先检查：

- `.env` 里的 `PUBLIC_HOST` 是否是真实公网 IP
- `deploy/nginx/certs/server.crt` 和 `server.key` 是否已经生成
- Logto 里的 Redirect URI 是否和 `https://公网IP/callback` 完全一致
- `VITE_LOGTO_APP_ID` 是否已经填好

如果改过 `.env` 里的 `VITE_*` 变量，需要重新构建前端：

```bash
docker compose up -d --build frontend
```

### 2. 后端接口 401，提示 issuer 不匹配

优先检查：

- `PUBLIC_HOST` 是否变了但容器没重建
- `docker compose.yml` 生成的 `LOGTO_ENDPOINT` 和 `LOGTO_ISSUER` 是否与 Logto 实际公网地址一致
- 当前浏览器是否已经信任自签证书；如果没有，先手动接受证书风险页

通常重新执行一次：

```bash
docker compose up -d --build backend celery-worker logto frontend
```

即可。

### 3. 上传后分析一直不完成

优先检查：

- `docker compose logs -f celery-worker`
- `OLLAMA_BASE_URL` 是否从服务器可达
- `YOLO_MODEL_PATH` 对应文件是否存在

如果你当前只是验证部署链路，建议先：

```env
OLLAMA_ENABLED=false
YOLO_ENABLED=false
```

这样系统会回退到内置 mock 结果，更容易先把整条链路跑通。
