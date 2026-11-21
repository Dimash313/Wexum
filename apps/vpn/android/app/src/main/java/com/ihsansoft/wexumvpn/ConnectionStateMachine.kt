package com.ihsansoft.wexumvpn

import java.util.concurrent.atomic.AtomicLong

/** The UI may read these phases. PROTECTED is intentionally unreachable in this scaffold. */
enum class ConnectionPhase {
    DISCONNECTED, AWAITING_CONSENT, PERMISSION_READY, CONNECTING, PROTECTED, INTERRUPTED, ERROR
}

enum class ConnectionFailure {
    PERMISSION_DENIED, PERMISSION_REVOKED, CONSENT_FLOW_FAILED, ENGINE_UNAVAILABLE, ENGINE_FAILED
}

data class ConnectionSnapshot(
    val phase: ConnectionPhase = ConnectionPhase.DISCONNECTED,
    val failure: ConnectionFailure? = null,
    val revision: Long = 0L,
)

/** No CONNECTED/VERIFIED event until independently reviewed tunnel verification exists. */
internal enum class EngineSignal { STARTING, INTERRUPTED, STOPPED, FAILED }

/**
 * Thread-safe process-local state. A UI actor cannot send engine events via UserPort.
 * Engine session identity is only a stale-callback guard, NEVER server-side authorization.
 */
class ConnectionStateMachine {
    private val lock = Any()
    private var snapshot = ConnectionSnapshot()
    private var pendingConsent: Long? = null
    private var activeEngineSession: Long? = null
    private val counter = AtomicLong(0L)
    private val listeners = LinkedHashMap<Long, () -> Unit>()

    val user: UserPort = UserPort()
    internal val service: ServicePort = ServicePort()

    fun current(): ConnectionSnapshot = synchronized(lock) { snapshot }

    /** Immediate notification and notifications on later state changes. Read current() when invoked. */
    fun observe(listener: () -> Unit): AutoCloseable {
        val key = counter.incrementAndGet()
        synchronized(lock) { listeners[key] = listener }
        listener()
        return AutoCloseable { synchronized(lock) { listeners.remove(key) } }
    }

    private inline fun <T> update(block: () -> T): T {
        val result: T
        val notifications: List<() -> Unit>
        synchronized(lock) {
            val previous = snapshot
            result = block()
            notifications = if (previous != snapshot) listeners.values.toList() else emptyList()
        }
        // Do not run listeners under the lock. Subscribers read the latest state.
        notifications.forEach { it() }
        return result
    }

    private fun change(phase: ConnectionPhase, failure: ConnectionFailure? = null) {
        if (snapshot.phase != phase || snapshot.failure != failure) {
            snapshot = ConnectionSnapshot(phase, failure, snapshot.revision + 1)
        }
    }

    /** Only OS-consent bookkeeping is accessible to the Activity. */
    inner class UserPort internal constructor() {
        fun beginConsent(): Long? = update {
            if (snapshot.phase == ConnectionPhase.AWAITING_CONSENT ||
                snapshot.phase == ConnectionPhase.CONNECTING ||
                snapshot.phase == ConnectionPhase.PROTECTED
            ) return@update null
            val attempt = counter.incrementAndGet()
            pendingConsent = attempt
            activeEngineSession = null
            change(ConnectionPhase.AWAITING_CONSENT)
            attempt
        }

        /** Caller MUST independently recheck VpnService.prepare(context) before reporting granted. */
        fun resolveConsent(attempt: Long, grantedByOs: Boolean): Boolean = update {
            if (snapshot.phase != ConnectionPhase.AWAITING_CONSENT || pendingConsent != attempt) {
                return@update false
            }
            pendingConsent = null
            if (grantedByOs) change(ConnectionPhase.PERMISSION_READY)
            else change(ConnectionPhase.ERROR, ConnectionFailure.PERMISSION_DENIED)
            true
        }

        fun consentLaunchFailed(attempt: Long): Boolean = update {
            if (snapshot.phase != ConnectionPhase.AWAITING_CONSENT || pendingConsent != attempt) {
                return@update false
            }
            pendingConsent = null
            change(ConnectionPhase.ERROR, ConnectionFailure.CONSENT_FLOW_FAILED)
            true
        }

        /** On resume, a revoked OS grant invalidates any previously observed ready/active state. */
        fun reconcileOsPermission(grantedByOs: Boolean) = update {
            if (!grantedByOs && snapshot.phase in setOf(
                    ConnectionPhase.PERMISSION_READY, ConnectionPhase.CONNECTING,
                    ConnectionPhase.PROTECTED, ConnectionPhase.INTERRUPTED
                )
            ) {
                activeEngineSession = null
                pendingConsent = null
                change(ConnectionPhase.DISCONNECTED, ConnectionFailure.PERMISSION_REVOKED)
            }
        }
    }

    /** Only VpnService and a future reviewed engine adapter should call these methods. */
    internal inner class ServicePort internal constructor() {
        fun permissionRevoked() = update {
            pendingConsent = null
            activeEngineSession = null
            change(ConnectionPhase.DISCONNECTED, ConnectionFailure.PERMISSION_REVOKED)
        }

        fun engineUnavailable() = update {
            pendingConsent = null
            activeEngineSession = null
            change(ConnectionPhase.ERROR, ConnectionFailure.ENGINE_UNAVAILABLE)
        }

        fun serviceStopped() = update {
            pendingConsent = null
            activeEngineSession = null
            change(ConnectionPhase.DISCONNECTED)
        }

        /** Internal only; no production engine calls this path yet. */
        fun openEngineSession(): Long? = update {
            if (snapshot.phase != ConnectionPhase.PERMISSION_READY) return@update null
            val session = counter.incrementAndGet()
            activeEngineSession = session
            session
        }

        fun onEngineSignal(session: Long, event: EngineSignal): Boolean = update {
            if (session != activeEngineSession) return@update false
            when (event) {
                EngineSignal.STARTING -> if (snapshot.phase == ConnectionPhase.PERMISSION_READY) {
                    change(ConnectionPhase.CONNECTING)
                }
                EngineSignal.INTERRUPTED -> if (snapshot.phase == ConnectionPhase.CONNECTING) {
                    change(ConnectionPhase.INTERRUPTED)
                }
                EngineSignal.FAILED -> {
                    activeEngineSession = null
                    change(ConnectionPhase.ERROR, ConnectionFailure.ENGINE_FAILED)
                }
                EngineSignal.STOPPED -> {
                    activeEngineSession = null
                    change(ConnectionPhase.DISCONNECTED)
                }
            }
            true
        }
    }
}
