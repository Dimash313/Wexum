package com.ihsansoft.wexumvpn

import android.content.Intent
import android.net.VpnService

/**
 * OS VPN integration boundary only. No tunnel, routes, credentials, or gateway
 * transport are created until the engine and server contracts are reviewed.
 */
class WexumVpnService : VpnService() {
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        VpnRuntime.state.transportUnavailable()
        stopSelf(startId)
        return START_NOT_STICKY
    }

    override fun onRevoke() {
        VpnRuntime.state.revoked()
        super.onRevoke()
    }

    override fun onDestroy() {
        VpnRuntime.state.disconnect()
        super.onDestroy()
    }
}
