import radiance_parallax;
[[vk::binding(0,0)]] Sampler2D heightTex;
struct Push { uint64_t output; };
[[vk::push_constant]] ConstantBuffer<Push> pc;
[shader("compute")]
[numthreads(1,1,1)]
void main(uint3 id:SV_DispatchThreadID) {
    uint test=id.x;
    float2 uv=float2(0.5,0.5);
    float3 dir=test==0?float3(0,0,-1):float3(0.6,0,-0.8);
    float depth=test==3?0:0.25;
    if(test==2)uv.x=0.99;
    ParallaxTraceHit hit;
    bool found=tracePrimaryParallaxHeightMap(heightTex,float2(0),float2(1),uv,uv,0,
        dir,float3(1,0,0),float3(0,1,0),float3(0,0,1),depth,0u,32,hit);
    Ptr<float4>(pc.output)[test]=float4(hit.uv,hit.t,found?1:0);
}
