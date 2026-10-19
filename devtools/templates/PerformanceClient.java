package dev.comfyfluffy.caustica.rt.terrain;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import dev.comfyfluffy.caustica.CausticaConfig;
import dev.comfyfluffy.caustica.rt.*;
import net.minecraft.client.Screenshot;
import java.nio.file.*;
public class ValidationClient implements ClientModInitializer {
 static ValidationClient active;
 int ticks,phase,shots;long mark,start=System.nanoTime(),lastStep;boolean measuring;
 void log(String s)throws Exception{var f=RtComposite.class.getDeclaredField("frameCounter");f.setAccessible(true);s="time="+java.time.Instant.now()+" frame="+f.getLong(RtComposite.INSTANCE)+" "+s;Files.writeString(Path.of("lighting-progress.txt"),s+"\n",StandardOpenOption.CREATE,StandardOpenOption.APPEND);}
 void command(net.minecraft.client.Minecraft mc,String s){var server=mc.getSingleplayerServer();server.execute(()->server.getCommands().performPrefixedCommand(server.createCommandSourceStack(),s));}
 void shot(net.minecraft.client.Minecraft mc,String name){Screenshot.grab(mc.gameDirectory,name,mc.gameRenderer.mainRenderTarget(),1,m->{});}
 boolean capture(String name)throws Exception{var mc=net.minecraft.client.Minecraft.getInstance();log("Capture "+name+" camera="+mc.player.position()+" yaw="+mc.player.getYRot()+" pitch="+mc.player.getXRot());return RtComposite.INSTANCE.exportLightingSignals(Path.of("signals-locked",name));}
 void mode(String provider){RtReconstructionPolicy.select(provider);mark=System.nanoTime();}
 void startWorld(net.minecraft.client.Minecraft mc){mc.options.pauseOnLostFocus=false;mc.options.renderDistance().set(6);mc.options.inactivityFpsLimit().set(net.minecraft.client.InactivityFpsLimit.MINIMIZED);
 CausticaConfig.Rt.Composite.SPP.set(1);CausticaConfig.Rt.Composite.MAX_BOUNCES.set(2);
 CausticaConfig.Rt.Volumetric.CLOUD_MODE.set("off");CausticaConfig.Rt.Volumetric.LIGHT.set(false);
 CausticaConfig.Rt.Volumetric.LIGHT_MODE.set("radiance");CausticaConfig.Rt.Volumetric.CLOUD_BVH.set(false);
 CausticaConfig.Rt.IndirectCache.PROVIDER.set("off");
 CausticaConfig.Rt.DepthOfField.ENABLED.set(false);CausticaConfig.Rt.MotionBlur.ENABLED.set(false);
 CausticaConfig.Rt.Lens.ENABLED.set(false);CausticaConfig.Rt.Fg.ENABLED.set(false);
 CausticaConfig.Rt.Lights.RESTIR_PT.set(false);CausticaConfig.Rt.PostProcessing.PARALLAX.set(true);CausticaConfig.Rt.PostProcessing.PARALLAX_DEPTH.set(.5f);CausticaConfig.Rt.Lights.RESTIR_DI.set(false);CausticaConfig.Rt.Lights.RESTIR_GI.set(false);CausticaConfig.Rt.DlssRr.QUALITY.set(5);
 CausticaConfig.Rt.Exposure.MODE.set("manual");CausticaConfig.Rt.Exposure.MANUAL_EV.set(-4f);
 CausticaConfig.Rt.Reconstruction.NRD_METHOD.set("reblur");
 boolean resume=Boolean.getBoolean("caustica.validation.resumeRr");CausticaConfig.Rt.Lights.RESTIR_PT.set(resume);mode(resume?"dlss":"fsr");phase=1;mc.createWorldOpenFlows().openWorld("Synthetic Validation",()->{});}
 public void onInitializeClient(){active=this;
 var timer=java.util.concurrent.Executors.newSingleThreadScheduledExecutor(r->{var t=new Thread(r,"isolated-validation");t.setDaemon(true);return t;});
 timer.scheduleAtFixedRate(()->{var mc=net.minecraft.client.Minecraft.getInstance();mc.execute(()->step(mc));},5,1,java.util.concurrent.TimeUnit.SECONDS);
 }
 public static void freeze(){var mc=net.minecraft.client.Minecraft.getInstance();
 if(active==null||active.phase<2||mc.player==null)return;
 net.minecraft.client.KeyMapping.releaseAll();mc.options.setCameraType(net.minecraft.client.CameraType.FIRST_PERSON);
 mc.mouseHandler.releaseMouse();mc.player.setPos(.5,active.phase>=12?80:68,.5);mc.player.setYRot(-90);
 mc.player.setXRot(active.phase>=12?-12:10);
 mc.player.setOldPosAndRot();mc.player.setDeltaMovement(0,0,0);
 }
 void step(net.minecraft.client.Minecraft mc){try{
 if(mc.options==null||mc.gui.screen()==null && mc.level==null)return;
 if(System.nanoTime()-start>3600_000_000_000L)throw new AssertionError("Runtime timeout");
 if(++ticks==1)log("Validation first client tick");if(phase==0 && ticks>=15 && mc.gui.screen()!=null && mc.gui.screen().getClass().getSimpleName().equals("TitleScreen"))startWorld(mc);
 if(mc.level==null||mc.player==null){log("Waiting screen: "+(mc.gui.screen()==null?"none":mc.gui.screen().getClass().getSimpleName()));if(mc.gui.screen() instanceof net.minecraft.client.gui.screens.ConfirmScreen confirm){var cb=net.minecraft.client.gui.screens.ConfirmScreen.class.getDeclaredField("callback");cb.setAccessible(true);((it.unimi.dsi.fastutil.booleans.BooleanConsumer)cb.get(confirm)).accept(true);}if(mc.gui.screen() instanceof net.minecraft.client.gui.screens.BackupConfirmScreen backup){var cb=net.minecraft.client.gui.screens.BackupConfirmScreen.class.getDeclaredField("onProceed");cb.setAccessible(true);((net.minecraft.client.gui.screens.BackupConfirmScreen.Listener)cb.get(backup)).proceed(false,false);}return;}
 mc.player.getAbilities().flying=true;mc.player.setDeltaMovement(0,0,0);
 if(phase==1){phase=Boolean.getBoolean("caustica.validation.resumeRr")?10:2;mark=System.nanoTime();command(mc,"gamemode creative ValidationPlayer");
 command(mc,"fill -10 64 -10 26 77 10 minecraft:quartz_block");
 command(mc,"fill -9 65 -9 25 76 9 minecraft:air");
 command(mc,"fill -9 65 -9 25 65 9 minecraft:polished_basalt");
 command(mc,"fill -9 76 -9 25 76 9 minecraft:iron_block");
 for(int x=2;x<=22;x+=4){
   command(mc,"setblock "+x+" 73 -10 minecraft:sea_lantern");
   command(mc,"setblock "+x+" 73 10 minecraft:sea_lantern");
   command(mc,"setblock "+x+" 76 0 minecraft:glowstone");}
 command(mc,"fill 6 66 -3 6 73 -3 minecraft:gold_block");
 command(mc,"fill 12 66 3 12 73 3 minecraft:iron_block");
 command(mc,"item replace entity ValidationPlayer weapon.mainhand with minecraft:air");
 command(mc,"item replace entity ValidationPlayer weapon.offhand with minecraft:air");
 command(mc,"tp ValidationPlayer 0 68 0 -90 10");command(mc,"time set 18000");
 command(mc,"gamerule minecraft:advance_time false");mc.getSingleplayerServer().setWeatherParameters(100000,0,false,false);
 CausticaConfig.Rt.Volumetric.LIGHT_STRENGTH.set(0f);CausticaConfig.Rt.DepthOfField.ENABLED.set(false);
 command(mc,"fill 2 66 -4 2 72 4 minecraft:bricks");
 log("Height solver "+ParallaxProbe.run());
 log("Entered isolated PBR world");return;}
 var pipelineField=RtComposite.class.getDeclaredField("worldPipeline");pipelineField.setAccessible(true);
 if(pipelineField.get(RtComposite.INSTANCE)==null){mark=System.nanoTime();measuring=false;return;}
 long now=System.nanoTime();
 if(lastStep!=0 && now-lastStep>5_000_000_000L){mark=now;measuring=false;log("WARM_RESET phase="+phase);}
 lastStep=now;double elapsed=(now-mark)/1e9;
 String[] names={"","","nrd-pom-on","nrd-pom-off","nrd-pom-on-repeat","nrd-material-bypass","nrd-material-repeat","nrd-di","nrd-gi","nrd-pt","rr-pt","rr-baseline","outdoor-clear","outdoor-clouds","outdoor-clouds-fog","outdoor-default-fog","outdoor-post","terrain-updates"};
 if(elapsed<10)return;
 if(mc.getFramerateLimitTracker().getThrottleReason()!=com.mojang.blaze3d.platform.FramerateLimitTracker.FramerateThrottleReason.NONE)throw new AssertionError("Measurement frame limiter: "+mc.getFramerateLimitTracker().getThrottleReason());
 if(!measuring){log("MEASURE_BEGIN "+names[phase]+" limit="+mc.getFramerateLimitTracker().getFramerateLimit()+" reason=NONE");measuring=true;return;}
 if(phase==17 && elapsed<35 && ((int)elapsed)%4==0){int x=4+((int)elapsed%12);command(mc,"setblock "+x+" 78 3 minecraft:glowstone");command(mc,"setblock "+(x-1)+" 78 3 minecraft:air");}
 if(elapsed<35)return;
 log("MEASURE_END "+names[phase]);
 if(!capture(names[phase]))return;shot(mc,names[phase]+".png");
 if(Boolean.getBoolean("caustica.validation.transportOnly")) {
 switch(phase){
 case 2:CausticaConfig.Rt.Lights.RESTIR_PT.set(true);phase=9;break;
 case 9:CausticaConfig.Rt.Lights.RESTIR_PT.set(false);command(mc,"fill -10 66 -10 26 77 10 minecraft:air");command(mc,"time set 23500");CausticaConfig.Rt.Exposure.MANUAL_EV.set(0f);phase=12;break;
 case 12:CausticaConfig.Rt.Volumetric.CLOUD_MODE.set("radiance");CausticaConfig.Rt.Volumetric.CLOUD_SHADOWS.set(true);CausticaConfig.Rt.Volumetric.CLOUD_BVH.set(true);phase=13;break;
 case 13:log("PASS: transport subset");mc.stop();return;
 default:throw new AssertionError("Unexpected subset phase "+phase);
 }
 mark=System.nanoTime();lastStep=mark;measuring=false;return;
 }
 switch(phase){
 case 2:CausticaConfig.Rt.PostProcessing.PARALLAX.set(false);break;
 case 3:CausticaConfig.Rt.PostProcessing.PARALLAX.set(true);break;
 case 4:System.setProperty("caustica.rt.profileMaterialBypass","true");CausticaConfig.Rt.PostProcessing.PARALLAX.set(false);break;
 case 5:System.clearProperty("caustica.rt.profileMaterialBypass");break;
 case 6:CausticaConfig.Rt.PostProcessing.PARALLAX.set(true);CausticaConfig.Rt.Lights.RESTIR_DI.set(true);break;
 case 7:CausticaConfig.Rt.Lights.RESTIR_DI.set(false);CausticaConfig.Rt.Lights.RESTIR_GI.set(true);break;
 case 8:CausticaConfig.Rt.Lights.RESTIR_GI.set(false);CausticaConfig.Rt.Lights.RESTIR_PT.set(true);break;
 case 9:mode("dlss");break;
 case 10:CausticaConfig.Rt.Lights.RESTIR_PT.set(false);break;
 case 11:mode("fsr");command(mc,"fill -10 66 -10 26 77 10 minecraft:air");command(mc,"time set 23500");CausticaConfig.Rt.Exposure.MANUAL_EV.set(0f);break;
 case 12:CausticaConfig.Rt.Volumetric.CLOUD_MODE.set("radiance");CausticaConfig.Rt.Volumetric.CLOUD_SHADOWS.set(true);CausticaConfig.Rt.Volumetric.CLOUD_BVH.set(true);break;
 case 13:CausticaConfig.Rt.Volumetric.LIGHT.set(true);CausticaConfig.Rt.Volumetric.LIGHT_STRENGTH.set(.25f);mc.getSingleplayerServer().setWeatherParameters(0,100000,true,true);break;
 case 14:CausticaConfig.Rt.Volumetric.LIGHT_MODE.set("default");break;
 case 15:CausticaConfig.Rt.DepthOfField.ENABLED.set(true);CausticaConfig.Rt.Lens.ENABLED.set(true);CausticaConfig.Rt.MotionBlur.ENABLED.set(true);break;
 case 16:break;
 case 17:log("PASS: height probe and complete pass matrix");mc.stop();return;
 default:throw new AssertionError("Unexpected phase "+phase);
 }
 phase++;mark=System.nanoTime();lastStep=mark;measuring=false;
 }catch(Throwable e){try{Files.writeString(Path.of("lighting-failure.txt"),e.toString());}catch(Exception ignored){}e.printStackTrace();mc.stop();}}
}
