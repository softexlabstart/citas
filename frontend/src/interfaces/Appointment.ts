import { Service } from './Service';
import { User } from './User';
import { Recurso } from './Recurso';
import { Sede } from './Sede';

export interface Appointment {
  id: number;
  nombre: string;
  fecha: string;
  servicio: Service;
  colaboradores: Recurso[];
  confirmado: boolean;
  user: User;
  estado: 'Pendiente' | 'Confirmada' | 'Cancelada' | 'Asistio' | 'No Asistio';
  sede: Sede;
}

