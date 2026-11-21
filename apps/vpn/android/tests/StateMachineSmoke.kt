package com.ihsansoft.wexumvpn

import java.util.concurrent.CountDownLatch
import kotlin.concurrent.thread

fun main() {
    val s = ConnectionStateMachine()
    check(s.current().phase == ConnectionPhase.DISCONNECTED)
    val initial = s.user.beginConsent()!!
    check(s.user.beginConsent() == null)
    check(s.user.resolveConsent(initial, false))
    check(s.current().failure == ConnectionFailure.PERMISSION_DENIED)
    check(s.service.openEngineSession() == null)
    val attempt = s.user.beginConsent()!!
    check(!s.user.resolveConsent(initial, true))
    check(s.user.resolveConsent(attempt, true))
    check(s.current().phase == ConnectionPhase.PERMISSION_READY)
    val session = s.service.openEngineSession()!!
    check(s.service.onEngineSignal(session, EngineSignal.STARTING))
    check(s.current().phase == ConnectionPhase.CONNECTING)
    check(s.service.onEngineSignal(session, EngineSignal.INTERRUPTED))
    check(s.current().phase == ConnectionPhase.INTERRUPTED)
    check(s.current().phase != ConnectionPhase.PROTECTED)
    s.service.permissionRevoked()
    check(!s.service.onEngineSignal(session, EngineSignal.STARTING))
    check(s.current().phase == ConnectionPhase.DISCONNECTED)
    check(s.current().failure == ConnectionFailure.PERMISSION_REVOKED)
    val second = s.user.beginConsent()!!
    s.service.serviceStopped()
    check(!s.user.resolveConsent(second, true))
    check(s.current().phase == ConnectionPhase.DISCONNECTED)
    val fresh = ConnectionStateMachine()
    var notifications = 0
    val subscription = fresh.observe { notifications++ }
    fresh.service.engineUnavailable()
    check(notifications == 2)
    subscription.close()
    fresh.service.permissionRevoked()
    check(notifications == 2)
    // Permission grant and revoke from separate threads: final state must be safe.
    repeat(100) {
        val race = ConnectionStateMachine()
        val id = race.user.beginConsent()!!
        val ready = CountDownLatch(1)
        val t = thread { ready.await(); race.user.resolveConsent(id, true) }
        val t2 = thread { ready.await(); race.service.permissionRevoked() }
        ready.countDown()
        t.join(); t2.join()
        check(race.current().phase != ConnectionPhase.PROTECTED)
        // The OS permission recheck at resume is authoritative for the local UI.
        race.user.reconcileOsPermission(false)
        check(race.current().phase == ConnectionPhase.DISCONNECTED)
    }
    println("PASS: permission, service, observer, stale-callback and concurrency smoke")
}
