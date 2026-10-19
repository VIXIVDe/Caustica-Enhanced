# Voxy compatibility

Caustica Enhanced supports the official Minecraft 26.2
Voxy 0.2.19-beta release. Install Voxy and its Sodium dependency separately
(Sodium 0.9.1 or 0.9.2 for 26.2). Unsupported Voxy versions are rejected by
Fabric's dependency check rather than entering incompatible rendering hooks.

Select **Distant terrain provider** in the rendering settings. The list shows only the providers that are installed
(**Voxy**, **Distant Horizons**) plus **Off**; the default is the first entry (Voxy if installed, else Distant Horizons, else Off).
Exactly one provider supplies terrain at a time:

- **Voxy:** use Voxy data only.
- **Distant Horizons:** use DH data only.
- **Off:** disable both distant providers in Caustica.

Voxy retains its storage and ingestion system; Caustica independently converts
acquired snapshots to Vulkan geometry and traces them with the existing reduced
distant-lighting path. Voxy's OpenGL terrain renderer is disabled under Vulkan.
Voxy LODs reuse block-face sprites from the current resource pack, stored biome
tints and material IDs. Cutout leaves use atlas alpha; water retains biome color.
Face UVs are projected during ray hits, without expanded per-triangle UV storage.
The adapter retains Voxy voxel geometry, rather than original block model meshes;
normal maps and parallax remain reserved for near terrain. Voxy and DH cannot supply terrain simultaneously.

Voxy supplies visited or imported terrain. This adapter does not generate
unknown Minecraft chunks. Distance comes from Voxy's configured distance,
converted from 512-block sections and capped at 512 chunks. Unknown areas remain
unknown until Voxy receives their data.

## Resource control

- One snapshot worker; at most 64 new columns per batch, scheduled every 250 ms.
- Unseen roots precede missing-data retries; missing data retries after 5 seconds.
- 64 MiB retained CPU mesh budget, 8 MiB per column, existing GPU headroom checks.
- Greedy merging and six neighboring face snapshots suppress internal faces.
- Water interfaces preserve submerged opaque surfaces; water and lava variants
  retain their material classification, including flowing fluids.
- Coarse parents remain until required finer geometry is GPU-ready, then their
  CPU mesh bytes and GPU geometry are retired; fallback meshes rebuild on demand.
- One-block voxel precision extends at least 512 metres from the camera; coarser
  levels switch gradually with distance. Sprite repetition preserves texel scale.
- Atlas preparation gates Voxy palette initialization, including resource reloads.
- World epochs and acquired engine references protect updates and shutdown.

## Limits

- The 64 MiB limit applies to Caustica's retained CPU mesh cache, not Voxy's own storage cache, the Java heap or total process
  memory. Finer geometry can increase active GPU memory despite removing redundant parent meshes.
- No long-duration, large-world performance measurement is published for either provider; see
  [`../../docs/VERIFICATION.md`](../../docs/VERIFICATION.md) for what the build verified.

Voxy provenance and its unbundled license/dependencies are recorded in
`THIRD_PARTY_NOTICES.md`.
