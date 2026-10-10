package com.nous.companion

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.Process
import android.util.Log

class CommandReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context?, intent: Intent?) {
        // This receiver remains exported because the companion is driven through
        // explicit adb broadcasts. Restrict callers to adb shell and this app;
        // ordinary third-party apps must not be able to tap or navigate the UI.
        val senderUid = sendingUid
        if (senderUid != Process.SHELL_UID && senderUid != Process.myUid()) {
            Log.w("NOUS_COMPANION", "Rejected command broadcast from untrusted uid")
            return
        }

        if (intent?.action != ACTION_COMMAND) {
            Log.w("NOUS_COMPANION", "Rejected command with unexpected action")
            return
        }

        val command = intent.getStringExtra("command") ?: return
        if (command !in ALLOWED_COMMANDS) {
            CompanionState.update("rejected", "ERROR: unknown command")
            Log.w("NOUS_COMPANION", "Rejected unknown command")
            return
        }

        val service = NousAccessibilityService.instance
        if (service == null) {
            CompanionState.update(command, "ERROR: Accessibility service not connected")
            Log.w("NOUS_COMPANION", "Accessibility service not connected")
            return
        }

        val result = when (command) {
            "back" -> "back=${service.pressBack()}"
            "home" -> "home=${service.pressHome()}"
            "tap" -> {
                val x = intent.getFloatExtra("x", -1f)
                val y = intent.getFloatExtra("y", -1f)
                if (x.isFinite() && y.isFinite() && x >= 0f && y >= 0f) {
                    "tap=${service.tap(x, y)} x=$x y=$y"
                } else {
                    "ERROR: invalid tap coordinates"
                }
            }
            "ui_tree" -> service.rootSummary()
            "state" -> CompanionState.summary()
            else -> "ERROR: unknown command"
        }

        CompanionState.update(command, result)
        // UI-tree text can contain private on-screen information. Never copy it
        // into logcat, where unrelated apps/tools may collect it.
        Log.i("NOUS_COMPANION", "Processed allowlisted command: $command")
    }

    companion object {
        private const val ACTION_COMMAND = "com.nous.companion.COMMAND"
        private val ALLOWED_COMMANDS = setOf("back", "home", "tap", "ui_tree", "state")
    }
}
