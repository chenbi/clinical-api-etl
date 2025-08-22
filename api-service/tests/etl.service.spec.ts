import axios from "axios";
import { ETLService, ETLJob, ETLJobStatus } from "../src/services/etl.service";
import { DatabaseService } from "../src/services/database.service";

jest.mock("axios");
jest.mock("../src/services/database.service");

describe("ETLService", () => {
  let service: ETLService;
  let dbMock: jest.Mocked<DatabaseService>;

  beforeEach(() => {
    service = new ETLService();
    dbMock = new DatabaseService() as jest.Mocked<DatabaseService>;
    (service as any).dbService = dbMock;
  });

  it("should be defined", () => {
    expect(service).toBeDefined();
  });

  it("submitJob() returns a running ETLJob", async () => {
    dbMock.createETLJob = jest.fn().mockResolvedValue(undefined);
    const job = await service.submitJob("file.csv", "study1");
    expect(dbMock.createETLJob).toHaveBeenCalledWith(
      expect.objectContaining({
        filename: "file.csv",
        studyId: "study1",
        status: "running",
      })
    );
    expect(job).toMatchObject<Partial<ETLJob>>({
      filename: "file.csv",
      studyId: "study1",
      status: "running",
    });
  });

  it("getJob() returns whatever dbService.getETLJob returns", async () => {
    const fake: ETLJob = {
      id: "j1",
      filename: "f",
      status: "completed",
      studyId: "s",
      createdAt: new Date(),
      updatedAt: new Date(),
    };
    dbMock.getETLJob = jest.fn().mockResolvedValue(fake);

    const result = await service.getJob("j1");
    expect(dbMock.getETLJob).toHaveBeenCalledWith("j1");
    expect(result).toBe(fake);
  });

  it("getJobStatus() fetches remote status and updates DB if changed", async () => {
    const existing: ETLJob = {
      id: "j1",
      filename: "f",
      status: "pending",
      studyId: "s",
      createdAt: new Date(),
      updatedAt: new Date(),
    };
    dbMock.getETLJob = jest.fn().mockResolvedValue(existing);

    const remote: ETLJobStatus = { status: "completed", message: "done" };
    (axios.get as jest.Mock).mockResolvedValue({ data: remote });

    dbMock.updateETLJobStatus = jest.fn().mockResolvedValue(undefined);

    const result = await service.getJobStatus("j1");
    expect(dbMock.getETLJob).toHaveBeenCalledWith("j1");
    expect(axios.get).toHaveBeenCalledWith(
      expect.stringContaining("/jobs/j1/status")
    );
    expect(dbMock.updateETLJobStatus).toHaveBeenCalledWith(
      "j1",
      "completed",
      "done"
    );
    expect(result).toEqual(remote);
  });

  it("getJobStatus() throws if job not in DB", async () => {
    dbMock.getETLJob = jest.fn().mockResolvedValue(null);
    await expect(service.getJobStatus("nope")).rejects.toThrow(
      "Job nope not found"
    );
  });
});
