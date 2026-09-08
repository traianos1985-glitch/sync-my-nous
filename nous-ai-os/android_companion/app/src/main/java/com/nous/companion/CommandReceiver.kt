package com.nous.companion

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log

class CommandReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context?, intent: Intent?) {
        val command = intent?.getStringExtra("command") ?: return
        val service = NousAccessibilityService.instance

        Log.i("NOUS_COMPANION", "Received command: $command")

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
                if (x >= 0 && y >= 0) {
                    "tap=${service.tap(x, y)} x=$x y=$y"
                } else {
                    "ERROR: invalid tap coordinates x=$x y=$y"
                }
            }
            "ui_tree" -> service.rootSummary()
            "state" -> CompanionState.summary()
            else -> "ERROR: unknown command $command"
        }

        CompanionState.update(command, result)
        Log.i("NOUS_COMPANION_RESULT", result.take(3500))
    }
}
