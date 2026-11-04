package dev.masking.probe

import android.app.Activity
import android.graphics.Color
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.text.SpannableString
import android.text.Spanned
import android.text.style.ForegroundColorSpan
import android.widget.ArrayAdapter
import android.widget.LinearLayout
import android.widget.ListView
import android.widget.TextView

/** Test screen for the cover-gap test: the word ZQXJ is drawn in pure magenta so video frames can be checked for it.
 *  Top line: the word appears and disappears every 1.5 s ("new text"). Below: a long list to fling ("scrolling"). */
class TestActivity : Activity() {
    private val main = Handler(Looper.getMainLooper())

    private fun marked(s: String) = SpannableString(s).apply {
        val i = s.indexOf(WORD)
        if (i >= 0) setSpan(ForegroundColorSpan(Color.MAGENTA), i, i + WORD.length, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
    }

    override fun onCreate(state: Bundle?) {
        super.onCreate(state)
        val top = TextView(this).apply { textSize = 28f; setPadding(40, 420, 40, 40) /* Android 15 draws behind the title bar: start below it */; setBackgroundColor(Color.WHITE); setTextColor(Color.BLACK) }
        val rows = (1..400).map { if (it % 3 == 0) marked("Row $it some text $WORD more text") else "Row $it plain text only" }
        val list = ListView(this).apply {
            adapter = object : ArrayAdapter<CharSequence>(this@TestActivity, android.R.layout.simple_list_item_1, rows) {
                override fun getView(p: Int, v: android.view.View?, g: android.view.ViewGroup) =
                    (super.getView(p, v, g) as TextView).apply { textSize = 24f; setTextColor(Color.BLACK) }
            }
            setBackgroundColor(Color.WHITE)
        }
        setContentView(LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; addView(top); addView(list) })
        var on = false
        main.post(object : Runnable {
            override fun run() {
                on = !on; top.text = if (on) marked("New message $WORD here") else "No message"
                main.postDelayed(this, 1500)
            }
        })
    }

    companion object { const val WORD = "ZQXJ" }
}
