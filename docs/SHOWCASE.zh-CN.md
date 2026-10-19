# Caustica Enhanced

### 为 Minecraft 26.2 打造的 Vulkan 硬件路径追踪渲染器

> 让方块世界拥有真实的光：太阳、月亮、火把、云、雨、雾、水面，全部按物理规则互相照亮。
> 客户端模组 · Fabric · GPL-3.0-only

[English](SHOWCASE.md) · [技术报告](TECHNICAL_REPORT.zh-CN.md) · [构建说明](BUILDING.zh-CN.md)

---

## 一分钟了解

Caustica Enhanced 替换 Minecraft 26.2 的世界渲染：用 Vulkan 光线追踪硬件追踪真实光路，再用 NVIDIA DLSS Ray Reconstruction（或 NRD ReBLUR 搭配 DLSS / FSR / XeSS 上采样）把每像素只有 1 个样本的结果还原成干净的画面。你仍然使用原版界面、原版方块、原版资源包——只是光变了。

它建立在开源的 Caustica 与 Caustica-RTX 之上，并在此基础上补齐了一整套"让世界看起来像个世界"的系统：天气、体积云、体积光、末地、极光、远景地形、相机光学、HDR，以及一个能输出 8K 的离线摄影模式。

---

## 你会看到什么

**真正的间接光与反射**
每个像素追踪主光线与多次反弹，漫反射、光泽反射、透射一次算完；玻璃、冰、水是有折射率的体积，不是贴图。

**很多光源也不卡成幻灯片的"聪明"采样**
常开的 RIS 光源采样（至少 8 个候选），可选 **ReSTIR DI**（大量小光源，如一整排火把）与 **ReSTIR PT Enhanced**（完整路径重采样）。选 DI 时会自动搭配 SHARC 间接缓存。

**会呼吸的天空与天气**
Hillaire 大气散射、物理尺寸的日月、NASA 星图、夜间极光、雨后彩虹；Radiance 体积云（可投影、可参与光线追踪）、froxel 体积光、随天气和时间变化的雾、会积水的湿润地面、折射的雨滴；末地有自己的紫色体积光束与漩涡。

**拿在手里的光是真的光**
双手各持一个光源（火把、岩浆桶、荧石……）都会照亮周围，并投下真实阴影。

**PBR 与"凸起来"的纹理**
支持 LabPBR 资源包与有界高度场视差；资源包可以用 JSON 覆盖材质的发光强度、折射率和色散。

**水**
三档水面（性能 / 平衡 / 质量）：质量档是 32 分量的方向波谱，焦散与可见涟漪同源。

**看得很远**
Voxy 与 Distant Horizons 的远景地形被转换成可追踪的几何，一同参与反射与光照。

**像摄影师一样控制画面**
光圈 f/1.4 – f/22 的物理景深、动态模糊、八边形光圈衍射星芒、镜头光晕与棱镜漏光、胶片颗粒；曝光以真实的 cd/m² 与 EV100 度量；**ACES 2.0** 输出，支持 **HDR（PQ，500–4000 nit）**；三种风格：原版 / GTA VI 风格 / Kodak 2383 风格。

**帧生成**
DLSS、FSR、XeSS 三个提供者（2×–4×，3×/4× 多帧生成需要 RTX 50），并支持 NVIDIA Reflex。

**离线摄影模式**
按 `Y` 打开面板，分块累积最高 **7680 × 7680** 像素，输出 PNG / JPEG / TIFF / OpenEXR / HEIC / AVIF / JPEG XL，附完整拍摄元数据，HDR 与 EXR 自动附带一张 SDR 副图。

---

## 和其他方案比一比

先说结论：**没有"通吃"的选择**。它们解决的是不同问题、面向不同平台与显卡。下面只列出各项目**自己公开说明**里写到的内容；没写到的写作"未列出"，不代表不具备。

### A. 同类的 Vulkan 硬件光线追踪模组

| | **Caustica Enhanced** | Caustica-RTX | Radiance |
| --- | --- | --- | --- |
| Minecraft 版本 | 26.2（Fabric） | 26.2（Fabric） | 1.20.1 / 1.21.1 / 1.21.4（Fabric、Forge、NeoForge）；26.x 移植进行中、暂无构建 |
| 渲染方式 | Vulkan 硬件路径追踪 | Vulkan 硬件路径追踪 | Vulkan 硬件光线追踪 |
| DLSS Ray Reconstruction | ✅ | ✅ | ✅ |
| 非 NVIDIA 路线 | ✅ NRD ReBLUR + FSR | 待办（README 中未勾选） | ✅ NRD + FSR |
| 帧生成 | DLSS / FSR / XeSS，2×–4× | DLSS FG，RTX 50 多帧至 4×（实验） | DLSS 与 FSR 帧生成（受支持时） |
| ReSTIR | ✅ DI 与 PT Enhanced | 待办 | 未提及 |
| 云 / 体积光 / 雾 / 天气 | ✅ Radiance 云、froxel 体积光、天气雾、雨与湿润、末地、极光、彩虹 | 待办 | 大气、云、雾、水、降雨湿润 |
| 远景地形 | ✅ Voxy 与 Distant Horizons | 待办 | Distant Horizons 3.3.0–3.3.2（旧版本线） |
| 间接缓存 | Radiance Cache 或 SHARC | 未列出 | 未列出 |
| HDR 输出 | ✅ ACES 2.0，500–4000 nit | ✅ | 未列出 |
| 离线高分辨率摄影 | ✅ 最高 7680 px，多格式 + 元数据 | 未列出 | 未列出 |
| 开源许可 | GPL-3.0-only（原始 Caustica 文件保留 LGPL-3.0+） | LGPL-3.0+ | GPL-3.0 |

*Caustica-RTX 是 Caustica 的 RTX 取向分支，README 把 ReSTIR、末地天空、天气、体积雾/云、NRD+FSR、LOD 列为尚未完成的待办；Caustica Enhanced 的这些部分已在源码中实现。Radiance 则胜在**版本线更广**（1.20.1–1.21.4、多加载器）。*

### B. 其他路线：光影包与 Bedrock

| | 平台 | 做法 | 一句话定位 |
| --- | --- | --- | --- |
| **Rethinking Voxels** | Java，Iris 光影包（1.19.2+） | 体素化 + 彩色光与光线追踪阴影（基于 Complementary Reimagined 的修改版） | 不依赖 Vulkan 光追模组，门槛低、画风贴近原版 |
| **SEUS PTGI** | Java，光影包 | 软件实现的路径追踪全局光照，不需要 RT 核心 | 没有 RT 核心也能体验路径追踪全局光照 |
| **Minecraft RTX** | 基岩版（官方） | 官方路径追踪 + DLSS | 官方、开箱即用，但**只在基岩版** |
| **BetterRTX** | 基岩版（社区） | 修改官方 RTX 着色器：物理天空、水面视差、积水、焦散、景深与动态模糊等 | 想继续用基岩版 RTX 并加强它 |

### 它适合你吗？

- ✅ 你玩 **Java 版 26.2**，显卡支持 Vulkan 光线追踪（NVIDIA 可用 DLSS 全家桶；非 NVIDIA 走 NRD + FSR 路线），想要**接近离线渲染的整体光照**，并愿意为此付出性能：选 **Caustica Enhanced**。
- ✅ 你要的是**多版本、多加载器**的硬件光追：看看 **Radiance**。
- ✅ 你没有光追硬件，或者想要轻量、贴近原版的画风：**Rethinking Voxels** 或其他光影包更合适。
- ✅ 你玩基岩版：**Minecraft RTX**（+ BetterRTX）。

---

## 系统要求

| 项目 | 要求 |
| --- | --- |
| 游戏 | Minecraft **26.2**（Java 版），Fabric Loader ≥ 0.19.5，Fabric API，**Java 25** |
| 图形 | 使用 **Vulkan** 后端；显卡与驱动需支持 Vulkan 光线追踪（加速结构、光线追踪管线、光线查询、位置获取等） |
| DLSS / Ray Reconstruction | NVIDIA RTX 显卡与受支持驱动 |
| 多帧生成（3×/4×） | RTX 50 系列 |
| 非 NVIDIA | 提供 NRD ReBLUR + FSR 路线（XeSS 超分仅在 NVIDIA 设备上提供） |
| 系统 | 随包的原生重建库为 **Windows x64**（NGX 垫片另有 Linux 构建脚本） |
| 显存 | 光线追踪本身需要较多显存；ReSTIR PT Enhanced 每个内部像素约 736 字节（1920×1080 约 1.42 GiB，另加其他缓冲） |
| 可选 | **Voxy 0.2.19-beta**（含 Sodium）或 **Distant Horizons ≥ 3.3.3** 提供远景；HDR 需要支持 HDR 的显示器与系统设置 |

> RTX 20/30 系列：默认关闭 SER、OMM 与 DLSS 帧生成，DLSS Ray Reconstruction 仍可使用；FSR / XeSS 帧生成可用。

## 安装

1. 准备 Minecraft 26.2 + Fabric Loader + Fabric API，并在游戏视频设置里选择 **Vulkan** 图形后端。
2. 把构建好的 Caustica Enhanced JAR 放进 `mods` 文件夹（**只放一个 Caustica 的 JAR**）。预编译 JAR 以仓库 Releases 为准；自行构建见 [BUILDING.md](BUILDING.zh-CN.md)。
3. 需要远景地形的话，另装 Voxy 0.2.19-beta（及其 Sodium 依赖）或 Distant Horizons ≥ 3.3.3。
4. 首次进入游戏时，驱动需要编译光线追踪管线，会显示"Preparing shaders / Compiling world pipeline"进度；原版画面在此期间仍可使用，编译结果会缓存，之后启动更快。
5. 设置位于视频设置中的 **Caustica Enhanced** 页面；模组数据（配置、缓存、导出）都在游戏目录下的 `Caustica Enhanced/` 文件夹里。

## 常见问题

**需要 RTX 显卡吗？** 需要支持 Vulkan 光线追踪的显卡。DLSS 相关功能需要 NVIDIA RTX；非 NVIDIA 显卡走 NRD ReBLUR + FSR 路线。

**会不会很吃性能？** 路径追踪本来就重。本项目提供了降低成本的选项（水面性能档、按需编译 PT 阶段、DLSS/FSR/XeSS 上采样、帧生成），但**我们没有发布任何帧率数据**，请以你自己机器上的实测为准。

**能和光影包一起用吗？** 不能。它整体替换世界渲染。

**远景地形为什么有的地方是空的？** 远景由 Voxy / Distant Horizons 提供，它们只提供**已访问或已生成**的地形；本模组不会让未知区块凭空出现。

**HDR 怎么开？** 先在系统里打开 HDR，再在 *HDR Display* 页启用；峰值亮度可选 500 / 1000 / 2000 / 4000 nit。

## 诚实说明：当前状态与限制

我们宁愿把话说在前面：

- **本源码树已完整构建，并通过 66 个测试类 / 231 项 Java 单元测试；着色器已离线编译并验证。但这一构建尚未在 GPU / 游戏内运行验证。** 文档中描述的是源码**已实现**的行为，而不是"已经在你的机器上被证明"的画质或性能。
- 多帧生成的呈现仍是实验性的；帧生成**不会**降低着色成本或输入延迟。
- 视差是有界高度场，不会生成真实位移几何；远景是体素近似，没有近景植物动画。
- ReSTIR PT 占用显存大；缓存复用是近似；froxel 分辨率有限。
- 视觉风格（GTA VI / Kodak 2383）是**艺术灵感**，不是授权或实测的胶片/引擎复刻，也与任何公司无关。
- 只支持 **26.2**；不是基岩版。

## 致谢与许可

Caustica Enhanced 以 **GPL-3.0-only** 发布（原始 Caustica 文件保留 LGPL-3.0-or-later 声明），并包含或参考了下列项目的代码与算法，它们各自的许可与致谢见 [THIRD_PARTY_NOTICES.md](../mod/THIRD_PARTY_NOTICES.md)：
Caustica（ComfyFluffy）、Caustica-RTX（AriesAlex）、Radiance / MCVR / Shaderpack-Advanced、Prime PT、NVIDIA DLSS / NRD / NRI / SHARC / STBN、Intel XeSS、AMD FidelityFX、NASA Deep Star Maps。Voxy 不随包分发。

---

### 竞品信息来源（2026-10-18 访问，可能已更新）

- Caustica-RTX README — <https://github.com/AriesAlex/Caustica-RTX>
- Radiance README — <https://github.com/Minecraft-Radiance/Radiance>
- Rethinking Voxels README — <https://github.com/gri573/rethinking-voxels>
- SEUS PTGI 介绍 — PCGamesN，<https://www.pcgamesn.com/minecraft/sonic-ether-shader>
- Minecraft RTX 官方发布说明 — NVIDIA，<https://www.nvidia.com/en-us/geforce/news/minecraft-rtx-dlss-official-release/>
- BetterRTX — <https://github.com/BetterRTX>

本文对其他项目的描述仅依据上述公开页面；凡"未列出"，仅表示该页面未提及，并不代表该项目不具备此能力。商标归各自所有者。
