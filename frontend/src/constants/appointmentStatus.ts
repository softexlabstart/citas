export const APPOINTMENT_STATUS = {
  PENDIENTE: 'Pendiente',
  CONFIRMADA: 'Confirmada',
  CANCELADA: 'Cancelada',
  ASISTIO: 'Asistio',
  NO_ASISTIO: 'No Asistio',
} as const;

type StatusConfig = {
  [key: string]: { color: string; key: string };
};

export const statusConfig: StatusConfig = {
  [APPOINTMENT_STATUS.PENDIENTE]: { color: 'warning', key: 'pending' },
  [APPOINTMENT_STATUS.CONFIRMADA]: { color: 'success', key: 'confirmed' },
  [APPOINTMENT_STATUS.CANCELADA]: { color: 'danger', key: 'cancelled' },
  [APPOINTMENT_STATUS.ASISTIO]: { color: 'primary', key: 'attended' },
  [APPOINTMENT_STATUS.NO_ASISTIO]: { color: 'secondary', key: 'not_attended' },
};
