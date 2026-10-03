export type Employee = {
  id: number;
  full_name: string;
  personnel_number: string;
  telegram_user_id: number | null;
  telegram_username: string | null;
  callsign: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type WorkObject = {
  id: number;
  name: string;
  shift_start_time: string;
  checkin_before_minutes: number;
  checkin_after_minutes: number;
  timezone: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};
