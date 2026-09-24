# Caustica-Enhanced
Ray-traced renderer for Minecraft 26.2's Vulkan backend. Modified and enhanced by ChatGPT-6 Astra.

Target: Minecraft 26.2, Fabric, Java 25+, Windows x64, Vulkan

English

Caustica-Enhanced is a Vulkan ray-tracing renderer for Minecraft. It builds chunk-level acceleration structures and traces block, entity, and lighting geometry in a compute/ray-tracing pipeline. World streaming remains at the normal 32-chunk render-distance limit. The renderer uses one sample per pixel by default and supports up to three path bounces.

| Area | Features and implementation |
|---|---|
| Reconstruction | Selectable DLSS, FSR 3.1.4 Vulkan, or XeSS 3.0.2 upscaling. DLSS is paired with NVIDIA Ray Reconstruction (RR); FSR and XeSS use NVIDIA NRD RELAX. Adapter vendor detection routes non-NVIDIA GPUs to FSR + NRD. Upscaler changes reset temporal history. |
| Atmosphere | Optional volumetric clouds and light scattering with adjustable 0–1 strength and cloud coverage. Density sampling uses layered noise and adaptive ray-march steps; cloud shadows use a lower-cost density pass. Rain and thunderstorms smoothly raise cloud strength and coverage to 1, then restore the configured values when clear. Fog strength remains independently adjustable. |
| Water | Performance and Quality modes use 16- and 32-wave analytic surfaces respectively. Procedural phase, direction, and amplitude variation animate surface normals; refraction and caustic focusing are approximated in the shader. Water tint varies with optical path length. |
| Materials and post-processing | LabPBR height data in normal-map alpha drives bounded parallax UV offsets on eligible opaque surfaces. Post-processing includes selectable Vanilla/GTA VI color grading, exposure, adjustable bloom, softened lens glare, and depth-aware motion blur. HDR10 output is available when supported by the system and display. |
| NVIDIA features | Reflex On/Boost and optional 2× DLSS Frame Generation are hardware/driver gated. A first-person option excludes the local player model from ray-tracing geometry while third-person models remain available. |
| Interface | Settings are available in English and Simplified Chinese, from vanilla Video Settings and Sodium 0.9.2. Existing configuration files take precedence over bundled defaults. |

**Validation and limits.** The delivered build passes 62 Java tests, 24 GPU numerical checks, and isolated client startup/settings checks with and without Sodium. FSR, XeSS, and NRD GPU dispatch/readback was exercised on an RTX 3060 Laptop. FSR support here is Vulkan 3.1.4, not FSR 4. NRD currently processes combined radiance rather than separate diffuse and specular signals. Other GPU vendors, HDR displays, actual frame-generation presentation, in-world image quality, and sustained performance were not independently verified.

简体中文

目标环境： Minecraft 26.2、Fabric、Java 25+、Windows x64、Vulkan

Caustica-Enhanced 是面向 Minecraft 的 Vulkan 光线追踪渲染器。它为区块几何建立加速结构，并在计算／光追管线中追踪方块、实体与光照。世界视距上限为原版 32 区块；默认每像素每帧采样 1 次，路径最多反弹 3 次。

| 模块 | 功能与实现 |
|---|---|
| 重建与超分辨率 | 可选 DLSS、FSR 3.1.4 Vulkan、XeSS 3.0.2。DLSS 固定搭配 NVIDIA 光线重建 RR；FSR 和 XeSS 固定搭配 NVIDIA NRD RELAX。检测到非 NVIDIA 显卡时自动选择 FSR + NRD。切换超分辨率后重置时域历史。 |
| 大气效果 | 可选体积云与体积光，云覆盖率和强度范围均为 0–1。分层噪声生成密度，并按距离调整光线步进；云影使用较低成本的密度计算。雨天或雷雨会平滑地把云覆盖率和强度提高至 1，天气转晴后恢复配置值。体积雾强度独立调节。 |
| 水面 | 性能／质量模式分别使用 16／32 层解析波形。程序化改变波形相位、方向和振幅以产生动画法线；着色器近似计算折射与焦散聚光。水色随光在水中的传播距离变化。 |
| 材质与后处理 | 从 LabPBR 法线贴图 Alpha 读取高度，在符合条件的不透明表面上进行有限视差 UV 偏移。后处理包括 Vanilla／GTA VI 调色、曝光、Bloom 强度、柔化镜头眩光和深度感知动态模糊。系统与显示器支持时可输出 HDR10。 |
| NVIDIA 功能 3060 Laptop 上验证。此处 FSR 使用 Vulkan 3.1.4，不是 FSR 4。NRD 当前处理合并光照信号，尚未拆分漫反射与镜面反射。其他显卡厂商、HDR 显示器输出、实际帧生成呈现、游戏内画质及长时间性能尚未独立验证。


<img width="2560" height="1600" alt="2026-09-18_21 50 34" src="https://github.com/user-attachments/assets/0c8c7f1e-356c-4bcc-9f47-dbea6d8d8fe6" />
<img width="2560" height="1600" alt="2026-09-18_21 38 31" src="https://github.com/user-attachments/assets/54bba7c5-14b1-4fdc-b5ab-ab421f40dc31" />
<img width="2560" height="1600" alt="2026-09-18_21 30 56" src="https://github.com/user-attachments/assets/c606acce-624b-4a9d-9a04-49e29f9bd737" />
<img width="2560" height="1600" alt="2026-09-18_21 23 39" src="https://github.com/user-attachments/assets/3d64d669-2849-4057-8fb6-b96b06eeeaf1" />
<img width="2560" height="1600" alt="2026-09-18_21 22 15" src="https://github.com/user-attachments/assets/73832a2d-d0fe-47ad-847b-f808be983f93" />
<img width="2560" height="1600" alt="2026-09-18_21 16 56" src="https://github.com/user-attachments/assets/de9ed259-cf3c-4bbc-81b2-029f81b44dfd" />
<img width="2560" height="1600" alt="2026-09-18_21 13 12" src="https://github.com/user-attachments/assets/8a0dee8c-28ec-4417-a8c7-48117ed34537" />
<img width="2560" height="1600" alt="2026-09-18_21 04 16" src="https://github.com/user-attachments/assets/a0f46046-a92e-48a5-8cfa-3669ca217d00" />
<img width="2560" height="1600" alt="2026-09-18_21 02 08" src="https://github.com/user-attachments/assets/96e184fc-f1f3-467d-9b6c-c477f2880e0c" />
<img width="2560" height="1600" alt="2026-09-18_20 53 02" src="https://github.com/user-attachments/assets/56f20024-57cd-4d5f-bdd7-d8dd84f61faf" />
<img width="2560" height="1600" alt="2026-09-18_20 34 24" src="https://github.com/user-attachments/assets/1a6c72d8-a739-429f-8528-35bea6452a89" />
<img width="2560" height="1600" alt="2026-09-18_20 05 56" src="https://github.com/user-attachments/assets/75c942ee-a8ce-4f95-a079-e85fcceb9433" />
<img width="2560" height="1600" alt="2026-09-18_19 56 22" src="https://github.com/user-attachments/assets/4333f880-a1ba-4580-b477-1871c6643f6a" />
