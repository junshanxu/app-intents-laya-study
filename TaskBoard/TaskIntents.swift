import AppIntents
import Foundation

struct FindTasksIntent: AppIntent {
    static let title: LocalizedStringResource = "Study: Find Tasks"
    static let description = IntentDescription("Find synthetic tasks by title.")

    @Parameter(title: "Title contains") var query: String

    static var parameterSummary: some ParameterSummary {
        Summary("Find tasks matching \(\.$query)")
    }

    func perform() async throws -> some IntentResult & ReturnsValue<String> {
        return .result(value: try StudyStore.json(StudyService.findTasks(query: query)))
    }
}

struct CreateTaskIntent: AppIntent {
    static let title: LocalizedStringResource = "Study: Create Task"
    static let description = IntentDescription("Create a synthetic task.")

    @Parameter(title: "Task ID") var taskID: String
    @Parameter(title: "Title") var title: String
    @Parameter(title: "Due date in YYYY-MM-DD") var dueDate: String
    @Parameter(title: "Related trip ID") var tripID: String?

    static var parameterSummary: some ParameterSummary {
        Summary("Create task \(\.$title) with ID \(\.$taskID) due \(\.$dueDate) for trip \(\.$tripID)")
    }

    func perform() async throws -> some IntentResult & ReturnsValue<String> {
        return .result(value: try StudyStore.json(StudyService.createTask(id: taskID, title: title, dueDate: dueDate, tripID: tripID)))
    }
}

struct SetTaskStatusIntent: AppIntent {
    static let title: LocalizedStringResource = "Study: Set Task Status"
    static let description = IntentDescription("Set a synthetic task to open or done.")

    @Parameter(title: "Task ID") var taskID: String
    @Parameter(title: "Status") var status: String

    static var parameterSummary: some ParameterSummary {
        Summary("Set task \(\.$taskID) to \(\.$status)")
    }

    func perform() async throws -> some IntentResult & ReturnsValue<String> {
        return .result(value: try StudyStore.json(StudyService.setTaskStatus(id: taskID, status: status)))
    }
}

struct RescheduleTaskIntent: AppIntent {
    static let title: LocalizedStringResource = "Study: Reschedule Task"
    static let description = IntentDescription("Change the due date of a synthetic task.")

    @Parameter(title: "Task ID") var taskID: String
    @Parameter(title: "Due date in YYYY-MM-DD") var dueDate: String

    static var parameterSummary: some ParameterSummary {
        Summary("Reschedule task \(\.$taskID) to \(\.$dueDate)")
    }

    func perform() async throws -> some IntentResult & ReturnsValue<String> {
        return .result(value: try StudyStore.json(StudyService.rescheduleTask(id: taskID, dueDate: dueDate)))
    }
}
