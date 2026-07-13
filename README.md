# IFC Viewer

一个基于浏览器的 IFC 3D 模型查看器。单文件 Python 服务：后端解析 IFC 并转换为 GLB，前端用 Three.js 交互查看，支持属性查看、按类别过滤、剖面裁切与 DXF 导出。

## 功能

- **3D 模型浏览** — Three.js 场景：左键旋转、右键平移、滚轮缩放
- **Category 过滤** — 左侧按构件类型（IfcWall / IfcSlab 等）分组，可显示/隐藏
- **Category 批量选中** — 一键高亮该类型全部构件
- **单击属性查看** — 查看 GlobalId、Name、Property Sets 等
- **属性导出 XLSX** — 将构件属性表导出为 Excel（浏览器端 SheetJS）
- **交互式剖面** — 点击面设置剖切平面，拖动移动剖面
- **剖面 DXF 导出** — 剖切轮廓导出为 AutoCAD DXF（落在 XY 平面，方向已校正）

## 环境要求

- Python 3.10+（已在 Python 3.14 验证）
- 现代浏览器（Chrome / Edge / Firefox）

## 安装

```bash
pip install -r requirements.txt
```

依赖说明：

| 包 | 用途 |
|---|---|
| `ifcopenshell` | 解析 IFC 文件与几何 |
| `trimesh` | 网格处理、剖切求交、GLB 导出 |
| `numpy` | 数值与坐标变换 |
| `ezdxf` | 生成 DXF |

前端库（Three.js、SheetJS）通过 CDN 加载，无需本地安装。

## 启动

```bash
python server.py
# 或指定端口
python server.py 8080
```

浏览器打开：http://localhost:8080

点击 **Open IFC File** 上传 `.ifc` 即可。

## 使用说明

### 浏览与属性

1. 上传 IFC 后模型自动居中适配视角
2. 单击构件 → 右侧属性面板
3. 左侧 Category 面板可按类型隐藏 / 选中

### 导出属性

加载成功后点击 **Export XLSX**，下载构件属性表。

### 剖面与 DXF

1. 点击 **Section**，进入拾取模式
2. 点击模型某个面，建立剖切平面（半透明红色）
3. 在剖切平面上拖动可平移剖面
4. 点击 **DXF** 下载 `section.dxf`
5. 用 AutoCAD 打开：轮廓在 **XY 平面（Z=0）**，方向已按保留侧观察校正

再次点击 **Section** 可退出剖面模式。

## API

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/` | 返回内嵌前端页面 |
| `POST` | `/convert` | 上传原始 IFC 字节流 → JSON `{ glb: base64, props: [...] }` |
| `GET` | `/section-dxf?...` | 按剖切参数返回 DXF 文件 |

`/section-dxf` 查询参数：

- `nx, ny, nz` — 剖切平面法线
- `px, py, pz` — 剖切平面上一点
- `ox, oy, oz` — 模型场景偏移

## 技术栈

- **后端**：Python `http.server` + `ifcopenshell` + `trimesh` + `ezdxf`
- **前端**：原生 HTML/JS + Three.js（ES module CDN）+ SheetJS（XLSX）

## 文件结构

```
ifc-viewer/
├── server.py           # 单文件：后端服务 + 前端页面
├── requirements.txt    # Python 依赖
└── README.md
```

## 说明与限制

- 几何转换依赖 `ifcopenshell.geom`，复杂模型首次加载可能较慢
- 剖面求交基于内存中的 mesh 缓存（本次会话上传的模型）
- DXF 导出的是剖切线框，不是带填充的 2D 图纸
- 大模型可能占用较多内存；建议先用中小型 IFC 验证流程

## License

按仓库现有协议使用；若未指定，默认仅供学习与内部使用。
