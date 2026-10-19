package dev.comfyfluffy.caustica.rt.terrain;
import dev.comfyfluffy.caustica.rt.*;
import org.lwjgl.vulkan.*;
import org.lwjgl.system.*;
import java.nio.file.*;
import java.util.*;

/** Executes the production Slang height solver on a controlled half-height texture. */
public final class ParallaxProbe {
    static void check(int r){if(r!=0)throw new AssertionError("Parallax probe Vulkan "+r);}
    public static String run() throws Exception {
        var ctx=RtContext.currentOrNull();ctx.waitIdle();
        byte[] pixels=new byte[16*16*4];
        for(int i=0;i<16*16;i++){pixels[4*i]=(byte)128;pixels[4*i+1]=(byte)128;pixels[4*i+2]=(byte)255;pixels[4*i+3]=(byte)128;}
        var type=Class.forName("dev.comfyfluffy.caustica.rt.material.RtMaterialPageTexture");
        var ctor=type.getDeclaredConstructors()[0];ctor.setAccessible(true);
        Object texture=ctor.newInstance(ctx,16,16,List.of(pixels),"height probe");
        var viewMethod=type.getDeclaredMethod("view");viewMethod.setAccessible(true);
        long view=(long)viewMethod.invoke(texture);
        var result=ctx.createBuffer(64,VK10.VK_BUFFER_USAGE_STORAGE_BUFFER_BIT,true,"height probe output");
        long sampler=0,descriptors=0,setLayout=0,layout=0,pipeline=0,module=0;
        try(var stack=MemoryStack.stackPush()) {
            var h=stack.mallocLong(1);
            check(VK10.vkCreateSampler(ctx.vk(),VkSamplerCreateInfo.calloc(stack).sType$Default()
                .magFilter(VK10.VK_FILTER_NEAREST).minFilter(VK10.VK_FILTER_NEAREST)
                .addressModeU(VK10.VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE)
                .addressModeV(VK10.VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE)
                .addressModeW(VK10.VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE),null,h));sampler=h.get(0);
            var binding=VkDescriptorSetLayoutBinding.calloc(1,stack).binding(0).descriptorCount(1)
                .descriptorType(VK10.VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER).stageFlags(VK10.VK_SHADER_STAGE_COMPUTE_BIT);
            check(VK10.vkCreateDescriptorSetLayout(ctx.vk(),VkDescriptorSetLayoutCreateInfo.calloc(stack).sType$Default().pBindings(binding),null,h));setLayout=h.get(0);
            var sizes=VkDescriptorPoolSize.calloc(1,stack).type(VK10.VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER).descriptorCount(1);
            check(VK10.vkCreateDescriptorPool(ctx.vk(),VkDescriptorPoolCreateInfo.calloc(stack).sType$Default().maxSets(1).pPoolSizes(sizes),null,h));descriptors=h.get(0);
            check(VK10.vkAllocateDescriptorSets(ctx.vk(),VkDescriptorSetAllocateInfo.calloc(stack).sType$Default().descriptorPool(descriptors).pSetLayouts(stack.longs(setLayout)),h));long set=h.get(0);
            var image=VkDescriptorImageInfo.calloc(1,stack).sampler(sampler).imageView(view).imageLayout(VK10.VK_IMAGE_LAYOUT_GENERAL);
            var write=VkWriteDescriptorSet.calloc(1,stack).sType$Default().dstSet(set).dstBinding(0).descriptorCount(1).descriptorType(VK10.VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER).pImageInfo(image);
            VK10.vkUpdateDescriptorSets(ctx.vk(),write,null);
            var range=VkPushConstantRange.calloc(1,stack).stageFlags(VK10.VK_SHADER_STAGE_COMPUTE_BIT).size(8);
            check(VK10.vkCreatePipelineLayout(ctx.vk(),VkPipelineLayoutCreateInfo.calloc(stack).sType$Default().pSetLayouts(stack.longs(setLayout)).pPushConstantRanges(range),null,h));layout=h.get(0);
            byte[] bytes=Files.readAllBytes(Path.of(System.getProperty("caustica.validation.parallaxShader")));
            var code=MemoryUtil.memAlloc(bytes.length).put(bytes).flip();
            try{check(VK10.vkCreateShaderModule(ctx.vk(),VkShaderModuleCreateInfo.calloc(stack).sType$Default().pCode(code),null,h));module=h.get(0);}finally{MemoryUtil.memFree(code);}
            var stage=VkPipelineShaderStageCreateInfo.calloc(stack).sType$Default().stage(VK10.VK_SHADER_STAGE_COMPUTE_BIT).module(module).pName(stack.UTF8("main"));
            var info=VkComputePipelineCreateInfo.calloc(1,stack);info.get(0).sType$Default().stage(stage).layout(layout);
            check(VK10.vkCreateComputePipelines(ctx.vk(),0,info,null,h));pipeline=h.get(0);
            final long p=pipeline,l=layout;
            ctx.submitSync(cmd->{try(var s=MemoryStack.stackPush()) {
                VK10.vkCmdBindPipeline(cmd,VK10.VK_PIPELINE_BIND_POINT_COMPUTE,p);
                VK10.vkCmdBindDescriptorSets(cmd,VK10.VK_PIPELINE_BIND_POINT_COMPUTE,l,0,s.longs(set),null);
                VK10.vkCmdPushConstants(cmd,l,VK10.VK_SHADER_STAGE_COMPUTE_BIT,0,s.malloc(8).putLong(result.deviceAddress).flip());
                VK10.vkCmdDispatch(cmd,4,1,1);
                var barrier=VkMemoryBarrier.calloc(1,s).sType$Default().srcAccessMask(VK10.VK_ACCESS_SHADER_WRITE_BIT).dstAccessMask(VK10.VK_ACCESS_HOST_READ_BIT);
                VK10.vkCmdPipelineBarrier(cmd,VK10.VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,VK10.VK_PIPELINE_STAGE_HOST_BIT,0,barrier,null,null);
            }});
            result.invalidate();float[][] values=new float[4][4];
            for(int i=0;i<4;i++)for(int j=0;j<4;j++){float v=MemoryUtil.memGetFloat(result.mapped+16L*i+4L*j);if(!Float.isFinite(v))throw new AssertionError("Nonfinite height probe");values[i][j]=v;}
            float expectedDepth=(127f/255)*.25f;
            if(values[0][3]!=1||Math.abs(values[0][2]-expectedDepth)>.002||Math.abs(values[0][0]-.5)>.001)throw new AssertionError("Normal height hit "+Arrays.toString(values[0]));
            if(values[1][3]!=1||Math.abs(values[1][0]-(.5+.75*expectedDepth))>.002)throw new AssertionError("Oblique height hit "+Arrays.toString(values[1]));
            if(values[2][0]<0||values[2][0]>1||values[3][3]!=0)throw new AssertionError("Height boundary/depth bypass");
            String report=Arrays.deepToString(values);Files.writeString(Path.of("parallax-probe.txt"),report);return "PASS "+report;
        } finally {
            if(pipeline!=0)VK10.vkDestroyPipeline(ctx.vk(),pipeline,null);
            if(module!=0)VK10.vkDestroyShaderModule(ctx.vk(),module,null);
            if(layout!=0)VK10.vkDestroyPipelineLayout(ctx.vk(),layout,null);
            if(descriptors!=0)VK10.vkDestroyDescriptorPool(ctx.vk(),descriptors,null);
            if(setLayout!=0)VK10.vkDestroyDescriptorSetLayout(ctx.vk(),setLayout,null);
            if(sampler!=0)VK10.vkDestroySampler(ctx.vk(),sampler,null);
            result.destroy();var destroy=type.getDeclaredMethod("destroy");destroy.setAccessible(true);destroy.invoke(texture);
        }
    }
}
