package dev.comfyfluffy.caustica.validation.mixin;
import dev.comfyfluffy.caustica.rt.terrain.ValidationClient;
import net.minecraft.client.renderer.GameRenderer;
import net.minecraft.client.DeltaTracker;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
@Mixin(GameRenderer.class)
public class BenchmarkCameraMixin {
 @Inject(method="renderLevel(Lnet/minecraft/client/DeltaTracker;)V",at=@At("HEAD"))
 private void lock(DeltaTracker dt,CallbackInfo ci){ValidationClient.freeze();}
}
