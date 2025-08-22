import { DatabaseService } from "../src/services/database.service";
import { Pool } from "pg";

jest.mock("pg");

describe("DatabaseService", () => {
  let service: DatabaseService;
  let poolMock: Partial<Pool>;

  beforeEach(() => {
    // Create the service then override its internal pool
    service = new DatabaseService();
    poolMock = {
      query: jest.fn(),
      end: jest.fn(),
    };
    (service as any).pool = poolMock;
  });

  it("queryMeasurements() runs a query and returns rows", async () => {
    const fakeRows = [{ id: 1 }];
    (poolMock.query as jest.Mock).mockResolvedValue({ rows: fakeRows });

    const result = await service.queryMeasurements({ studyId: "s1" });
    expect(poolMock.query).toHaveBeenCalled();
    expect(result).toHaveLength(fakeRows.length);
    // only assert the id matches, other fields may be undefined or mapped
    expect(result[0].id).toBe(fakeRows[0].id);
  });

  it("updateETLJobStatus() runs the update SQL", async () => {
    (poolMock.query as jest.Mock).mockResolvedValue({ rowCount: 1 });

    await service.updateETLJobStatus("job1", "completed", "done");
    expect(poolMock.query).toHaveBeenCalledWith(
      expect.stringContaining("UPDATE etl_jobs"),
      expect.arrayContaining(["completed", expect.any(Date), "job1"])
    );
  });
});
