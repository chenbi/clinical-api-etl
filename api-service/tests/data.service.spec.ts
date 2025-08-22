import {
  DataService,
  ClinicalMeasurement,
  DataFilters,
} from "../src/services/data.service";
import { DatabaseService } from "../src/services/database.service";

describe("DataService", () => {
  let service: DataService;
  let dbMock: jest.Mocked<DatabaseService>;

  beforeEach(() => {
    // Create an instance then override its private dbService
    service = new DataService();
    dbMock = {
      queryMeasurements: jest.fn(),
      createETLJob: jest.fn(),
      updateETLJobStatus: jest.fn(),
      getETLJob: jest.fn(),
      // ...only the methods you actually call in DataService
    } as any;
    (service as any).dbService = dbMock;
  });

  it("should be defined", () => {
    expect(service).toBeDefined();
  });

  it("getData() calls queryMeasurements with given filters", async () => {
    const fake: ClinicalMeasurement[] = [
      {
        id: "1",
        studyId: "s",
        participantId: "p",
        measurementType: "t",
        value: "v",
        unit: "u",
        timestamp: new Date(),
        siteId: "",
        qualityScore: 0,
      },
    ] as any;
    dbMock.queryMeasurements.mockResolvedValue(fake);

    const filters: DataFilters = { studyId: "s1" };
    const result = await service.getData(filters);
    expect(dbMock.queryMeasurements).toHaveBeenCalledWith(filters);
    expect(result).toEqual(fake);
  });

  it("getStudyData() calls queryMeasurements with only studyId", async () => {
    const fake: ClinicalMeasurement[] = [];
    dbMock.queryMeasurements.mockResolvedValue(fake);

    const result = await service.getStudyData("s2");
    expect(dbMock.queryMeasurements).toHaveBeenCalledWith({ studyId: "s2" });
    expect(result).toEqual(fake);
  });
});
