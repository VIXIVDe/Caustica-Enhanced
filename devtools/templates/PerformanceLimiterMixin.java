package dev.comfyfluffy.caustica.validation.mixin;
import com.mojang.blaze3d.platform.FramerateLimitTracker;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
/** The isolated performance client must render independently of desktop window state. */
@Mixin(FramerateLimitTracker.class)
public class PerformanceLimiterMixin {
 @Inject(method="getThrottleReason",at=@At("HEAD"),cancellable=true)
 private void noDesktopThrottle(CallbackInfoReturnable<FramerateLimitTracker.FramerateThrottleReason> ci){
  if(Boolean.getBoolean("caustica.validation.performance"))ci.setReturnValue(FramerateLimitTracker.FramerateThrottleReason.NONE);
 }
}
