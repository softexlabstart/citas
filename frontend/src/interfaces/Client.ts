export interface Client {
    id: number;
    username: string;
    first_name: string;
    last_name: string;
    full_name: string;
    email: string;
    telefono: string;
    ciudad: string;
    barrio: string;
    genero: string;
    fecha_nacimiento: string; // Added
    age: number;
    has_consented_data_processing: boolean;
    data_processing_opt_out: boolean;
}
