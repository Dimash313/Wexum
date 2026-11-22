# Apple iOS VPN capability and release gates

Checked against Apple developer guidance on 2026-11-21.

1. A custom packet-oriented VPN requires `NetworkExtension`, a separate `NEPacketTunnelProvider` app extension, matching App IDs and valid provisioning/capabilities. The host's entitlements plist requests `packet-tunnel-provider`, but neither an extension nor a signed entitlement has been validated; merely declaring a plist value does not grant privilege.
2. `NETunnelProviderManager` may load app-owned configurations from system preferences and `NEVPNStatusDidChange` can report status. `connected` alone does **not** independently prove a protected packet path, DNS correctness, or that our own provider is operational. This candidate only reads status; it does not call `startVPNTunnel`, `saveToPreferences` or `setTunnelNetworkSettings`.
3. Apple App Review Guideline 5.4 requires providers offering VPN services to enroll as **organizations**, explain collection and use of data on an in-app screen **before** service use or purchase, commit to strict data restrictions, and comply with local licensing rules. The prototype-only data notice is not a final legally reviewed privacy policy.
4. Before distribution: confirm organization enrollment, team and capability provisioning; product ownership; backend/auth contracts; independently reviewed protocol; published privacy policy and license review; real signed build; device tests on iOS with Wi-Fi/cellular transitions and leak tests; approved ethics and store review.
5. Without eligible Apple signing and Xcode, static source/syntax checks and Linux Swift tests do not validate NetworkExtension runtime or real traffic protection. No production claims or customer launch.

References:
- https://developer.apple.com/documentation/xcode/configuring-network-extensions
- https://developer.apple.com/documentation/networkextension/nepackettunnelprovider
- https://developer.apple.com/documentation/networkextension/netunnelprovidermanager
- https://developer.apple.com/documentation/networkextension/routing-your-vpn-network-traffic
- https://developer.apple.com/app-store/review/guidelines/ (5.4)
