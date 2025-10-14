/**
 * Formatea un número como moneda colombiana (COP)
 * Ejemplo: 25000 -> "$ 25.000"
 * Ejemplo: 25450.50 -> "$ 25.451" (redondeado al entero más cercano)
 */
export const formatCOP = (value: number | null | undefined): string => {
    if (value === null || value === undefined) {
        return '$ 0';
    }

    // Redondear al entero más cercano
    const roundedValue = Math.round(value);

    // Formatear con separador de miles (punto)
    const formatted = roundedValue.toLocaleString('es-CO', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
    });

    return `$ ${formatted}`;
};
