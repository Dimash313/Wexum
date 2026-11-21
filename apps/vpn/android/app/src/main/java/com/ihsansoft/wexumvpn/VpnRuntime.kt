package com.ihsansoft.wexumvpn

/** Process-local state only; never persisted as an indicator of network protection. */
internal object VpnRuntime {
    val state = ConnectionStateMachine()
}
