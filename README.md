# IFC Viewer

基于浏览器的 IFC 3D 模型查看器。单文件 Python 服务：后端解析 IFC 并转换为 GLB，前端 Three.js 交互查看。支持多模型加载、模型树管理、按类别过滤/选中、属性查看、交互式剖面与 DXF 导出。

## 功能

- **3D 模型浏览** — 左键旋转、右键平移、滚轮缩放
- **多模型支持** — Open IFC 加载首个模型，Append IFC 追加更多模型
- **模型树** — 左侧面板显示所有已加载模型，可展开查看各模型的 Category 子节点
- **模型切换** — 点击模型名切换激活模型，Category 面板自动更新
- **Category 过滤/选中** — 模型树中直接控制 Category 的显示/隐藏和批量选中
- **属性查看** — 单击构件查看 GlobalId、Name、Property Sets 等
- **XLSX 导出** — 构件属性表导出为 Excel
- **交互式剖面** — 点击面设置剖切平面，拖动移动，Section 按钮切换
- **DXF 导出** — 剖切轮廓导出为 AutoCAD DXF（XY 平面，方向已校正）
- **品牌 Logo** — 浏览器标签页 icon 和视口左上角 logo 叠加

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

## 使用说明

### 模型加载

- **Open IFC File** — 加载第一个 IFC 模型（若已有模型则先刷新页面）
- **Append IFC** — 在当前场景中追加新的 IFC 模型（加载第一个后出现）

### 模型树

左侧 **Models** 面板：

- 点击 ▶ 展开/折叠该模型的 Category 子节点
- 点击 👁 切换模型整体可见性
- 点击模型名 — 激活该模型，Category 面板同步更新
- 子节点中 👁 控制该 Category 显示/隐藏，**Sel** 批量选中

### 属性查看

- 单击 3D 视图中的构件 → 右侧属性面板弹出
- 只在当前激活模型中生效

### XLSX 导出

加载模型后点击 **Export XLSX**，下载所有构件属性表。

### 剖面与 DXF

1. 点击 **Section** → 拾取模式
2. 点击模型某个面 → 建立剖切平面（半透明红色）
3. 拖动剖切面平移
4. 点击 **DXF** 下载 `section.dxf`
5. 用 AutoCAD 打开：轮廓在 **XY 平面（Z=0）**，方向已校正

再次点击 **Section** 退出剖面模式。

## API

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/` | 返回内嵌前端页面 |
| `GET` | `/webicon.png`、`/favicon.png` | 返回品牌图标 |
| `POST` | `/convert` | 上传 IFC 字节流 → `{ glb: base64, props: [...] }` |
| `POST` | `/convert?append=1` | 追加模式：新模型 mesh 并入剖面缓存 |
| `GET` | `/section-dxf?nx=...&ny=...&nz=...&px=...&py=...&pz=...&ox=...&oy=...&oz=...` | 返回剖切轮廓 DXF |

## 文件结构

```
ifc-viewer/
├── server.py           # 单文件：后端服务 + 前端页面
├── requirements.txt    # Python 依赖
├── README.md
└── logo/
    └── az.png          # 品牌图标
```

## 说明与限制

- 几何转换依赖 `ifcopenshell.geom`，复杂模型首次加载可能较慢
- 剖面求交基于内存中的 mesh 缓存（本次会话上传的所有模型）
- DXF 导出的是剖切线框，不是带填充的 2D 图纸
- 多模型追加后，剖面 DXF 包含所有模型的剖切轮廓
- 大模型可能占用较多内存；建议先用中小型 IFC 验证
