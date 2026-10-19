# 构建 Caustica Enhanced

[English](BUILDING.md) · [技术报告](TECHNICAL_REPORT.zh-CN.md) · [宣传页](SHOWCASE.zh-CN.md)

本仓库只包含**源码、着色器、小型资源和工具脚本**。它**刻意不包含**厂商 SDK、第三方模组 JAR、超大数据文件和发布用 JAR。本页列出你必须自备的内容、各自放在哪里，以及如何构建。

> 状态：维护者工作区中本源码树的构建退出码为 0，66 个 Java 测试套件 / 231 个测试通过（2 个被跳过），56 个 SPIR-V 模块校验通过（见 [VERIFICATION.zh-CN.md](VERIFICATION.zh-CN.md)）。这一构建**尚未在 GPU 或游戏内运行过**。构建成功只说明代码能编译、单元测试通过，不说明画面或性能正确。

## 1. 仓库结构

| 路径 | 内容 |
| --- | --- |
| `mod/` | **Gradle 根目录**：`build.gradle`、`src/main/java`、`src/test/java`、`shaders/`（Slang）、`native/`（C++ 桥接与 GPU 冒烟测试）、`resources/` 与 `src/main/resources/`、`tools/`（Python 资源烘焙脚本）、`docs/`（开发笔记） |
| `docs/` | 技术报告、宣传页、本页 |
| `devtools/` | 验证工具、辅助脚本、本地构建代理（Windows） |
| `scripts/` | `build.ps1`：维护者工作区使用的离线构建封装 |
| `toolchain/` | *不在仓库中。* 本地 SDK 目录（见第 3 节） |
| `reference/` | *不在仓库中。* 固定版本的参考数据（见 3.6） |

## 2. 构建主机要求

| 项目 | 要求 |
| --- | --- |
| 操作系统 | 完整构建需要 **Windows x64**（带 XeSS / FSR / NRD 的 Vulkan 重建桥只为 Windows x64 构建）。`build.gradle` 也包含 NGX shim 的 Linux x64 路径，但完整功能只在 Windows 上构建。 |
| JDK | **JDK 25 或更新**（`sourceCompatibility = 25`）；维护者工作区使用 JDK 26.0.2 |
| Gradle | Wrapper 固定为 **Gradle 9.5.0**，首次使用自动下载。Fabric Loom 1.17.21、Minecraft 26.2、Fabric Loader 0.19.5、Fabric API 0.153.0+26.2（见 `mod/gradle.properties`） |
| Vulkan SDK | `VULKAN_SDK` 须指向含 `slangc` 与 `spirv-val` 的 SDK（或两者都在 `PATH` 中）。着色器用 Slang 编写，构建时编译为 SPIR-V，并用 `spirv-val --target-env vulkan1.2` 校验 |
| C++ | CMake 与 MSVC 命令行环境（使用 `NMake Makefiles` 生成器），C++17 |
| NVIDIA DLSS SDK | 环境变量 `DLSS_SDK`（见 3.2） |
| 网络 | 首次构建会通过 Gradle 下载 Minecraft、映射、Fabric 与 NightConfig；维护者工作区之后用已填充的 Gradle home 以 `--offline` 构建 |
| Python | 仅第 6 节的可选资源工具需要：Python 3.14（`mod/pyproject.toml`），NumPy、OpenColorIO、OpenEXR；星图解码脚本需要 `zstandard` |

## 3. 你必须自备的内容

### 3.1 Groovy 构建源码

`mod/buildSrc/src/main/groovy/dev/comfyfluffy/caustica/build/` 下有三个被 `build.gradle` 导入的 Groovy 类：`CompileShaderWork.groovy`、`GenerateRtBindings.groovy`、`GenerateShaderRecords.groovy`。如果你的检出里缺少它们，请看该目录下的 `_COPY_GROOVY_FILES_HERE.txt`；缺少它们时 `build.gradle` 无法完成配置。

### 3.2 NVIDIA DLSS / NGX SDK（`DLSS_SDK`）

按 NVIDIA 的许可从 NVIDIA 下载 DLSS SDK，把 `DLSS_SDK` 设为其根目录。构建会把 `lib/Windows_x86_64/<rel|dev>/` 中的 DLSS 运行库（`nvngx_dlss.dll`、`nvngx_dlssd.dll`、`nvngx_dlssg.dll`）复制进 JAR，并用 CMake 构建小型 NGX shim（`mod/native/ngx_shim`）。`-PngxVendorConfig=rel|dev` 选择运行库类型（默认 `rel`，`runClient` 默认 `dev`）；`-PngxShimConfig=release|debug` 选择 shim 配置；`-PngxPlatforms=windows-x64`（或 `linux-x64`，或逗号分隔的两者）选择平台。

### 3.3 重建 SDK（`toolchain/`）

原生重建桥（`mod/native/reconstruction`）默认在相对 `mod/` 的 `../toolchain` 中查找（可用 `-PreconstructionSdkRoot=<目录>` 覆盖）：

| SDK 根目录下的路径 | 内容 |
| --- | --- |
| `xess-3.0.2/` | Intel XeSS SDK 3.0.2：`inc/`、`lib/libxess.lib`、`bin/libxess.dll`、`libxess_fg.dll`、`libxell.dll` |
| `fsr-vulkan/` | AMD FidelityFX SDK 1.1.4 的 `ffx-api` Vulkan 后端：`ffx-api/include`、`ffx-api/bin/amd_fidelityfx_vk.lib` 与 `.dll`。（FSR 较新的 ML/DX12 运行库**不能**替代它。） |
| `NRD/` | NVIDIA NRD 4.17.3：`Include/`、`Integration/`、`_Bin/NRD.lib`、`NRD.dll`、`NRI.lib`、`NRI.dll` |
| `NRD-build/_deps/nri-src/` | NRD 固定的 NRI 源码（`Include/`） |

构建 NRD 时使用 `NRD_NRI=ON`、`NRD_NORMAL_ENCODING=4`、`NRD_ROUGHNESS_ENCODING=1`、`NRD_EMBEDS_DXIL_SHADERS=OFF`、`NRD_EMBEDS_DXBC_SHADERS=OFF`、`NRI_ENABLE_D3D11_SUPPORT=OFF`、`NRI_ENABLE_D3D12_SUPPORT=OFF`。详见 [`mod/native/reconstruction/README.md`](../mod/native/reconstruction/README.md)。厂商二进制原样打包，其许可文本嵌入 JAR 的 `META-INF/licenses`。

### 3.4 Voxy（仅编译期）

把 Voxy **0.2.19-beta（Minecraft 26.2）** 的 JAR 放到 `devtools/dependencies/voxy/voxy-0.2.19-beta.jar`。期望 SHA-256：`A06E4D93DB88DC22D6CDE6DFE1E58D8428AE271D1F432BBB430735336F4B5C12`。Voxy 为 *All Rights Reserved*：它只作为编译期引用，不被打包也不可再分发，因此本仓库不携带。

### 3.5 Distant Horizons（编译与测试）

把 `DistantHorizons-3.3.3-26.2-fabric-neoforge.jar` 放到 `toolchain/reference-dh-3.3.3-26.2/DistantHorizons-3.3.3-26.2-fabric-neoforge.jar`，或用 `-PdhJar=<jar 路径>` 指定。

### 3.6 Prime 星图（需重新生成的二进制）

`mod/src/main/resources/assets/caustica/sky/prime-starmap.bin`（约 179 MB，BC6H 格式的 NASA Deep Star Maps）是*生成物*，不入库。请从 Prime 项目获取固定版本的 `prime-starmap-0.1.0.ktx2`（提交号与署名见 [`THIRD_PARTY_NOTICES.md`](../mod/THIRD_PARTY_NOTICES.md)），放到 `reference/prime-starmap-0.1.0.ktx2`（SHA-256 `64bcda4bf9068dae0591bf26f7bd363ec289d3cc95eb528e687a21cc2c355a02`），安装 `zstandard`（`pip install --target devtools/dependencies zstandard==0.25.0`），然后运行：

```powershell
python devtools/decode_prime_starmap.py
```

脚本会校验哈希和布局（16384×8192、15 级 BC6H mip）并写出 `.bin`。**要运行的 JAR 必须先做这一步：**文件缺失时 `RtStarMap.load` 会抛出 `missing star map resource`，没有它构建出的 JAR 无法在游戏中使用。（仅编译和单元测试不需要它。）

### 3.7 照片编码器压缩包（可选）

`caustica/codecs/windows-x64.zip`（ImageMagick 7.1.2-33 portable Q16）和 `caustica/codecs/heif-windows-x64.zip`（MSYS2 libheif 1.23.6 / x265 4.3）是 `mod/src/main/resources/` 下的类路径资源，用于离线摄影的 HEIC / AVIF / JPEG XL 导出。它们不在本仓库中。缺少时模组仍可运行，这三种格式会显示“不可用”（PNG、JPEG、TIFF、OpenEXR 不依赖它们）。**构建时的注意事项：**在 Windows 上，单元测试 `RtOfflineImageTest.jpegXlLosslessPreservesEverySdrAndHdrSample` 会从类路径打开 `windows-x64.zip`，缺失时测试失败，导致 `gradlew build` 在 `test` 阶段失败。请补上该压缩包，或以 `-x test` 构建（例如 `gradlew build -x test`）。

## 4. 构建

先设置环境（以 PowerShell 为例）：

```powershell
$env:JAVA_HOME   = 'C:\Program Files\Java\jdk-26.0.2'      # 任意 JDK >= 25
$env:VULKAN_SDK  = 'C:\VulkanSDK\<版本>'                   # Bin\ 中有 slangc 与 spirv-val
$env:DLSS_SDK    = 'C:\SDKs\DLSS'                          # NVIDIA DLSS SDK 根目录
# 同一个 shell 中还需要 CMake 与 MSVC 环境（vcvars64.bat）

cd mod
.\gradlew.bat build
```

常用变体：

| 目的 | 命令（在 `mod/` 中运行） |
| --- | --- |
| 完整构建（着色器、原生库、测试、JAR、源码 JAR） | `gradlew build`（若没有 3.7 的编码器压缩包，加 `-x test`） |
| 不重编着色器，仅测试 + 打 JAR（仅当已编译的着色器与源码一致时） | `gradlew test jar -x compileShaders -x sourcesJar` |
| 用已填充的 Gradle home 离线构建 | 加 `--offline` |
| 运行开发客户端 | `gradlew runClient`（见 `runClient.ps1`，使用 `dev` 版 DLSS 运行库） |

JAR 输出到 `mod/build/libs/Caustica Enhanced v.<N>.jar`（`<N>` 为 `mod_version` 最后一段，例如 `76`），旁边还有源码 JAR。维护者工作区中一次完整着色器编译约需 15–25 分钟。**不要随手运行 `gradlew clean`**，它会删除已生成的 SPIR-V 和原生构建目录。

JAR 体积很大（约 423 MB），因为它打包了 NGX/XeSS/FSR/NRD 运行库、SPIR-V 模块和星图。请通过 **GitHub Releases** 发布（单个资源最大 2 GiB），不要放进 git 历史。

### 维护者工作区封装（可选，Windows）

- `scripts/build.ps1 [-Fast] [-JavaHome <jdk>]` 会加载 `toolchain/env.ps1`（一个**不在仓库中**的本地脚本，负责配置 MSVC、CMake、Vulkan SDK、`DLSS_SDK` 和离线 Gradle home），然后运行 `gradlew -p mod build --offline`（`-Fast` 即不编译着色器的 `test jar`）。
- `devtools/build-release.ps1 -Release <N>` 设置 `mod_version`、运行完整构建并在维护者工作区的 `releases/` 下写出发布记录文件夹（JAR 副本、`SHA256SUMS.txt`、`verification.json`、日志）。
- `devtools/build-agent/` 是运行这些白名单操作的 Windows 文件队列代理（见其 README）。
- `devtools/BUILD-WORKFLOW.md` 记录快速/完整构建的规则，包括编辑时如何单独编译一个着色器。

## 5. 测试

- `gradlew test` 运行 `mod/src/test/java` 中的 JUnit 5 套件（66 个套件 / 231 个测试，2 个被跳过）。
- `mod/native/tests/*.ps1` 是独立的 GPU / 数学冒烟测试（云数学、缓存、发光体采样、对焦、LOD、运动等），会编译 Slang 内核并在 Vulkan 设备上运行。它们需要 GPU，**不属于**构建记录。
- [`VERIFICATION.zh-CN.md`](VERIFICATION.zh-CN.md) 记录构建验证了什么、没有证明什么。
- `devtools/` 里有合成世界验证与性能采集工具。它是为仍带有 ReSTIR GI 模式的早期渲染器编写的，部分地方仍引用该模式；请把它当作起点，而不是仍在维护的验收门槛。

## 6. 重新生成烘焙资源

| 资源 | 工具 | 说明 |
| --- | --- | --- |
| ACES 2.0 显示 LUT + 内置 LMT | `mod/tools/bake_display_lut.py` | OCIO 配置 `cg-config-v4.0.0_aces-v2.0_ocio-v2.5`；一个 SDR LUT 与 500 / 1000 / 2000 / 4000 尼特的 HDR LUT |
| 光圈 PSF | `mod/tools/bake_optics_psf.py` | 线性、能量归一的光谱 PSF |
| 云噪声包 | `mod/tools/pack_radiance_noise.py` | 来源为 `mod/tools/radiance-noise-source/`（署名见其 `NOTICE.md`） |
| 星图 | `devtools/decode_prime_starmap.py` | 见 3.6 |

前三项的 Python 环境由 `mod/pyproject.toml` / `mod/uv.lock` 描述（`uv sync`）。

## 7. 持续集成

`mod/.github/workflows/ci.yml` 继承自上游 Caustica 项目。它只构建 Windows 的 NGX shim（在托管运行器上检出 `NVIDIA/DLSS` 并安装 Vulkan SDK），其路径假定 Gradle 项目就是仓库根目录。GitHub 只运行 `<仓库根>/.github/workflows` 下的工作流，所以**它在当前布局下不会运行**。若要使用，请把它移到仓库根目录并给其中的路径加上 `mod/` 前缀。完整的 CI 构建还需要第 3 节的 SDK，原生 GPU 测试还需要 GPU，也就是一台自托管的 Windows 运行器。

## 8. 许可

组合作品为 GPL-3.0-only；Caustica 原有文件保留 LGPL-3.0-or-later 的文件头。第三方组件保留各自条款：[`mod/THIRD_PARTY_NOTICES.md`](../mod/THIRD_PARTY_NOTICES.md)、[`LICENSE`](../LICENSE)。
