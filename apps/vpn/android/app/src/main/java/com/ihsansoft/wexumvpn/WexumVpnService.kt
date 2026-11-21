package com.ihsansoft.wexumvpn

import android.content.Intent
import android.net.VpnService

/** Placeholder OS service only. Never starts a tunnel and never announces protection. */
class WexumVpnService : VpnService() {
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        VpnRuntime.state.service.engineUnavailable()
        stopSelf(startId)
        return START_NOT_STICKY
    }

    override fun onRevoke() {
        VpnRuntime.state.service.permissionRevoked()
        super.onRevoke()
    }

    override fun onDestroy() {
        VpnRuntime.state.service.serviceStopped()
        super.onDestroy()
    }
}
