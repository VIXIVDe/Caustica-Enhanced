package dev.comfyfluffy.caustica.rt.terrain;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import dev.comfyfluffy.caustica.CausticaConfig;
import dev.comfyfluffy.caustica.rt.*;
import net.minecraft.client.Screenshot;
import java.nio.file.*;
public class ValidationClient implements ClientModInitializer {
 static ValidationClient active;
 int ticks,phase,shots;long mark,start=System.nanoTime();
 void log(String s)throws Exception{var f=RtComposite.class.getDeclaredField("frameCounter");f.setAccessible(true);s="frame="+f.getLong(RtComposite.INSTANCE)+" "+s;Files.writeString(Path.of("lighting-progress.txt"),s+"\n",StandardOpenOption.CREATE,StandardOpenOption.APPEND);}
 void command(net.minecraft.client.Minecraft mc,String s){var server=mc.getSingleplayerServer();server.execute(()->server.getCommands().performPrefixedCommand(server.createCommandSourceStack(),s));}
 void shot(net.minecraft.client.Minecraft mc,String name){Screenshot.grab(mc.gameDirectory,name,mc.gameRenderer.mainRenderTarget(),1,m->{});}
 boolean capture(String name)throws Exception{var mc=net.minecraft.client.Minecraft.getInstance();log("Capture "+name+" camera="+mc.player.position()+" yaw="+mc.player.getYRot()+" pitch="+mc.player.getXRot());return RtComposite.INSTANCE.exportLightingSignals(Path.of("signals-locked",name));}
 void mode(String provider){RtReconstructionPolicy.select(provider);mark=System.nanoTime();}
 void startWorld(net.minecraft.client.Minecraft mc){mc.options.pauseOnLostFocus=false;mc.options.renderDistance().set(6);
 CausticaConfig.Rt.Composite.SPP.set(1);CausticaConfig.Rt.Composite.MAX_BOUNCES.set(2);
 CausticaConfig.Rt.Volumetric.CLOUD_MODE.set("off");CausticaConfig.Rt.Volumetric.LIGHT.set(true);
 CausticaConfig.Rt.Volumetric.LIGHT_MODE.set("radiance");CausticaConfig.Rt.Volumetric.CLOUD_BVH.set(false);
 CausticaConfig.Rt.IndirectCache.PROVIDER.set("off");
 CausticaConfig.Rt.DepthOfField.ENABLED.set(false);CausticaConfig.Rt.MotionBlur.ENABLED.set(false);
 CausticaConfig.Rt.Lens.ENABLED.set(false);CausticaConfig.Rt.Fg.ENABLED.set(false);
 CausticaConfig.Rt.Lights.RESTIR_DI.set(false);CausticaConfig.Rt.Lights.RESTIR_GI.set(false);CausticaConfig.Rt.DlssRr.QUALITY.set(5);
 CausticaConfig.Rt.Exposure.MODE.set("manual");CausticaConfig.Rt.Exposure.MANUAL_EV.set(-4f);
 CausticaConfig.Rt.Reconstruction.NRD_METHOD.set("reblur");mode("fsr");phase=1;mc.createWorldOpenFlows().openWorld("Synthetic Validation",()->{});}
 public void onInitializeClient(){active=this;
 var timer=java.util.concurrent.Executors.newSingleThreadScheduledExecutor(r->{var t=new Thread(r,"isolated-validation");t.setDaemon(true);return t;});
 timer.scheduleAtFixedRate(()->{var mc=net.minecraft.client.Minecraft.getInstance();mc.execute(()->step(mc));},5,1,java.util.concurrent.TimeUnit.SECONDS);
 }
 public static void freeze(){var mc=net.minecraft.client.Minecraft.getInstance();
 if(active==null||active.phase<2||mc.player==null)return;
 net.minecraft.client.KeyMapping.releaseAll();mc.options.setCameraType(net.minecraft.client.CameraType.FIRST_PERSON);
 mc.mouseHandler.releaseMouse();mc.player.setPos(.5,68,.5);mc.player.setYRot(-90);
 mc.player.setXRot(active.phase>=9?-30:10);
 mc.player.setOldPosAndRot();mc.player.setDeltaMovement(0,0,0);
 }
 void step(net.minecraft.client.Minecraft mc){try{
 if(mc.options==null||mc.gui.screen()==null && mc.level==null)return;
 if(System.nanoTime()-start>1100_000_000_000L)throw new AssertionError("Runtime timeout");
 if(++ticks==1)log("Validation first client tick");if(phase==0 && ticks>=15 && mc.gui.screen()!=null && mc.gui.screen().getClass().getSimpleName().equals("TitleScreen"))startWorld(mc);
 if(mc.level==null||mc.player==null){log("Waiting screen: "+(mc.gui.screen()==null?"none":mc.gui.screen().getClass().getSimpleName()));if(mc.gui.screen() instanceof net.minecraft.client.gui.screens.ConfirmScreen confirm){var cb=net.minecraft.client.gui.screens.ConfirmScreen.class.getDeclaredField("callback");cb.setAccessible(true);((it.unimi.dsi.fastutil.booleans.BooleanConsumer)cb.get(confirm)).accept(true);}if(mc.gui.screen() instanceof net.minecraft.client.gui.screens.BackupConfirmScreen backup){var cb=net.minecraft.client.gui.screens.BackupConfirmScreen.class.getDeclaredField("onProceed");cb.setAccessible(true);((net.minecraft.client.gui.screens.BackupConfirmScreen.Listener)cb.get(backup)).proceed(false,false);}return;}
 mc.player.getAbilities().flying=true;mc.player.setDeltaMovement(0,0,0);
 if(phase==1){phase=2;mark=System.nanoTime();command(mc,"gamemode creative ValidationPlayer");
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
 log("Entered isolated PBR world");return;}
 double elapsed=(System.nanoTime()-mark)/1e9;
 if(elapsed<(phase==2?35:16))return;
 String[] names={"","","nrd-ris","nrd-ris-repeat","nrd-gi","nrd-gi-repeat","rr-gi","rr-gi-repeat","volume-room","volume-noon","volume-dusk","volume-night"};
 if(phase<names.length){if(!capture(names[phase]))return;shot(mc,names[phase]+".png");
     log(ValidationProbe.focus());
     if(CausticaConfig.Rt.Lights.RESTIR_GI.get())log("GI GPU "+ValidationProbe.gi());
     log("Rendered "+names[phase]);}
 switch(phase){
 case 2:break;
 case 3:CausticaConfig.Rt.Lights.RESTIR_GI.set(true);break;
 case 4:break;
 case 5:mode("dlss");break;
 case 6:break;
 case 7:CausticaConfig.Rt.Lights.RESTIR_GI.set(false);CausticaConfig.Rt.Volumetric.LIGHT_STRENGTH.set(.5f);break;
 case 8:
     command(mc,"fill -10 64 -10 26 77 10 minecraft:air");
     command(mc,"fill -9 65 -9 25 65 9 minecraft:quartz_block");
     command(mc,"fill 15 66 -5 17 76 5 minecraft:quartz_block");
     command(mc,"time set 6000");break;
 case 9:command(mc,"time set 12500");break;
 case 10:command(mc,"time set 18000");break;
 case 11:log("PASS: PBR world NRD/RR RIS/GI and room/noon/dusk/night volume captures");mc.stop();return;
 default:mc.stop();return;
 }
 phase++;mark=System.nanoTime();
 }catch(Throwable e){try{Files.writeString(Path.of("lighting-failure.txt"),e.toString());}catch(Exception ignored){}e.printStackTrace();mc.stop();}}
}
