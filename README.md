# IFC Viewer

一个基于浏览器的 IFC 3D 模型查看器，支持上传 `.ifc` 文件并在浏览器中交互查看建筑信息模型。

## 功能

- **3D 模型浏览** — 基于 Three.js，鼠标左键旋转、右键平移、滚轮缩放
- **Category 过滤** — 按构件类型分类，可一键显示/隐藏任意类型
- **Category 批量选中** — 点击 Select 高亮该类型全部构件
- **单击属性查看** — 点击任意构件查看 GlobalId、Name、Property Sets 等属性
- **属性面板固定高度滚动** — 属性过多时面板内滚轮翻阅

## 安装依赖

```bash
pip install ifcopenshell trimesh numpy
```

## 启动

```bash
python server.py
```

浏览器打开 `http://localhost:8080`，点击 **Open IFC File** 上传 `.ifc` 文件即可。

## 技术栈

- 后端：Python `http.server` + `ifcopenshell`（解析 IFC）+ `trimesh`（几何转换）
- 前端：原生 HTML/JS + Three.js 0.160（ES module，CDN 加载）

## 文件结构

```
ifc-viewer/
├── server.py    # 单文件，包含后端服务和前端页面
└── README.md
```
