"""Compositor-side cost estimate (headless EGL, same Mesa iris driver Hyprland uses):
window texture 1920x1080 -> shader downscale to 640x360 FBO -> readback, sync vs PBO-async.
Plus the mask pass: full-res window drawn with a 160x160 mask texture + pixelate shader."""
import time, json, numpy as np, moderngl
from pathlib import Path

ctx = moderngl.create_context(standalone=True, backend="egl")
W, H, w, h = 1920, 1080, 640, 360
src = ctx.texture((W, H), 4, np.random.randint(0, 255, (H, W, 4), np.uint8).tobytes())
src.filter = (moderngl.LINEAR, moderngl.LINEAR)
small = ctx.framebuffer([ctx.texture((w, h), 4)])
full = ctx.framebuffer([ctx.texture((W, H), 4)])
mask = ctx.texture((160, 160), 1, ((np.random.rand(160, 160) > 0.7) * 255).astype(np.uint8).tobytes())
mask.filter = (moderngl.LINEAR, moderngl.LINEAR)
VS = "#version 330\nin vec2 p; out vec2 uv; void main(){uv=p*.5+.5; gl_Position=vec4(p,0,1);}"
down = ctx.program(vertex_shader=VS, fragment_shader="""#version 330
uniform sampler2D t; in vec2 uv; out vec4 o; void main(){o=texture(t,uv);}""")
maskp = ctx.program(vertex_shader=VS, fragment_shader="""#version 330
uniform sampler2D t; uniform sampler2D m; uniform vec2 sz; in vec2 uv; out vec4 o;
void main(){ float k = texture(m, uv).r;                       // dilated mask, bilinear-feathered
  vec2 cell = floor(uv*sz/24.)*24./sz;                          // 24 px pixelation blocks
  o = mix(texture(t,uv), texture(t,cell), step(0.5,k)); }""")
maskp["t"] = 0; maskp["m"] = 1; maskp["sz"] = (W, H)
quad = ctx.buffer(np.array([-1, -1, 1, -1, -1, 1, 1, 1], "f4"))
vd, vm = ctx.vertex_array(down, quad, "p"), ctx.vertex_array(maskp, quad, "p")
pbo = ctx.buffer(reserve=w * h * 4)

def timeit(fn, n=300):
    for _ in range(20): fn()
    ctx.finish(); ts = []
    for _ in range(n):
        t0 = time.perf_counter(); fn(); ts.append((time.perf_counter() - t0) * 1e3)
    return dict(p50=float(np.percentile(ts, 50)), p95=float(np.percentile(ts, 95)), max=float(max(ts)))

def downscale():
    small.use(); src.use(0); vd.render(moderngl.TRIANGLE_STRIP)
def sync_read():
    downscale(); small.read(components=4)                         # glReadPixels to CPU memory, blocks
state = {"pending": False}
def async_read():                                                  # read last frame's PBO, kick this frame's
    if state["pending"]: pbo.read()
    downscale(); small.read_into(pbo, components=4); state["pending"] = True
def mask_pass():
    full.use(); src.use(0); mask.write(((np.random.rand(160, 160) > 0.7) * 255).astype(np.uint8).tobytes()); mask.use(1)
    vm.render(moderngl.TRIANGLE_STRIP); ctx.finish()

import subprocess
out = dict(gl=ctx.info["GL_RENDERER"],
           contended=subprocess.run(["pgrep", "-f", "render.py"], capture_output=True).returncode == 0,
           downscale_plus_sync_readback_ms=timeit(sync_read),
           downscale_plus_pbo_async_readback_ms=timeit(async_read),
           mask_upload_plus_pixelate_pass_1080p_ms=timeit(mask_pass))
print(json.dumps(out, indent=1))
Path("results/readback.json").write_text(json.dumps(out, indent=1))
