import SwiftUI

@main
struct TaskBoardApp: App {
    @State private var tasks: [StudyTask] = []
    @State private var message = ""

    var body: some Scene {
        WindowGroup("Study Tasks") {
            VStack(alignment: .leading, spacing: 12) {
                Text("Study Tasks").font(.title)
                Text("Synthetic research data. Actions are available in Shortcuts.")
                    .foregroundStyle(.secondary)
                HStack {
                    Button("Refresh") { load() }
                    Text(message).foregroundStyle(.secondary)
                }
                List(tasks) { task in
                    VStack(alignment: .leading, spacing: 3) {
                        Text(task.title).font(.headline)
                        Text("\(task.id) · due \(task.dueDate) · \(task.status)")
                            .font(.caption).foregroundStyle(.secondary)
                        if let tripID = task.tripID {
                            Text("Trip: \(tripID)").font(.caption).foregroundStyle(.secondary)
                        }
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
            tasks = try StudyStore.readTasks()
            message = "\(tasks.count) tasks"
        } catch {
            tasks = []
            message = "No fixture loaded yet"
        }
    }
}
