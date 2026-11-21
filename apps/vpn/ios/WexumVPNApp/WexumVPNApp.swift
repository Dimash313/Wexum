import SwiftUI

@main
struct WexumVPNApp: App {
    @StateObject private var store = ConnectionStore()

    var body: some Scene {
        WindowGroup {
            ConnectionView().environmentObject(store)
        }
    }
}
