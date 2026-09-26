import SwiftUI

@main
struct TripLedgerApp: App {
    @State private var trips: [Trip] = []
    @State private var message = ""

    var body: some Scene {
        WindowGroup("Study Trips") {
            VStack(alignment: .leading, spacing: 12) {
                Text("Study Trips").font(.title)
                Text("Synthetic research data. Actions are available in Shortcuts.")
                    .foregroundStyle(.secondary)
                HStack {
                    Button("Refresh") { load() }
                    Text(message).foregroundStyle(.secondary)
                }
                List(trips) { trip in
                    VStack(alignment: .leading, spacing: 3) {
                        Text(trip.destination).font(.headline)
                        Text("\(trip.id) · \(trip.startDate) · \(trip.status)")
                            .font(.caption).foregroundStyle(.secondary)
                    }
                }
            }
            .padding(24)
            .frame(minWidth: 500, minHeight: 320)
            .onAppear(perform: load)
        }
    }

    private func load() {
        do {
            trips = try StudyStore.readTrips()
            message = "\(trips.count) trips"
        } catch {
            trips = []
            message = "No fixture loaded yet"
        }
    }
}
