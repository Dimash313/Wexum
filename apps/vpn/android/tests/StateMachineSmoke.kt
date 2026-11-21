package com.ihsansoft.wexumvpn

import java.util.concurrent.CountDownLatch
import kotlin.concurrent.thread

fun main() {
    val model = ConnectionStateMachine()
    check(model.current().phase == ConnectionPhase.DISCONNECTED)
    val first = model.user.beginConsent()!!
    check(model.user.beginConsent() == null)
    check(model.user.resolveConsent(first, false))
    check(model.current().failure == ConnectionFailure.PERMISSION_DENIED)
    val lease = model.service.attach()
    check(model.service.openEngineSession(lease) == null)
    val retry = model.user.beginConsent()!!
    check(!model.user.resolveConsent(first, true))
    check(model.user.resolveConsent(retry, true))
    check(model.current().phase == ConnectionPhase.PERMISSION_READY)
    check(model.service.openEngineSession(lease + 100) == null)
    val session = model.service.openEngineSession(lease)!!
    check(model.service.openEngineSession(lease) == null)
    check(!model.service.onEngineSignal(session, EngineSignal.INTERRUPTED))
    check(model.service.onEngineSignal(session, EngineSignal.STARTING))
    check(!model.service.onEngineSignal(session, EngineSignal.STARTING))
    check(model.service.onEngineSignal(session, EngineSignal.INTERRUPTED))
    check(!model.service.onEngineSignal(session, EngineSignal.STARTING))
    check(model.current().phase == ConnectionPhase.INTERRUPTED)
    model.service.permissionRevoked()
    check(!model.service.serviceStopped(lease))
    check(!model.service.engineUnavailable(lease))
    check(!model.service.onEngineSignal(session, EngineSignal.FAILED))
    check(model.current().phase == ConnectionPhase.DISCONNECTED)
    check(model.current().failure == ConnectionFailure.PERMISSION_REVOKED)
    val oldConsent = model.user.beginConsent()!!
    val oldLease = model.service.attach()
    check(model.service.serviceStopped(oldLease))
    check(!model.user.resolveConsent(oldConsent, true))
    check(model.current().phase == ConnectionPhase.DISCONNECTED)

    val errors = mutableListOf<String>()
    val observed = ConnectionStateMachine { exception -> errors += exception.javaClass.simpleName }
    val broken = observed.observe { if (observed.current().revision > 0) throw IllegalStateException("observer") }
    var goodCount = 0
    val healthy = observed.observe { goodCount++ }
    observed.service.permissionRevoked()
    check(errors == listOf("IllegalStateException"))
    check(goodCount == 2)
    broken.close()
    healthy.close()
    observed.service.permissionRevoked()
    check(goodCount == 2)

    repeat(100) {
        val race = ConnectionStateMachine()
        val id = race.user.beginConsent()!!
        val gate = CountDownLatch(1)
        val a = thread { gate.await(); race.user.resolveConsent(id, true) }
        val b = thread { gate.await(); race.service.permissionRevoked() }
        gate.countDown()
        a.join(); b.join()
        race.user.reconcileOsPermission(false)
        check(race.current().phase == ConnectionPhase.DISCONNECTED)
        check(race.current().phase != ConnectionPhase.PROTECTED)
    }
    println("PASS: stale service, illegal transitions, listener failures, permission races (100)")
}
