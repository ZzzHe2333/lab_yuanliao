# lab_yuanliao

一个面向研发实验室的原料 / 化学品仓库管理系统。当前版本采用 **Vue 3 + Vite 前端、Python + FastAPI 后端、SQLite 本地数据库**，核心功能参考 ChemTrack 的业务思路重新实现，适合在 Windows 实验室内网中以源码方式运行。

> 参考项目：`ekjyotshinh/ChemTrack`。本项目不直接复制其 React Native / Go / Firestore 代码，而是按相同的化学品库存管理场景重新实现为 Vue + Python 架构。

## 当前功能

- 单账户模式：暂不提供登录、用户和权限系统
- 多仓库 / 多库区管理
- 原料增删改查
- 名称、CAS、批号、供应商搜索
- 仓库、状态、过期、低库存筛选
- 采购日期与到期日期
- 数量、单位与低库存阈值
- 房间 / 柜号 / 层号库位
- 品牌、供应商、批号、储存条件、备注
- SDS 文件上传、查看、删除
- 每条原料自动生成二维码
- 浏览器摄像头扫码查询（浏览器支持 `BarcodeDetector` 时可用）
- 原料二维码标签打印
- 首页库存 / 过期 / 低库存统计
- FastAPI 自动接口文档

## 数据目录

所有运行时数据统一保存在仓库根目录的：

```text
data/
├─ lab_yuanliao.db
├─ sds/
└─ qrcodes/
```

`data/` 已整体写入 `.gitignore`，**数据库、SDS 和二维码不会上传到 GitHub**。首次启动时后端会自动创建这些目录和 SQLite 数据库。

## 一键启动（Windows）

需要先安装：

- Python 3.11+
- Node.js LTS

然后双击根目录：

```text
start.bat
```

首次运行会自动：

1. 创建 `.venv`
2. 安装 Python 依赖
3. 安装 Vue / Vite 依赖
4. 启动 FastAPI（8000）
5. 启动 Vite（5173）
6. 打开浏览器

访问：

- 前端：`http://127.0.0.1:5173`
- 后端：`http://127.0.0.1:8000`
- API 文档：`http://127.0.0.1:8000/docs`

局域网内其他电脑访问时，将 `127.0.0.1` 换成运行此项目电脑的局域网 IP，例如 `http://192.168.1.20:5173`。

## 项目结构

```text
lab_yuanliao/
├─ backend/
│  ├─ app/
│  │  ├─ database.py
│  │  ├─ schemas.py
│  │  └─ main.py
│  ├─ requirements.txt
│  └─ run.py
├─ frontend/
│  ├─ src/
│  │  ├─ components/
│  │  ├─ views/
│  │  ├─ api.js
│  │  ├─ router.js
│  │  └─ style.css
│  ├─ index.html
│  ├─ package.json
│  └─ vite.config.js
├─ data/              # 运行后自动创建，不上传 Git
├─ start.bat
└─ .gitignore
```

## V1 与 ChemTrack 的对应关系

| ChemTrack | lab_yuanliao |
| --- | --- |
| React Native / Expo | Vue 3 / Vite Web |
| Go / Gin | Python / FastAPI |
| Firestore | SQLite |
| Google Cloud Storage | 本地 `data/` |
| School | Warehouse（仓库） |
| User / Admin / Master | 暂时移除，单账户全权限 |
| Chemical CRUD | 已实现 |
| SDS | 已实现 |
| QR Code | 已实现 |
| QR Scan | Web 摄像头扫码 + 手动 ID 查询 |
| Alerts | 过期 + 低库存统计/筛选 |

## 后续计划

- 原料入库 / 领用 / 退库流水
- 批次与容器级库存
- Excel 导入导出
- COA 文件
- 标签尺寸模板和批量打印
- 临期提醒
- 库存盘点
- 操作日志
- 后续再增加多账户与权限
