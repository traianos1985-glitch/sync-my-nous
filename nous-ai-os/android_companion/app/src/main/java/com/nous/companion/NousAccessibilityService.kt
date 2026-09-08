package com.nous.companion

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.GestureDescription
import android.graphics.Path
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo

class NousAccessibilityService : AccessibilityService() {

    companion object {
        var instance: NousAccessibilityService? = null
    }

    override fun onServiceConnected() {
        super.onServiceConnected()
        instance = this
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {}

    override fun onInterrupt() {}

    override fun onDestroy() {
        super.onDestroy()
        if (instance === this) {
            instance = null
        }
    }

    fun pressBack(): Boolean {
        return performGlobalAction(GLOBAL_ACTION_BACK)
    }

    fun pressHome(): Boolean {
        return performGlobalAction(GLOBAL_ACTION_HOME)
    }

    fun tap(x: Float, y: Float): Boolean {
        val path = Path()
        path.moveTo(x, y)

        val gesture = GestureDescription.Builder()
            .addStroke(GestureDescription.StrokeDescription(path, 0, 80))
            .build()

        return dispatchGesture(gesture, null, null)
    }

    fun rootSummary(): String {
        val root: AccessibilityNodeInfo = rootInActiveWindow ?: return "NO_ROOT"
        return summarize(root, 0)
    }

    private fun summarize(node: AccessibilityNodeInfo, depth: Int): String {
        if (depth > 4) return ""
        val text = node.text ?: ""
        val desc = node.contentDescription ?: ""
        val cls = node.className ?: ""
        val viewId = node.viewIdResourceName ?: ""
        val clickable = node.isClickable
        val enabled = node.isEnabled

        val line = "depth=$depth class=$cls text=$text desc=$desc id=$viewId clickable=$clickable enabled=$enabled\n"

        val children = StringBuilder()
        for (i in 0 until node.childCount) {
            node.getChild(i)?.let {
                children.append(summarize(it, depth + 1))
            }
        }

        return line + children.toString()
    }
}
