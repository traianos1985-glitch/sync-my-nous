package com.nous.companion

object CompanionState {
    var lastCommand: String = "none"
    var lastResult: String = "none"
    var lastUpdated: Long = 0L

    fun update(command: String, result: String) {
        lastCommand = command
        lastResult = result
        lastUpdated = System.currentTimeMillis()
    }

    fun summary(): String {
        return "lastCommand=$lastCommand\nlastUpdated=$lastUpdated\nlastResult=\n$lastResult"
    }
}
