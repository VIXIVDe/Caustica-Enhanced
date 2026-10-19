# Caustica Enhanced

**面向 Minecraft 26.2（Fabric）的 Vulkan 硬件路径追踪。**
让方块世界拥有真实的光：太阳、月亮、火把、云、雨、雾和水，按物理规则彼此照亮。

[English](README.md) · [宣传页与对比](docs/SHOWCASE.zh-CN.md) · [技术报告](docs/TECHNICAL_REPORT.zh-CN.md) · [构建说明](docs/BUILDING.zh-CN.md)

| | |
| --- | --- |
| 游戏环境 | Minecraft **26.2**、Fabric Loader ≥ 0.19.5、Fabric API、Java 25+ |
| 渲染器 | Vulkan 硬件光线追踪（加速结构、光追管线、ray query） |
| 许可证 | GPL-3.0-only（Caustica 原有文件保留 LGPL-3.0-or-later 声明） |

> **如实说明。** 本源码树能完整构建，66 个测试套件 / 231 个 Java 单元测试通过，着色器已离线编译并校验。**这一构建尚未在 GPU 或游戏内运行过。** 文档描述的是源码实现了什么，不对你机器上的画质或帧率作任何承诺。见[状态与限制](#状态与限制)。

## 这是什么

Caustica Enhanced 用光线追踪器取代 Minecraft 的世界渲染器：每个像素追踪主光线和多次反弹，再用 **NVIDIA DLSS Ray Reconstruction**，或 **NRD ReBLUR 加 DLSS / FSR / XeSS 超分**，把带噪结果还原成干净的画面。界面、方块和资源包保持原版，改变的只有光照。

它建立在开源项目 [Caustica](https://github.com/ComfyFluffy/Caustica)（ComfyFluffy）和 [Caustica-RTX](https://github.com/AriesAlex/Caustica-RTX)（AriesAlex）之上，并采用了 Radiance / MCVR、Prime PT 等项目的算法与资源（详见 [`mod/THIRD_PARTY_NOTICES.md`](mod/THIRD_PARTY_NOTICES.md)）。

## 亮点

- **光传输**：追踪漫反射、光泽反射与透射；玻璃、冰、水是带折射率的体。常开 RIS 发光体采样，可选 **ReSTIR DI**（大量小光源）和 **ReSTIR PT Enhanced**（全路径重采样）。
- **天空与天气**：Hillaire 大气散射、按物理尺寸绘制的日月、NASA 星图、极光、彩虹、Radiance 体积云、froxel 体积光、随天气变化的雾、湿润地面、折射雨滴，以及带紫色体积光柱的末地。
- **手中的光**：双手各一盏真实光源（火把、岩浆桶、荧石……），带真实阴影。
- **材质**：LabPBR 资源包、有界高度场视差、资源包 JSON 可覆写发光、折射率与色散。
- **水面**：性能 / 平衡 / 质量三档；质量档是 32 分量波谱，焦散与可见波纹来自同一波场。
- **远景地形**：把 Voxy 与 Distant Horizons 的地形转换为可追踪几何。
- **摄影机**：物理景深（f/1.4–f/22）、运动模糊、光圈衍射、镜头光斑、胶片颗粒；曝光以 cd/m² / EV100 计量。
- **显示**：ACES 2.0 输出，SDR 与 **HDR（PQ，500–4000 尼特）**，三种风格（原版 / GTA VI / Kodak 2383 风格）。
- **帧生成**：DLSS、FSR、XeSS 三种提供者（2×–4×，3×/4× 需要 RTX 50），配合 NVIDIA Reflex。
- **离线摄影**：分块累积，最高 7680 × 7680 像素；PNG / JPEG / TIFF / OpenEXR / HEIC / AVIF / JPEG XL，写入拍摄元数据。

完整且逐项经源码核对的功能描述见[技术报告](docs/TECHNICAL_REPORT.zh-CN.md)（28 节，只写已实现的内容）。与 Caustica-RTX、Radiance、Rethinking Voxels、SEUS PTGI、Minecraft RTX、BetterRTX 的对比见[宣传页](docs/SHOWCASE.zh-CN.md)。

## 运行要求

- 支持 Vulkan 光线追踪的 GPU 与驱动。NVIDIA RTX 可使用 DLSS Ray Reconstruction 与 DLSS 超分；其他厂商走 NRD ReBLUR + FSR 路线。
- Windows x64（随附的原生重建库为 Windows x64）。
- 在 Minecraft 视频设置中选择 **Vulkan** 图形后端。
- 显存：路径追踪很吃显存；仅 ReSTIR PT Enhanced 每个内部像素约需 736 字节（1920×1080 时约 1.42 GiB）。
- 可选：Voxy 0.2.19-beta（配合 Sodium）或 Distant Horizons ≥ 3.3.3 用于远景地形；HDR 输出需要 HDR 显示器。

## 安装

1. 配置好带 Fabric Loader 与 Fabric API 的 Minecraft 26.2，并在视频设置中选择 **Vulkan** 后端。
2. 把构建好的 Caustica Enhanced JAR 放进 `mods`（只放一个 Caustica 的 JAR）。构建好的 JAR 应放在本仓库的 **Releases** 下（JAR 约 400 MB，不存入 git）；自行构建见 [docs/BUILDING.zh-CN.md](docs/BUILDING.zh-CN.md)。
3. 首次进入世界时驱动会编译光追管线并显示进度面板，结果会被缓存。
4. 设置位于视频设置里的 **Caustica Enhanced** 页面。配置、缓存和导出文件在游戏目录内的 `Caustica Enhanced/` 文件夹中。

## 文档

| 文档 | 用途 |
| --- | --- |
| [docs/TECHNICAL_REPORT.zh-CN.md](docs/TECHNICAL_REPORT.zh-CN.md) · [English](docs/TECHNICAL_REPORT.md) | 渲染器实现了什么（详细，不含路线图） |
| [docs/SHOWCASE.zh-CN.md](docs/SHOWCASE.zh-CN.md) · [English](docs/SHOWCASE.md) | 面向用户的介绍，以及与其他项目的对比 |
| [docs/BUILDING.zh-CN.md](docs/BUILDING.zh-CN.md) · [English](docs/BUILDING.md) | 工具链、仓库中没有的内容、构建命令 |
| [mod/THIRD_PARTY_NOTICES.md](mod/THIRD_PARTY_NOTICES.md) | 第三方代码、算法、SDK 与许可边界 |
| [mod/docs/](mod/docs) | 开发笔记：发布验证、离线摄影、性能采集、Voxy 兼容等 |
| [docs/VERIFICATION.zh-CN.md](docs/VERIFICATION.zh-CN.md) · [English](docs/VERIFICATION.md) | 构建验证了什么（以及没有证明什么） |

## 仓库结构

```
Caustica-Enhanced/
├── mod/        Gradle 根目录：Java 源码、Slang 着色器、C++ 桥接、资源、Python 资源工具
├── docs/       技术报告、宣传页、构建说明
├── devtools/   验证工具、辅助脚本、本地构建代理（Windows）
└── scripts/    维护者工作区使用的离线构建封装
```

厂商 SDK、Voxy / Distant Horizons 的 JAR、星图二进制、照片编码器压缩包和发布 JAR **有意不放进仓库**；各自从哪里获得见 [docs/BUILDING.zh-CN.md](docs/BUILDING.zh-CN.md)。

## 状态与限制

- 这一构建只做过编译和单元测试；没有 GPU 运行，没有游戏内运行，也没有公布任何性能数据。
- 帧生成提高的是呈现帧数，不是模拟或追踪速度；多倍帧生成的呈现仍属实验性质。
- 视差是有界高度场，不是真正位移的几何体。远景地形仅限于 Voxy / Distant Horizons 提供的数据。
- ReSTIR PT 显存占用大；复用是近似的；froxel 分辨率有限。
- GTA VI 与 Kodak 2383 风格是艺术化诠释，不是获得授权或实测的复刻。
- 仅支持 Minecraft **26.2 Java 版**，不支持基岩版。

## 许可证

组合作品采用 **GPL-3.0-only**（[`LICENSE`](LICENSE)）；Caustica 原有文件保留 LGPL-3.0-or-later 声明（[`mod/LICENSE.md`](mod/LICENSE.md)、[`mod/COPYING.LESSER`](mod/COPYING.LESSER)、[`mod/MCVR-LICENSE.md`](mod/MCVR-LICENSE.md)）。第三方组件保留各自条款。NVIDIA、Intel、AMD、Minecraft 等名称属于各自所有者；本项目与它们无隶属或背书关系。
