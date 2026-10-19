# Caustica Enhanced — Offline photography

## English

### Controls and interface
Y opens or closes the floating panel. Hold Alt to interact, and press Enter to photograph or cancel. The three panel sizes use a uniform integer framebuffer-pixel scale for both native text/widgets and their input coordinates; Medium is the default. Small windows clamp the scale to what fits. Controls use two columns when space permits, with compact category tabs and paging. The live VRAM bar displays driver-reported device-local heap usage and capacity; without the memory-budget extension, usage is explicitly marked allocator-only.

Freeze camera locks the capture position and orientation without blocking FOV or optical adjustments. Freeze world holds integrated-server simulation and local animation; it cannot pause a remote multiplayer server. Settings persist in Caustica Enhanced/config/offline.json in the instance directory (the older config/caustica-offline.json is migrated), excluding world time and transient time override state.

### Tiles and consistency
Automatic selects a tile core from current device-local memory headroom and recent live-frame cadence, and shows its pixel size in parentheses. A custom core can be selected and adjusted from 128 to 1024 pixels in 32-pixel steps. The chosen plan is fixed for the entire capture. A 32-pixel guard surrounds each core; output is visited left to right, top to bottom.

Exposure, focus, camera, animation clocks, weather transitions, published terrain and held-light profiles stay fixed during capture. Full-film coordinates and identical sample phases drive ray, fog, cloud, aperture and film-grain sampling. Each denoised tile receives the same preparation period (8 frames for RR, 4 for ReBLUR) before its requested 1–16 samples are accumulated. Direct offline volume integration avoids different interpolation grids between neighbouring tiles. Full-view bloom preserves its original pyramid normalization and follows the photo aspect ratio. These measures remove inconsistent per-tile state; a low sample budget still contains Monte Carlo noise.

The assembled preview retains a blurred game image in unfinished areas. Assembly is backed by disk and encoding runs on a worker thread. Cancelling restores the game settings and releases capture resources.

### Image output and metadata
PNG, JPEG, TIFF, EXR, HEIC, AVIF and lossless JPEG XL are supported. HEIC/AVIF support 8/10/12-bit channels; PNG/TIFF store high significant-bit settings in 16-bit channels. EXR stores half-float scene-linear values. JPEG is 8-bit SDR. HDR raster output uses PQ and its selected gamut, mapping and peak luminance.

Exports embed format-supported metadata and include a complete .metadata.json supplement: timestamp, project/version, camera pose/FOV/focus, world time/dimension, actual exposure, all photo controls, samples, bounces, reconstruction mode, tile plan, GPU and memory information, gamut, transfer function, precision and mapping. PNG/JPEG/TIFF/AVIF/JXL carry XMP; EXR carries capture attributes. The bundled HEIC encoder embeds the complete snapshot as labeled base64 UTF-8 in its primary image description, rather than claiming unsupported XMP preservation. ICC/CICP/PQ and peak-luminance tags are retained where supported. Configured CLLI values are bounds, not measurements of actual image content.

HDR and EXR exports also produce a genuine 16-bit Rec.709/sRGB .sdr.png rendition using the same styled scene-linear image and selected ACES/Reinhard/Linear shoulder. It is a separate mapped image, not an embedded gain map. Each file is individually committed atomically; the multi-file export is not one filesystem transaction.

### Rainbow flare and atmosphere
Rainbow lens flare uses visible bright highlights with wavelength-dependent diffraction spokes and internal ghosts. Analytic CIE observer curves provide smooth spectral colours before the common SDR/HDR output transform. Hidden light sources do not generate a highlight signal. This is a camera-optics approximation, not spectral path tracing.

Advanced atmosphere extends the shared Rayleigh/Mie/ozone sky model to finite camera-to-surface aerial perspective, including distant terrain. The transmittance and multiple-scattering LUTs provide coherent illumination and extinction. Four, six or eight analytical integration segments follow distance, with midpoint directional/upward visibility probes. It uses the sky model's 100 world blocks per kilometre scale, affects sky-lit dimensions, and skips underwater cameras and sky misses to avoid duplicate integration. Existing local weather fog and clouds remain separate media. The midpoint visibility probes approximate visibility along the segment; they are not a full per-step atmospheric shadow solution.

### Validation limits
The release build and 198 tests were run (196 passed, 2 skipped). An isolated world checks capture, freeze/FOV, VRAM, settings restoration, PNG and RR/ReBLUR EXR output, context metadata, SDR renditions and 8K cancellation. The supplied 8K AVIF was inspected, but its exact world/view has not been fully re-rendered at 8K. Native codec tests include actual decoded output and colour tags. Full-resolution performance across all hardware is not claimed.

## 中文

### 操作和界面
Y 打开或关闭右上角悬浮面板；按住 Alt 操作，Enter 拍照或取消。小、中、大采用统一的整数像素缩放，文字、控件与点击坐标同步缩放，默认中档；小窗口会限制到能容纳的比例。空间足够时使用双列控件，并保留分类标签和翻页。顶部显存条显示驱动报告的本地显存堆占用与容量；缺少预算扩展时会明确标注仅统计本分配器。

冻结镜头固定位置和方向，仍可调整 FOV 与镜头参数。冻结世界会停止单人服务器和本地动画，无法停止多人服务器。离线设置会自动记忆；时间及临时时间覆盖状态不会保存。

### 分区
Automatic 结合显存余量和当前帧间隔分配分区，并在括号内显示像素大小。自定义分区可在 128–1024 pixel 范围以 32 pixel 为步长调整。拍照后整个任务固定使用同一分区方案，每块四周附加 32 pixel 保护边界。

拍摄时锁定曝光、焦点、镜头、动画、天气过渡、已发布地形和手持光源。射线、云雾、景深和颗粒使用整张图片的坐标与一致采样阶段。RR 每块先准备 8 帧，ReBLUR 为 4 帧，再累计用户指定的 1–16 个样本。离线体积积分不依赖每块不同的低分辨率网格，整图 Bloom 保持统一归一化并匹配画幅比例。低采样数仍会存在路径追踪噪点。

### 导出
支持 PNG、JPEG、TIFF、EXR、HEIC、AVIF、无损 JPEG XL，以及对应的 8/10/12-bit 与高精度输出。写入格式支持的元数据，并附完整 .metadata.json：拍摄时间、项目版本、镜头姿态、FOV、焦距距离、游戏时间、曝光、全部拍摄设置、采样、反弹、重建方式、分区、GPU、显存和色彩信息。

HDR 保留 PQ、色域与峰值标签；峰值标签是设定范围，不代表实测内容亮度。HEIC 的完整参数以标记后的 base64 JSON 存在主图描述中，其他格式使用 XMP 或 EXR 属性。HDR/EXR 另附真正映射后的 16-bit SDR 图片 .sdr.png，方便普通显示器查看；它不是内嵌增益图。

### 新画面效果
彩虹炫光根据可见强光产生波长色散、光谱射线和镜片鬼影，在 SDR/HDR 色彩变换前处理，可独立开关。高级大气把天空已有的 Rayleigh、Mie、臭氧吸收与多次散射延伸到远景空气透视，与天空共用查找表，并保留独立的天气雾和云。仅作用于有天空光照的维度，不重复处理天空或水下。

### 验证范围
已运行构建及 198 项测试，196 项通过、2 项跳过；独立世界完成导出、冻结镜头/FOV、显存、元数据、SDR 副图、取消和恢复检查。原始 8K AVIF 已检查，但没有在其原场景完成一次完整 8K 复拍，不能据此保证所有硬件的 8K 耗时。

## Algorithm references

- Sébastien Hillaire, [A Scalable and Production Ready Sky and Atmosphere Rendering Technique](https://onlinelibrary.wiley.com/doi/10.1111/cgf.14050), and the author's [UnrealEngineSkyAtmosphere reference implementation](https://github.com/sebh/UnrealEngineSkyAtmosphere). Finite-segment integration and resource wiring are implemented for this renderer; no new external source files were copied.
- Chris Wyman, Peter-Pike Sloan and Peter Shirley, [Simple Analytic Approximations to the CIE XYZ Color Matching Functions](https://jcgt.org/published/0002/02/01/), equation 2. Used as a mathematical spectral-colour reference; no supplementary implementation was copied.
