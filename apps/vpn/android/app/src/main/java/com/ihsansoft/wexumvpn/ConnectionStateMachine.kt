package com.ihsansoft.wexumvpn

enum class ConnectionPhase {
    DISCONNECTED, AWAITING_CONSENT, READY, CONNECTING, PROTECTED, INTERRUPTED, ERROR
}

enum class ConnectionFailure {
    PERMISSION_DENIED, ENGINE_UNAVAILABLE, UNVERIFIED_TUNNEL
}

data class ConnectionSnapshot(
    val phase: ConnectionPhase,
    val failure: ConnectionFailure? = null,
)

/** Future engine input; booleans alone are not a substitute for a verified tunnel. */
internal data class TunnelEvidence(
    val tunEstablished: Boolean,
    val gatewayAuthenticated: Boolean,
    val trafficVerified: Boolean,
    val dnsVerified: Boolean,
) {
    fun isComplete(): Boolean =
        tunEstablished && gatewayAuthenticated && trafficVerified && dnsVerified
}

/** In-memory and fail-closed: process restart never restores a protected state. */
class ConnectionStateMachine {
    private var snapshot = ConnectionSnapshot(ConnectionPhase.DISCONNECTED)

    @Synchronized
    fun current(): ConnectionSnapshot = snapshot

    @Synchronized
    fun requestConsent() {
        if (snapshot.phase != ConnectionPhase.PROTECTED) {
            snapshot = ConnectionSnapshot(ConnectionPhase.AWAITING_CONSENT)
        }
    }

    @Synchronized
    fun permissionGranted() {
        if (snapshot.phase == ConnectionPhase.AWAITING_CONSENT ||
            snapshot.phase == ConnectionPhase.DISCONNECTED ||
            snapshot.phase == ConnectionPhase.ERROR
        ) {
            snapshot = ConnectionSnapshot(ConnectionPhase.READY)
        }
    }

    @Synchronized
    fun permissionDenied() {
        snapshot = ConnectionSnapshot(ConnectionPhase.ERROR, ConnectionFailure.PERMISSION_DENIED)
    }

    @Synchronized
    fun beginConnecting(): Boolean {
        if (snapshot.phase != ConnectionPhase.READY) return false
        snapshot = ConnectionSnapshot(ConnectionPhase.CONNECTING)
        return true
    }

    @Synchronized
    internal fun tunnelVerified(evidence: TunnelEvidence): Boolean {
        if (snapshot.phase != ConnectionPhase.CONNECTING) return false
        if (!evidence.isComplete()) {
            snapshot = ConnectionSnapshot(ConnectionPhase.ERROR, ConnectionFailure.UNVERIFIED_TUNNEL)
            return false
        }
        snapshot = ConnectionSnapshot(ConnectionPhase.PROTECTED)
        return true
    }

    @Synchronized
    fun networkLost() {
        if (snapshot.phase == ConnectionPhase.PROTECTED || snapshot.phase == ConnectionPhase.CONNECTING) {
            snapshot = ConnectionSnapshot(ConnectionPhase.INTERRUPTED)
        }
    }

    @Synchronized
    fun transportUnavailable() {
        snapshot = ConnectionSnapshot(ConnectionPhase.ERROR, ConnectionFailure.ENGINE_UNAVAILABLE)
    }

    @Synchronized
    fun revoked() {
        snapshot = ConnectionSnapshot(ConnectionPhase.DISCONNECTED)
    }

    @Synchronized
    fun disconnect() {
        snapshot = ConnectionSnapshot(ConnectionPhase.DISCONNECTED)
    }
}
