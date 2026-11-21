package com.ihsansoft.wexumvpn

import android.app.Activity
import android.app.AlertDialog
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

/** Transparent permission-only shell. It cannot start a VPN transport. */
class MainActivity : Activity() {
    private lateinit var status: TextView
    private lateinit var permissionButton: Button
    private val machine get() = VpnRuntime.state

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.statusBarColor = Color.BLACK
        window.navigationBarColor = Color.BLACK

        val container = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(28), dp(48), dp(28), dp(28))
            setBackgroundColor(Color.BLACK)
        }

        val heading = text(getString(R.string.home_title), 34f, Color.WHITE).apply {
            setTypeface(null, Typeface.BOLD)
        }
        container.addView(heading)

        val subtitle = text(getString(R.string.home_subtitle), 15f, Color.LTGRAY)
        container.addView(subtitle, gapTop(8))

        status = text("", 28f, Color.WHITE).apply {
            setTypeface(null, Typeface.BOLD)
            setPadding(0, dp(64), 0, dp(18))
            gravity = Gravity.START
        }
        container.addView(status)

        val notice = text(getString(R.string.home_notice), 16f, Color.LTGRAY)
        container.addView(notice, gapTop(8))

        permissionButton = Button(this).apply {
            text = getString(R.string.permission_button)
            setTextColor(Color.BLACK)
            setBackgroundColor(Color.WHITE)
            setOnClickListener { requestPermission() }
        }
        container.addView(permissionButton, gapTop(40))

        val languageButton = Button(this).apply {
            text = getString(R.string.language_button)
            setTextColor(Color.WHITE)
            setBackgroundColor(Color.DKGRAY)
            setOnClickListener { openLanguageSettings() }
        }
        container.addView(languageButton, gapTop(12))

        val aboutButton = Button(this).apply {
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
        }
        container.addView(aboutButton, gapTop(12))

        setContentView(ScrollView(this).apply {
            fillViewport = true
            addView(container)
        })
        render()
    }

    override fun onResume() {
        super.onResume()
        if (machine.current().phase == ConnectionPhase.READY && VpnService.prepare(this) != null) {
            machine.revoked()
        }
        if (::status.isInitialized) render()
    }

    private fun requestPermission() {
        val preparation = VpnService.prepare(this)
        if (preparation == null) {
            machine.permissionGranted()
            render()
            return
        }
        machine.requestConsent()
        render()
        @Suppress("DEPRECATION")
        startActivityForResult(preparation, VPN_REQUEST)
    }

    @Deprecated("Framework VPN consent callback; avoids an AndroidX dependency in this scaffold.")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode != VPN_REQUEST) return
        if (resultCode == RESULT_OK && VpnService.prepare(this) == null) {
            machine.permissionGranted()
        } else {
            machine.permissionDenied()
        }
        render()
    }

    private fun render() {
        val phase = machine.current().phase
        val label = when (phase) {
            ConnectionPhase.DISCONNECTED -> R.string.status_disconnected
            ConnectionPhase.AWAITING_CONSENT -> R.string.status_consent
            ConnectionPhase.READY -> R.string.status_ready
            ConnectionPhase.CONNECTING -> R.string.status_connecting
            ConnectionPhase.PROTECTED -> R.string.status_protected
            ConnectionPhase.INTERRUPTED -> R.string.status_interrupted
            ConnectionPhase.ERROR -> R.string.status_error
        }
        status.setText(label)
        permissionButton.isEnabled = phase != ConnectionPhase.READY
    }

    private fun openLanguageSettings() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            val intent = Intent(Settings.ACTION_APP_LOCALE_SETTINGS).apply {
                data = Uri.fromParts("package", packageName, null)
            }
            startActivity(intent)
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
        ViewGroup.LayoutParams.MATCH_PARENT,
        ViewGroup.LayoutParams.WRAP_CONTENT,
    ).apply { topMargin = dp(top) }

    private fun dp(value: Int) = (value * resources.displayMetrics.density + 0.5f).toInt()

    companion object {
        private const val VPN_REQUEST = 100
    }
}
