package com.ihsansoft.wexumvpn

import android.content.Intent
import android.net.VpnService

/** Placeholder OS service only. Never starts a tunnel and never announces protection. */
class WexumVpnService : VpnService() {
    private var lease: Long? = null

    override fun onCreate() {
        super.onCreate()
        lease = VpnRuntime.state.service.attach()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        lease?.let { VpnRuntime.state.service.engineUnavailable(it) }
        stopSelf(startId)
        return START_NOT_STICKY
    }

    override fun onRevoke() {
        VpnRuntime.state.service.permissionRevoked()
        super.onRevoke()
    }

    override fun onDestroy() {
        lease?.let { VpnRuntime.state.service.serviceStopped(it) }
        lease = null
        super.onDestroy()
    }
}
