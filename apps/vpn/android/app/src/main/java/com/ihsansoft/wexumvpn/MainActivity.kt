package com.ihsansoft.wexumvpn

import android.app.Activity
import android.app.AlertDialog
import android.content.ActivityNotFoundException
import android.content.Intent
import android.graphics.Color
import android.graphics.Typeface
import android.net.Uri
import android.net.VpnService
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.view.Gravity
import android.view.ViewGroup
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast

/** UI has no access to trusted engine signals: only permission-bound UserPort. */
class MainActivity : Activity() {
    private lateinit var status: TextView
    private lateinit var permissionButton: Button
    private val user get() = VpnRuntime.state.user
    private var observer: AutoCloseable? = null
    private var started = false
    private var pendingAttempt: Long? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        pendingAttempt = if (savedInstanceState?.containsKey(KEY_REQUEST) == true &&
            VpnRuntime.state.current().phase == ConnectionPhase.AWAITING_CONSENT
        ) savedInstanceState.getLong(KEY_REQUEST) else null

        window.statusBarColor = Color.BLACK
        window.navigationBarColor = Color.BLACK
        val container = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(28), dp(48), dp(28), dp(28))
            setBackgroundColor(Color.BLACK)
        }
        container.addView(text(getString(R.string.home_title), 34f, Color.WHITE).apply {
            setTypeface(null, Typeface.BOLD)
        })
        container.addView(text(getString(R.string.home_subtitle), 15f, Color.LTGRAY), gapTop(8))
        status = text("", 28f, Color.WHITE).apply {
            setTypeface(null, Typeface.BOLD)
            setPadding(0, dp(64), 0, dp(18))
            gravity = Gravity.START
        }
        container.addView(status)
        container.addView(text(getString(R.string.home_notice), 16f, Color.LTGRAY), gapTop(8))
        permissionButton = Button(this).apply {
            text = getString(R.string.permission_button)
            setTextColor(Color.BLACK)
            setBackgroundColor(Color.WHITE)
            setOnClickListener { requestPermission() }
        }
        container.addView(permissionButton, gapTop(40))
        container.addView(Button(this).apply {
            text = getString(R.string.language_button)
            setTextColor(Color.WHITE)
            setBackgroundColor(Color.DKGRAY)
            setOnClickListener { openLanguageSettings() }
        }, gapTop(12))
        container.addView(Button(this).apply {
            text = getString(R.string.about_button)
            setTextColor(Color.WHITE)
            setBackgroundColor(Color.DKGRAY)
            setOnClickListener {
                AlertDialog.Builder(this@MainActivity)
                    .setTitle(R.string.about_title)
                    .setMessage(R.string.about_message)
                    .setPositiveButton(android.R.string.ok, null)
                    .show()
            }
        }, gapTop(12))
        setContentView(ScrollView(this).apply {
            isFillViewport = true
            addView(container)
        })
        render()
    }

    override fun onStart() {
        super.onStart()
        started = true
        observer = VpnRuntime.state.observe { runOnUiThread { if (started && !isFinishing) render() } }
    }

    override fun onStop() {
        started = false
        observer?.close()
        observer = null
        super.onStop()
    }

    override fun onResume() {
        super.onResume()
        try {
            user.reconcileOsPermission(VpnService.prepare(this) == null)
        } catch (_: SecurityException) {
            user.reconcileOsPermission(false)
        }
        if (::status.isInitialized) render()
    }

    override fun onSaveInstanceState(outState: Bundle) {
        pendingAttempt?.let { outState.putLong(KEY_REQUEST, it) }
        super.onSaveInstanceState(outState)
    }

    private fun requestPermission() {
        val attempt = user.beginConsent() ?: return
        pendingAttempt = attempt
        val preparation = try {
            VpnService.prepare(this)
        } catch (_: SecurityException) {
            user.consentLaunchFailed(attempt)
            pendingAttempt = null
            return
        }
        if (preparation == null) {
            user.resolveConsent(attempt, true)
            pendingAttempt = null
            return
        }
        try {
            @Suppress("DEPRECATION")
            startActivityForResult(preparation, VPN_REQUEST)
        } catch (_: ActivityNotFoundException) {
            user.consentLaunchFailed(attempt)
            pendingAttempt = null
        } catch (_: SecurityException) {
            user.consentLaunchFailed(attempt)
            pendingAttempt = null
        }
    }

    @Deprecated("Android framework VpnService.prepare callback; intentionally avoids AndroidX dependency.")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode != VPN_REQUEST) return
        val attempt = pendingAttempt ?: return
        pendingAttempt = null
        val granted = resultCode == RESULT_OK && try {
            VpnService.prepare(this) == null
        } catch (_: SecurityException) {
            false
        }
        user.resolveConsent(attempt, granted)
    }

    private fun render() {
        val phase = VpnRuntime.state.current().phase
        status.setText(when (phase) {
            ConnectionPhase.DISCONNECTED -> R.string.status_disconnected
            ConnectionPhase.AWAITING_CONSENT -> R.string.status_consent
            ConnectionPhase.PERMISSION_READY -> R.string.status_ready
            ConnectionPhase.CONNECTING -> R.string.status_connecting
            ConnectionPhase.PROTECTED -> R.string.status_protected
            ConnectionPhase.INTERRUPTED -> R.string.status_interrupted
            ConnectionPhase.ERROR -> R.string.status_error
        })
        permissionButton.isEnabled = phase != ConnectionPhase.AWAITING_CONSENT &&
            phase != ConnectionPhase.PERMISSION_READY && phase != ConnectionPhase.CONNECTING &&
            phase != ConnectionPhase.PROTECTED
    }

    private fun openLanguageSettings() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            val intent = Intent(Settings.ACTION_APP_LOCALE_SETTINGS).apply {
                data = Uri.fromParts("package", packageName, null)
            }
            try {
                startActivity(intent)
            } catch (_: ActivityNotFoundException) {
                Toast.makeText(this, R.string.language_legacy, Toast.LENGTH_LONG).show()
            }
        } else {
            Toast.makeText(this, R.string.language_legacy, Toast.LENGTH_LONG).show()
        }
    }

    private fun text(value: String, size: Float, color: Int) = TextView(this).apply {
        text = value
        textSize = size
        setTextColor(color)
    }

    private fun gapTop(top: Int) = LinearLayout.LayoutParams(
        ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT,
    ).apply { topMargin = dp(top) }

    private fun dp(value: Int) = (value * resources.displayMetrics.density + 0.5f).toInt()

    companion object {
        private const val VPN_REQUEST = 100
        private const val KEY_REQUEST = "consent_attempt"
    }
}
