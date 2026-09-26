import Foundation

func required(_ args: [String: String], _ key: String) throws -> String {
    guard let value = args[key] else { throw StudyError.invalidInput("missing \(key)") }
    return value
}

do {
    guard CommandLine.arguments.count == 3 else {
        throw StudyError.invalidInput("usage: studyctl OPERATION JSON_ARGUMENTS")
    }
    let operation = CommandLine.arguments[1]
    let data = Data(CommandLine.arguments[2].utf8)
    let args = try JSONDecoder().decode([String: String].self, from: data)
    let output: String
    switch operation {
    case "search_trips":
        output = try StudyStore.json(StudyService.searchTrips(destination: required(args, "destination")))
    case "add_trip":
        output = try StudyStore.json(StudyService.addTrip(
            id: required(args, "trip_id"),
            destination: required(args, "destination"),
            startDate: required(args, "start_date")))
    case "set_trip_status":
        output = try StudyStore.json(StudyService.setTripStatus(
            id: required(args, "trip_id"), status: required(args, "status")))
    case "find_tasks":
        output = try StudyStore.json(StudyService.findTasks(query: required(args, "query")))
    case "create_task":
        output = try StudyStore.json(StudyService.createTask(
            id: required(args, "task_id"), title: required(args, "title"),
            dueDate: required(args, "due_date"), tripID: args["trip_id"]))
    case "set_task_status":
        output = try StudyStore.json(StudyService.setTaskStatus(
            id: required(args, "task_id"), status: required(args, "status")))
    case "reschedule_task":
        output = try StudyStore.json(StudyService.rescheduleTask(
            id: required(args, "task_id"), dueDate: required(args, "due_date")))
    default:
        throw StudyError.invalidInput("unknown operation \(operation)")
    }
    print(output)
} catch {
    let message = error.localizedDescription
    FileHandle.standardError.write(Data((message + "\n").utf8))
    exit(1)
}
