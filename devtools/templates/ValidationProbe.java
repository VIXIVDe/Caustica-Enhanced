package dev.comfyfluffy.caustica.rt.terrain;
import dev.comfyfluffy.caustica.rt.*;
import dev.comfyfluffy.caustica.rt.accel.*;
import org.lwjgl.system.*;
import org.lwjgl.vulkan.*;
import org.joml.*;
import java.nio.file.*;
public final class ValidationProbe {
    static Object field(Object owner,String name)throws Exception {var f=owner.getClass().getDeclaredField(name);f.setAccessible(true);return f.get(owner);}
    static void check(int r){if(r!=0)throw new AssertionError("probe Vulkan "+r);}
    static float[] image(RtImage image)throws Exception {
        var ctx=RtContext.currentOrNull();ctx.waitIdle();
        var result=ctx.createReadbackBuffer((long)image.width*image.height*4,"isolated depth probe");
        try {
            ctx.submitSync(cmd->{try(var stack=MemoryStack.stackPush()){
                var barriers=VkImageMemoryBarrier.calloc(1,stack);
                barriers.get(0).sType$Default().oldLayout(VK10.VK_IMAGE_LAYOUT_GENERAL).newLayout(VK10.VK_IMAGE_LAYOUT_GENERAL)
                    .srcAccessMask(VK10.VK_ACCESS_MEMORY_WRITE_BIT).dstAccessMask(VK10.VK_ACCESS_TRANSFER_READ_BIT)
                    .srcQueueFamilyIndex(-1).dstQueueFamilyIndex(-1).image(image.image);
                barriers.get(0).subresourceRange().aspectMask(VK10.VK_IMAGE_ASPECT_COLOR_BIT).levelCount(1).layerCount(1);
                VK10.vkCmdPipelineBarrier(cmd,VK10.VK_PIPELINE_STAGE_ALL_COMMANDS_BIT,VK10.VK_PIPELINE_STAGE_TRANSFER_BIT,0,null,null,barriers);
                var copy=VkBufferImageCopy.calloc(1,stack);copy.get(0).imageSubresource().aspectMask(VK10.VK_IMAGE_ASPECT_COLOR_BIT).layerCount(1);
                copy.get(0).imageExtent().set(image.width,image.height,1);
                VK10.vkCmdCopyImageToBuffer(cmd,image.image,VK10.VK_IMAGE_LAYOUT_GENERAL,result.handle,copy);
                var host=VkMemoryBarrier.calloc(1,stack).sType$Default().srcAccessMask(VK10.VK_ACCESS_TRANSFER_WRITE_BIT).dstAccessMask(VK10.VK_ACCESS_HOST_READ_BIT);
                VK10.vkCmdPipelineBarrier(cmd,VK10.VK_PIPELINE_STAGE_TRANSFER_BIT,VK10.VK_PIPELINE_STAGE_HOST_BIT,0,host,null,null);
            }});
            result.invalidate();float[] values=new float[image.width*image.height];
            for(int i=0;i<values.length;i++)values[i]=MemoryUtil.memGetFloat(result.mapped+4L*i);
            return values;
        }finally{result.destroy();}
    }
    static String focus()throws Exception {
        RtImage depth=(RtImage)field(RtComposite.INSTANCE,"gDepth");
        Object display=field(RtComposite.INSTANCE,"displayPipeline");
        float focus=image((RtImage)field(display,"focusImage"))[0];
        float center=image(depth)[depth.height/2*depth.width+depth.width/2];
        var matrix=(Matrix4f)field(RtComposite.INSTANCE,"frameInvViewProj");
        var p=matrix.transform(new Vector4f(0,0,focus,1));
        float distance=new Vector3f(p.x/p.w,p.y/p.w,p.z/p.w).length();
        int phase=ValidationClient.active.phase;
        return "FOCUS depth="+focus+" reticle="+center+" worldDistance="+distance;
    }
    static String gi()throws Exception {
        Object owner=field(RtComposite.INSTANCE,"restirGi");
        RtBuffer[] buffers=(RtBuffer[])field(owner,"temporal");
        int write=(int)field(owner,"writeIndex");RtBuffer records=buffers[1-write];
        var ctx=RtContext.currentOrNull();ctx.waitIdle();
        RtBuffer result=ctx.createBuffer(32,VK10.VK_BUFFER_USAGE_STORAGE_BUFFER_BIT,true,"isolated GI probe");
        long layout=0,pipeline=0,module=0;
        try(var stack=MemoryStack.stackPush()){
            MemoryUtil.memSet(result.mapped,0,32);result.flush();var handle=stack.mallocLong(1);
            var range=VkPushConstantRange.calloc(1,stack).stageFlags(VK10.VK_SHADER_STAGE_COMPUTE_BIT).size(24);
            check(VK10.vkCreatePipelineLayout(ctx.vk(),VkPipelineLayoutCreateInfo.calloc(stack).sType$Default().pPushConstantRanges(range),null,handle));layout=handle.get(0);
            byte[] bytes=Files.readAllBytes(Path.of(System.getProperty("caustica.validation.probeShader")));
            var code=MemoryUtil.memAlloc(bytes.length).put(bytes).flip();
            try{check(VK10.vkCreateShaderModule(ctx.vk(),VkShaderModuleCreateInfo.calloc(stack).sType$Default().pCode(code),null,handle));module=handle.get(0);}finally{MemoryUtil.memFree(code);}
            var stage=VkPipelineShaderStageCreateInfo.calloc(stack).sType$Default().stage(VK10.VK_SHADER_STAGE_COMPUTE_BIT).module(module).pName(stack.UTF8("main"));
            var info=VkComputePipelineCreateInfo.calloc(1,stack);info.get(0).sType$Default().stage(stage).layout(layout);
            check(VK10.vkCreateComputePipelines(ctx.vk(),0,info,null,handle));pipeline=handle.get(0);
            final long pipelineHandle=pipeline,layoutHandle=layout;
            int count=(int)(records.size/80);
            ctx.submitSync(cmd->{try(var commandStack=MemoryStack.stackPush()){
                var barrier=VkMemoryBarrier.calloc(1,commandStack).sType$Default().srcAccessMask(VK10.VK_ACCESS_MEMORY_WRITE_BIT).dstAccessMask(VK10.VK_ACCESS_SHADER_READ_BIT|VK10.VK_ACCESS_SHADER_WRITE_BIT);
                VK10.vkCmdPipelineBarrier(cmd,VK10.VK_PIPELINE_STAGE_ALL_COMMANDS_BIT,VK10.VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,0,barrier,null,null);
                var push=commandStack.calloc(24).putLong(records.deviceAddress).putLong(result.deviceAddress).putInt(count).putInt(0).flip();
                VK10.vkCmdBindPipeline(cmd,VK10.VK_PIPELINE_BIND_POINT_COMPUTE,pipelineHandle);
                VK10.vkCmdPushConstants(cmd,layoutHandle,VK10.VK_SHADER_STAGE_COMPUTE_BIT,0,push);
                VK10.vkCmdDispatch(cmd,(count+63)/64,1,1);
                barrier.get(0).srcAccessMask(VK10.VK_ACCESS_SHADER_WRITE_BIT).dstAccessMask(VK10.VK_ACCESS_HOST_READ_BIT);
                VK10.vkCmdPipelineBarrier(cmd,VK10.VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,VK10.VK_PIPELINE_STAGE_HOST_BIT,0,barrier,null,null);
            }});
            result.invalidate();int ready=MemoryUtil.memGetInt(result.mapped),lit=MemoryUtil.memGetInt(result.mapped+4),reused=MemoryUtil.memGetInt(result.mapped+8),aged=MemoryUtil.memGetInt(result.mapped+12),bad=MemoryUtil.memGetInt(result.mapped+16);
            if(ready==0 || lit==0 || bad!=0)throw new AssertionError("Inactive GI: "+ready+","+lit+","+reused+","+aged+","+bad);
            return "ready="+ready+" lit="+lit+" reused="+reused+" age="+aged+" nonfinite="+bad;
        }finally{if(pipeline!=0)VK10.vkDestroyPipeline(ctx.vk(),pipeline,null);if(module!=0)VK10.vkDestroyShaderModule(ctx.vk(),module,null);if(layout!=0)VK10.vkDestroyPipelineLayout(ctx.vk(),layout,null);result.destroy();}
    }
}
