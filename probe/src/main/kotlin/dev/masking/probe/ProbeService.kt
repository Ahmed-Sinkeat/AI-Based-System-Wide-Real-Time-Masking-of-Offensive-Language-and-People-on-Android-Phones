package dev.masking.probe

import android.accessibilityservice.AccessibilityService
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.PixelFormat
import android.graphics.Rect
import android.graphics.RectF
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import android.util.Log
import android.view.Display
import android.view.View
import android.view.WindowManager
import android.view.WindowManager.LayoutParams as LP
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo as Node
import android.view.accessibility.AccessibilityWindowInfo

/** Logs counts only, never the text itself (tag PROBE). Modes are set from the laptop:
 *  adb shell am broadcast -a probe.CMD --es cmd boxes|gap|shot|off */
class ProbeService : AccessibilityService() {
    private val main = Handler(Looper.getMainLooper())
    private lateinit var cover: CoverView
    private var mode = "off"
    private val lastLog = HashMap<String, Long>()

    private val rx = object : BroadcastReceiver() {
        override fun onReceive(c: Context, i: Intent) {
            val cmd = i.getStringExtra("cmd") ?: return
            Log.i(T, "CMD $cmd")
            if (cmd == "shot") shotTest() else { mode = cmd; cover.set(emptyList()) }
        }
    }

    override fun onServiceConnected() {
        cover = CoverView(this)
        val lp = LP(LP.MATCH_PARENT, LP.MATCH_PARENT, LP.TYPE_ACCESSIBILITY_OVERLAY,
            LP.FLAG_NOT_TOUCHABLE or LP.FLAG_NOT_FOCUSABLE or LP.FLAG_LAYOUT_IN_SCREEN or LP.FLAG_LAYOUT_NO_LIMITS,
            PixelFormat.TRANSLUCENT).apply { layoutInDisplayCutoutMode = LP.LAYOUT_IN_DISPLAY_CUTOUT_MODE_ALWAYS }
        getSystemService(WindowManager::class.java).addView(cover, lp)
        registerReceiver(rx, IntentFilter("probe.CMD"), Context.RECEIVER_EXPORTED)
        Log.i(T, "CONNECTED")
    }

    override fun onAccessibilityEvent(e: AccessibilityEvent) {
        val pkg = e.packageName?.toString() ?: return
        when (mode) {
            "gap" -> if (pkg == packageName) gap(e)
            "boxes" -> if (pkg != packageName) boxes(pkg)
        }
    }

    override fun onInterrupt() {}

    /** Test 1: does this app share text, and per-letter boxes for it? */
    private fun boxes(pkg: String) {
        val now = SystemClock.uptimeMillis()
        if (now - (lastLog[pkg] ?: 0) < 2000) return // ponytail: one sample per app every 2 s is enough for a yes/no
        lastLog[pkg] = now
        val root = rootInActiveWindow ?: return
        if (root.packageName?.toString() != pkg) return
        val all = ArrayList<Node>(); val q = ArrayDeque(listOf(root))
        while (q.isNotEmpty() && all.size < 3000) { val n = q.removeFirst(); all += n; for (i in 0 until n.childCount) n.getChild(i)?.let(q::add) }
        val text = all.filter { !it.text.isNullOrBlank() }
        val desc = all.count { it.text.isNullOrBlank() && !it.contentDescription.isNullOrBlank() }
        val withKey = text.filter { KEY in it.availableExtraData }
        var got = 0; var tried = 0
        val t0 = SystemClock.elapsedRealtimeNanos()
        for (n in withKey.filter { it.isVisibleToUser }.take(5)) {
            tried++
            if (charBoxes(n, 0, minOf(n.text.length, 20)).isNotEmpty()) got++
        }
        val ms = (SystemClock.elapsedRealtimeNanos() - t0) / 1e6
        Log.i(T, "BOXES pkg=$pkg nodes=${all.size} textNodes=${text.size} descOnly=$desc withBoxKey=${withKey.size} tried=$tried gotBoxes=$got ms=${"%.1f".format(ms)}")
    }

    private fun charBoxes(n: Node, start: Int, len: Int): List<RectF> {
        val args = Bundle().apply { putInt(Node.EXTRA_DATA_TEXT_CHARACTER_LOCATION_ARG_START_INDEX, start); putInt(Node.EXTRA_DATA_TEXT_CHARACTER_LOCATION_ARG_LENGTH, len) }
        if (!n.refreshWithExtraData(KEY, args)) return emptyList()
        return n.extras.getParcelableArray(KEY, RectF::class.java)?.filterNotNull() ?: emptyList()
    }

    /** Test 2: cover every visible ZQXJ on our test screen, on every event (no waiting). */
    private fun gap(e: AccessibilityEvent) {
        val t0 = SystemClock.elapsedRealtimeNanos()
        val root = rootInActiveWindow ?: return
        val rects = ArrayList<RectF>()
        for (n in root.findAccessibilityNodeInfosByText(TestActivity.WORD)) {
            if (!n.isVisibleToUser) continue
            val s = n.text?.toString() ?: continue
            val i = s.indexOf(TestActivity.WORD); if (i < 0) continue
            val b = charBoxes(n, i, TestActivity.WORD.length)
            if (b.isEmpty()) continue
            rects += RectF(b.minOf { it.left }, b.minOf { it.top }, b.maxOf { it.right }, b.maxOf { it.bottom }).apply { inset(-6f, -6f) }
        }
        cover.set(rects)
        Log.i(T, "GAP type=${e.eventType} covers=${rects.size} ms=${"%.2f".format((SystemClock.elapsedRealtimeNanos() - t0) / 1e6)}")
    }

    /** Test 5: window picture. Works? How fast? Rate limit? Are our covers in it (they must not be)? */
    private fun shotTest() {
        val w = windows.firstOrNull { it.isActive && it.type == AccessibilityWindowInfo.TYPE_APPLICATION } ?: windows.firstOrNull { it.isActive }
        if (w == null) { Log.i(T, "SHOT no active window"); return }
        val pkg = w.root?.packageName ?: "?"
        val bounds = Rect().also(w::getBoundsInScreen)
        cover.test = Rect(bounds.centerX() - 150, bounds.centerY() - 150, bounds.centerX() + 150, bounds.centerY() + 150); cover.invalidate()
        main.postDelayed({
            fun take(tag: String, then: () -> Unit) {
                val t0 = SystemClock.elapsedRealtime()
                takeScreenshotOfWindow(w.id, mainExecutor, object : TakeScreenshotCallback {
                    override fun onSuccess(r: ScreenshotResult) {
                        val ms = SystemClock.elapsedRealtime() - t0
                        val bmp = Bitmap.wrapHardwareBuffer(r.hardwareBuffer, r.colorSpace)!!.copy(Bitmap.Config.ARGB_8888, false)
                        r.hardwareBuffer.close()
                        Log.i(T, "SHOT $tag pkg=$pkg ok ms=$ms size=${bmp.width}x${bmp.height} window=${bounds.width()}x${bounds.height()} " +
                            "ourCoverInPicture=${isMagenta(bmp.getPixel(bmp.width / 2, bmp.height / 2))} darkShare=${"%.2f".format(dark(bmp))}")
                        then()
                    }
                    override fun onFailure(code: Int) { Log.i(T, "SHOT $tag pkg=$pkg FAILED code=$code ms=${SystemClock.elapsedRealtime() - t0}"); then() }
                })
            }
            // first picture, then one at once (expect the rate-limit error), then one after 400 ms (expect ok)
            take("first") { take("immediate") { main.postDelayed({ take("after400ms") {
                takeScreenshot(Display.DEFAULT_DISPLAY, mainExecutor, object : TakeScreenshotCallback {
                    override fun onSuccess(r: ScreenshotResult) {
                        val bmp = Bitmap.wrapHardwareBuffer(r.hardwareBuffer, r.colorSpace)!!.copy(Bitmap.Config.ARGB_8888, false)
                        r.hardwareBuffer.close()
                        Log.i(T, "SHOT fullDisplay ourCoverInPicture=${isMagenta(bmp.getPixel(bounds.centerX(), bounds.centerY()))}")
                        cover.test = null; cover.invalidate()
                    }
                    override fun onFailure(code: Int) { Log.i(T, "SHOT fullDisplay FAILED code=$code"); cover.test = null; cover.invalidate() }
                })
            } }, 400) } }
        }, 300)
    }

    private fun isMagenta(c: Int) = Color.red(c) > 200 && Color.green(c) < 80 && Color.blue(c) > 200
    private fun dark(b: Bitmap): Double {
        var d = 0; var n = 0
        for (y in 0 until b.height step 40) for (x in 0 until b.width step 40) { n++; val c = b.getPixel(x, y); if (Color.red(c) + Color.green(c) + Color.blue(c) < 30) d++ }
        return d.toDouble() / n
    }

    /** One full-screen overlay; covers are black boxes in screen coordinates. `test` is a magenta box for the picture test. */
    class CoverView(c: Context) : View(c) {
        private var rects: List<RectF> = emptyList()
        var test: Rect? = null
        private val black = Paint().apply { color = Color.BLACK }
        private val magenta = Paint().apply { color = Color.MAGENTA }
        private val loc = IntArray(2)
        fun set(r: List<RectF>) { if (r != rects) { rects = r; invalidate() } }
        override fun onDraw(c: Canvas) {
            getLocationOnScreen(loc)
            c.translate(-loc[0].toFloat(), -loc[1].toFloat())
            for (r in rects) c.drawRect(r, black)
            test?.let { c.drawRect(it, magenta) }
        }
    }

    companion object {
        const val T = "PROBE"
        val KEY: String = Node.EXTRA_DATA_TEXT_CHARACTER_LOCATION_KEY
    }
}
