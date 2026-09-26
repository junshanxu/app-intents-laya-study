import Foundation

struct Trip: Codable, Identifiable, Sendable {
    let id: String
    var destination: String
    var startDate: String
    var status: String
}

struct StudyTask: Codable, Identifiable, Sendable {
    let id: String
    var title: String
    var dueDate: String
    var status: String
    var tripID: String?
}

enum StudyStore {
    static let root = FileManager.default.homeDirectoryForCurrentUser
        .appendingPathComponent("Library/Application Support/AppIntentsLayaStudy", isDirectory: true)

    static func readTrips() throws -> [Trip] {
        try read("trips.json", as: [Trip].self)
    }

    static func writeTrips(_ trips: [Trip]) throws {
        try write(trips, to: "trips.json")
    }

    static func readTasks() throws -> [StudyTask] {
        try read("tasks.json", as: [StudyTask].self)
    }

    static func writeTasks(_ tasks: [StudyTask]) throws {
        try write(tasks, to: "tasks.json")
    }

    static func json<T: Encodable>(_ value: T) throws -> String {
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys]
        return String(decoding: try encoder.encode(value), as: UTF8.self)
    }

    private static func read<T: Decodable>(_ name: String, as type: T.Type) throws -> T {
        let url = root.appendingPathComponent(name)
        return try JSONDecoder().decode(type, from: Data(contentsOf: url))
    }

    private static func write<T: Encodable>(_ value: T, to name: String) throws {
        try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
        let url = root.appendingPathComponent(name)
        try JSONEncoder().encode(value).write(to: url, options: .atomic)
    }
}

enum StudyError: LocalizedError {
    case invalidInput(String)
    case duplicateID(String)
    case missingID(String)

    var errorDescription: String? {
        switch self {
        case .invalidInput(let detail): "Invalid input: \(detail)"
        case .duplicateID(let id): "ID already exists: \(id)"
        case .missingID(let id): "ID not found: \(id)"
        }
    }
}

enum StudyService {
    static func searchTrips(destination: String) throws -> [Trip] {
        try StudyStore.readTrips().filter {
            $0.destination.localizedCaseInsensitiveContains(destination)
        }
    }

    static func addTrip(id: String, destination: String, startDate: String) throws -> Trip {
        try requireText(id, name: "trip ID")
        try requireText(destination, name: "destination")
        try requireDate(startDate)
        var trips = try StudyStore.readTrips()
        guard !trips.contains(where: { $0.id == id }) else { throw StudyError.duplicateID(id) }
        let trip = Trip(id: id, destination: destination, startDate: startDate, status: "booked")
        trips.append(trip)
        try StudyStore.writeTrips(trips)
        return trip
    }

    static func setTripStatus(id: String, status: String) throws -> Trip {
        guard ["booked", "cancelled"].contains(status) else {
            throw StudyError.invalidInput("trip status must be booked or cancelled")
        }
        var trips = try StudyStore.readTrips()
        guard let index = trips.firstIndex(where: { $0.id == id }) else { throw StudyError.missingID(id) }
        trips[index].status = status
        try StudyStore.writeTrips(trips)
        return trips[index]
    }

    static func findTasks(query: String) throws -> [StudyTask] {
        try StudyStore.readTasks().filter { $0.title.localizedCaseInsensitiveContains(query) }
    }

    static func createTask(id: String, title: String, dueDate: String, tripID: String?) throws -> StudyTask {
        try requireText(id, name: "task ID")
        try requireText(title, name: "title")
        try requireDate(dueDate)
        let trimmedTripID = tripID?.trimmingCharacters(in: .whitespacesAndNewlines)
        let relatedTripID = trimmedTripID?.isEmpty == true ? nil : trimmedTripID
        if let relatedTripID {
            guard try StudyStore.readTrips().contains(where: { $0.id == relatedTripID }) else {
                throw StudyError.missingID(relatedTripID)
            }
        }
        var tasks = try StudyStore.readTasks()
        guard !tasks.contains(where: { $0.id == id }) else { throw StudyError.duplicateID(id) }
        let task = StudyTask(id: id, title: title, dueDate: dueDate, status: "open", tripID: relatedTripID)
        tasks.append(task)
        try StudyStore.writeTasks(tasks)
        return task
    }

    static func setTaskStatus(id: String, status: String) throws -> StudyTask {
        guard ["open", "done"].contains(status) else {
            throw StudyError.invalidInput("task status must be open or done")
        }
        var tasks = try StudyStore.readTasks()
        guard let index = tasks.firstIndex(where: { $0.id == id }) else { throw StudyError.missingID(id) }
        tasks[index].status = status
        try StudyStore.writeTasks(tasks)
        return tasks[index]
    }

    static func rescheduleTask(id: String, dueDate: String) throws -> StudyTask {
        try requireDate(dueDate)
        var tasks = try StudyStore.readTasks()
        guard let index = tasks.firstIndex(where: { $0.id == id }) else { throw StudyError.missingID(id) }
        tasks[index].dueDate = dueDate
        try StudyStore.writeTasks(tasks)
        return tasks[index]
    }

    private static func requireText(_ value: String, name: String) throws {
        guard !value.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            throw StudyError.invalidInput("\(name) is empty")
        }
    }

    private static func requireDate(_ value: String) throws {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        formatter.isLenient = false
        formatter.timeZone = TimeZone(secondsFromGMT: 0)
        guard value.range(of: #"^\d{4}-\d{2}-\d{2}$"#, options: .regularExpression) != nil,
              formatter.date(from: value) != nil else {
            throw StudyError.invalidInput("date must be a real YYYY-MM-DD date")
        }
    }
}
