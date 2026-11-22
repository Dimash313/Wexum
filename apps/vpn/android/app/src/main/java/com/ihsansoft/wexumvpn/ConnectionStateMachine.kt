package com.ihsansoft.wexumvpn

import java.util.concurrent.atomic.AtomicLong

/** PROTECTED has no authorized transition until a reviewed tunnel verifier exists. */
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

internal enum class EngineSignal { STARTING, INTERRUPTED, STOPPED, FAILED }

/**
 * Process-local, fail-closed state. Session/lease numbers reject stale callbacks; they are
 * not OS permission, VPN verification, or server authorization. No tunnel is implemented.
 */
class ConnectionStateMachine(
    private val onObserverFailure: (Exception) -> Unit = { exception ->
        System.err.println("WexumVPN state observer failed: ${exception.javaClass.simpleName}")
    },
) {
    private val lock = Any()
    private var snapshot = ConnectionSnapshot()
    private var pendingConsent: Long? = null
    private var serviceLease: Long? = null
    private var activeEngineSession: Long? = null
    private val counter = AtomicLong()
    private val listeners = LinkedHashMap<Long, () -> Unit>()

    val user: UserPort = UserPort()
    internal val service: ServicePort = ServicePort()

    fun current(): ConnectionSnapshot = synchronized(lock) { snapshot }

    /** Observer receives the latest snapshot, never an authoritative tunnel event. */
    fun observe(listener: () -> Unit): AutoCloseable {
        val key = counter.incrementAndGet()
        synchronized(lock) { listeners[key] = listener }
        try {
            listener()
        } catch (exception: Exception) {
            synchronized(lock) { listeners.remove(key) }
            throw exception
        }
        return AutoCloseable { synchronized(lock) { listeners.remove(key) } }
    }

    private inline fun <T> update(block: () -> T): T {
        val result: T
        val notifications: List<() -> Unit>
        synchronized(lock) {
            val before = snapshot
            result = block()
            notifications = if (before != snapshot) listeners.values.toList() else emptyList()
        }
        // A broken UI listener must not abort a security-critical revocation or block peers.
        notifications.forEach { listener ->
            try {
                listener()
            } catch (exception: Exception) {
                try {
                    onObserverFailure(exception)
                } catch (handlerError: Exception) {
                    System.err.println("WexumVPN observer error handler failed: ${handlerError.javaClass.simpleName}")
                }
            }
        }
        return result
    }

    private fun change(phase: ConnectionPhase, failure: ConnectionFailure? = null) {
        if (snapshot.phase != phase || snapshot.failure != failure) {
            snapshot = ConnectionSnapshot(phase, failure, snapshot.revision + 1)
        }
    }

    /** The Activity can request/record OS consent but cannot emit engine events. */
    inner class UserPort internal constructor() {
        fun beginConsent(): Long? = update {
            if (snapshot.phase in setOf(
                    ConnectionPhase.AWAITING_CONSENT, ConnectionPhase.CONNECTING,
                    ConnectionPhase.PROTECTED, ConnectionPhase.INTERRUPTED,
                )
            ) return@update null
            val attempt = counter.incrementAndGet()
            pendingConsent = attempt
            activeEngineSession = null
            change(ConnectionPhase.AWAITING_CONSENT)
            attempt
        }

        /** OS must be checked by the Android Activity before passing grantedByOs=true. */
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

        fun reconcileOsPermission(grantedByOs: Boolean) = update {
            if (!grantedByOs && snapshot.phase in setOf(
                    ConnectionPhase.PERMISSION_READY, ConnectionPhase.CONNECTING,
                    ConnectionPhase.PROTECTED, ConnectionPhase.INTERRUPTED,
                )
            ) {
                activeEngineSession = null
                pendingConsent = null
                change(ConnectionPhase.DISCONNECTED, ConnectionFailure.PERMISSION_REVOKED)
            }
        }
    }

    /** Only the platform VpnService and a future audited engine adapter may call this port. */
    internal inner class ServicePort internal constructor() {
        /** Each Android Service instance owns a lease, not shared across recreation. */
        fun attach(): Long = update {
            if (serviceLease != null) {
                activeEngineSession = null
                if (snapshot.phase in setOf(ConnectionPhase.CONNECTING, ConnectionPhase.INTERRUPTED)) {
                    change(ConnectionPhase.DISCONNECTED)
                }
            }
            val lease = counter.incrementAndGet()
            serviceLease = lease
            lease
        }

        /** OS revocation invalidates all attempts, including a still-open consent dialog. */
        fun permissionRevoked() = update {
            pendingConsent = null
            activeEngineSession = null
            serviceLease = null
            change(ConnectionPhase.DISCONNECTED, ConnectionFailure.PERMISSION_REVOKED)
        }

        fun engineUnavailable(lease: Long): Boolean = update {
            if (serviceLease != lease || snapshot.phase !in setOf(
                    ConnectionPhase.PERMISSION_READY, ConnectionPhase.CONNECTING,
                    ConnectionPhase.INTERRUPTED,
                )
            ) return@update false
            activeEngineSession = null
            change(ConnectionPhase.ERROR, ConnectionFailure.ENGINE_UNAVAILABLE)
            true
        }

        /** A late onDestroy from a replaced/revoked service cannot erase newer state. */
        fun serviceStopped(lease: Long): Boolean = update {
            if (serviceLease != lease) return@update false
            serviceLease = null
            activeEngineSession = null
            if (snapshot.phase != ConnectionPhase.ERROR &&
                snapshot.failure != ConnectionFailure.PERMISSION_REVOKED
            ) change(ConnectionPhase.DISCONNECTED)
            true
        }

        /** Requires a live service lease and an OS-approved permission state. */
        fun openEngineSession(lease: Long): Long? = update {
            if (serviceLease != lease || snapshot.phase != ConnectionPhase.PERMISSION_READY ||
                activeEngineSession != null
            ) return@update null
            val session = counter.incrementAndGet()
            activeEngineSession = session
            session
        }

        /** True means a legal transition occurred, not merely a matching session ID. */
        fun onEngineSignal(session: Long, event: EngineSignal): Boolean = update {
            if (serviceLease == null || session != activeEngineSession) return@update false
            when (event) {
                EngineSignal.STARTING -> {
                    if (snapshot.phase != ConnectionPhase.PERMISSION_READY) return@update false
                    change(ConnectionPhase.CONNECTING)
                }
                EngineSignal.INTERRUPTED -> {
                    if (snapshot.phase != ConnectionPhase.CONNECTING) return@update false
                    change(ConnectionPhase.INTERRUPTED)
                }
                EngineSignal.FAILED -> {
                    if (snapshot.phase !in setOf(
                            ConnectionPhase.PERMISSION_READY, ConnectionPhase.CONNECTING,
                            ConnectionPhase.INTERRUPTED,
                        )
                    ) return@update false
                    activeEngineSession = null
                    change(ConnectionPhase.ERROR, ConnectionFailure.ENGINE_FAILED)
                }
                EngineSignal.STOPPED -> {
                    if (snapshot.phase !in setOf(
                            ConnectionPhase.PERMISSION_READY, ConnectionPhase.CONNECTING,
                            ConnectionPhase.INTERRUPTED,
                        )
                    ) return@update false
                    activeEngineSession = null
                    change(ConnectionPhase.DISCONNECTED)
                }
            }
            true
        }
    }
}
