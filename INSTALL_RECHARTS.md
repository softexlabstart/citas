# Instalación de Recharts para Dashboard Financiero

## Requisito

Para que el Dashboard Financiero funcione correctamente, necesitas instalar la librería **recharts** para los gráficos.

## Instrucciones de Instalación

### Opción 1: npm (recomendado)

```bash
cd frontend
npm install recharts
```

### Opción 2: yarn

```bash
cd frontend
yarn add recharts
```

## Verificación

Después de instalar, verifica que se haya agregado a tu `package.json`:

```json
"dependencies": {
  ...
  "recharts": "^2.x.x",
  ...
}
```

## Iniciar la aplicación

Una vez instalado recharts, puedes iniciar el frontend normalmente:

```bash
cd frontend
npm start
```

## Acceder al Dashboard

1. Inicia sesión como administrador
2. Ve al menú lateral
3. Click en "Dashboard Financiero" (icono 💵)
4. La ruta será `/reports`

## Troubleshooting

Si encuentras errores relacionados con recharts después de la instalación:

1. **Limpiar caché de npm**:
   ```bash
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   ```

2. **Verificar versión de Node**:
   - Recharts requiere Node.js >= 14
   - Verifica con: `node --version`

3. **Tipos de TypeScript**:
   - Los tipos para recharts están incluidos en el paquete
   - No necesitas instalar `@types/recharts` por separado

## Versión Recomendada

```json
"recharts": "^2.12.0"
```

Esta versión es estable y compatible con React 18+.
