package com.ihsansoft.wexumvpn

/** In-memory only: process restarts cannot restore a protected flag or an engine session. */
internal object VpnRuntime {
    val state = ConnectionStateMachine()
}
