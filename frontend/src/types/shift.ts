import type { Employee, WorkObject } from "./directory.ts";
import type { Shift, TelegramMessage } from "./message.ts";
import type { User } from "./user.ts";

export type { Shift };

export type ShiftDetail = Shift & {
  employee: Employee | null;
  work_object: WorkObject | null;
  source_message: TelegramMessage | null;
  confirmed_by_user: User | null;
};

export type ShiftFilters = {
  employeeId: string;
  objectId: string;
  dateFrom: string;
  dateTo: string;
  confirmedManually: "" | "true" | "false";
  offset: number;
};
