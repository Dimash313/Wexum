// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "WexumVPNCore",
    platforms: [.iOS(.v16)],
    products: [.library(name: "WexumVPNCore", targets: ["WexumVPNCore"])],
    targets: [
        .target(name: "WexumVPNCore"),
        .testTarget(name: "WexumVPNCoreTests", dependencies: ["WexumVPNCore"])
    ]
)
