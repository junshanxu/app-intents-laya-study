import AppIntents
import Foundation

struct SearchTripsIntent: AppIntent {
    static let title: LocalizedStringResource = "Study: Search Trips"
    static let description = IntentDescription("Find synthetic trips by destination.")

    @Parameter(title: "Destination") var destination: String

    static var parameterSummary: some ParameterSummary {
        Summary("Search trips for \(\.$destination)")
    }

    func perform() async throws -> some IntentResult & ReturnsValue<String> {
        return .result(value: try StudyStore.json(StudyService.searchTrips(destination: destination)))
    }
}

struct AddTripIntent: AppIntent {
    static let title: LocalizedStringResource = "Study: Add Trip"
    static let description = IntentDescription("Add a synthetic trip.")

    @Parameter(title: "Trip ID") var tripID: String
    @Parameter(title: "Destination") var destination: String
    @Parameter(title: "Start date in YYYY-MM-DD") var startDate: String

    static var parameterSummary: some ParameterSummary {
        Summary("Add trip \(\.$tripID) to \(\.$destination) on \(\.$startDate)")
    }

    func perform() async throws -> some IntentResult & ReturnsValue<String> {
        return .result(value: try StudyStore.json(StudyService.addTrip(id: tripID, destination: destination, startDate: startDate)))
    }
}

struct SetTripStatusIntent: AppIntent {
    static let title: LocalizedStringResource = "Study: Set Trip Status"
    static let description = IntentDescription("Set a synthetic trip to booked or cancelled.")

    @Parameter(title: "Trip ID") var tripID: String
    @Parameter(title: "Status") var status: String

    static var parameterSummary: some ParameterSummary {
        Summary("Set trip \(\.$tripID) to \(\.$status)")
    }

    func perform() async throws -> some IntentResult & ReturnsValue<String> {
        return .result(value: try StudyStore.json(StudyService.setTripStatus(id: tripID, status: status)))
    }
}
