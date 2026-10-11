package com.nous.companion

import android.content.Context
import java.security.SecureRandom
import java.util.Base64

/**
 * Per-install secret used to authenticate explicit ADB broadcasts on every
 * supported Android version. Stored only in this app's private preferences.
 */
object PairingToken {
    private const val PREFS_NAME = "nous_companion_private"
    private const val TOKEN_KEY = "adb_pairing_token"
    private val TOKEN_PATTERN = Regex("^[A-Za-z0-9_-]{43}$")

    fun getOrCreate(context: Context): String {
        val preferences = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        val existing = preferences.getString(TOKEN_KEY, null)
        if (existing != null && TOKEN_PATTERN.matches(existing)) {
            return existing
        }

        val bytes = ByteArray(32)
        SecureRandom().nextBytes(bytes)
        val generated = Base64.getUrlEncoder().withoutPadding().encodeToString(bytes)
        // Persist synchronously: never accept a token that would change after process death.
        check(preferences.edit().putString(TOKEN_KEY, generated).commit()) {
            "pairing_token_persistence_failed"
        }
        return generated
    }

    fun matches(context: Context, candidate: String?): Boolean {
        if (candidate.isNullOrEmpty()) return false
        val expected = getOrCreate(context)
        return java.security.MessageDigest.isEqual(
            expected.toByteArray(Charsets.UTF_8),
            candidate.toByteArray(Charsets.UTF_8)
        )
    }
}
