package com.ihsansoft.wexumvpn

/**
 * Internal contract for a future independently reviewed transport. This does not expose a
 * connected callback; no implementation or live network transport is bundled in this project.
 * The service, not UI or backend-supplied strings, must own tunnel verification.
 */
internal interface VpnEngine {
    fun start(session: Long, emit: (session: Long, signal: EngineSignal) -> Unit)
    fun stop()
}
