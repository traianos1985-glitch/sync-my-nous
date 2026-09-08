package com.nous.companion

import android.app.Activity
import android.os.Bundle
import android.provider.Settings
import android.content.ComponentName
import android.content.Intent
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView

class MainActivity : Activity() {

    private lateinit var statusView: TextView
    private lateinit var resultView: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val scroll = ScrollView(this)
        val layout = LinearLayout(this)
        layout.orientation = LinearLayout.VERTICAL
        layout.setPadding(32, 32, 32, 32)

        val title = TextView(this)
        title.text = "NOUS Companion v3.1"
        title.textSize = 22f

        statusView = TextView(this)
        statusView.textSize = 16f

        resultView = TextView(this)
        resultView.textSize = 13f

        val settingsButton = Button(this)
        settingsButton.text = "Open Accessibility Settings"
        settingsButton.setOnClickListener {
            startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
        }

        val refreshButton = Button(this)
        refreshButton.text = "Refresh Status / Last Result"
        refreshButton.setOnClickListener {
            updateStatus()
        }

        layout.addView(title)
        layout.addView(statusView)
        layout.addView(settingsButton)
        layout.addView(refreshButton)
        layout.addView(resultView)

        scroll.addView(layout)
        setContentView(scroll)
        updateStatus()
    }

    override fun onResume() {
        super.onResume()
        updateStatus()
    }

    private fun updateStatus() {
        val enabled = isAccessibilityEnabled()
        val connected = NousAccessibilityService.instance != null

        statusView.text =
            "Accessibility setting enabled: $enabled\n" +
            "Service runtime connected: $connected\n"

        resultView.text = "\nLast Companion State:\n${CompanionState.summary()}"
    }

    private fun isAccessibilityEnabled(): Boolean {
        val expected = ComponentName(this, NousAccessibilityService::class.java).flattenToString()
        val enabledServices = Settings.Secure.getString(
            contentResolver,
            Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES
        ) ?: return false

        return enabledServices.split(":").any {
            it.equals(expected, ignoreCase = true)
        }
    }
}
