import React, { useState } from 'react';
import { Container, Card } from 'react-bootstrap';
import LegalModal from '../components/LegalModal';

const PrivacyPolicyPage: React.FC = () => {
    const [showLegalModal, setShowLegalModal] = useState(false);
    return (
        <Container className="my-5">
            <Card className="shadow-sm">
                <Card.Body className="p-5">
                    <h1 className="mb-4">Política de Privacidad</h1>
                    <p className="text-muted">Última actualización: {new Date().toLocaleDateString('es-CO')}</p>

                    <section className="mb-4">
                        <h2 className="h4 mb-3">1. Introducción</h2>
                        <p>
                            En el Sistema de Gestión de Citas, respetamos su privacidad y nos comprometemos a proteger sus datos
                            personales. Esta Política de Privacidad explica cómo recopilamos, utilizamos, compartimos y protegemos
                            su información en cumplimiento con la Ley 1581 de 2012 de Colombia sobre Protección de Datos Personales.
                        </p>
                    </section>

                    <section className="mb-4">
                        <h2 className="h4 mb-3">2. Responsable del Tratamiento de Datos</h2>
                        <p>
                            <strong>Razón Social:</strong> [Softexlab]<br />
                            <strong>Email:</strong> info@softexlab.com<br />
                            <strong>Teléfono:</strong> +57 3193636323
                        </p>
                    </section>

                    <section className="mb-4">
                        <h2 className="h4 mb-3">3. Datos que Recopilamos</h2>
                        <p>Recopilamos los siguientes tipos de datos personales:</p>

                        <h5 className="mt-3">3.1 Datos de Identificación</h5>
                        <ul>
                            <li>Nombre completo</li>
                            <li>Correo electrónico</li>
                            <li>Número de teléfono</li>
                            <li>Ciudad y barrio</li>
                            <li>Fecha de nacimiento</li>
                            <li>Género</li>
                        </ul>

                        <h5 className="mt-3">3.2 Datos de la Cuenta</h5>
                        <ul>
                            <li>Nombre de usuario</li>
                            <li>Contraseña (encriptada)</li>                            <li>Rol de usuario</li>
                        </ul>

                        <h5 className="mt-3">3.3 Datos de Uso</h5>
                        <ul>
                            <li>Historial de citas</li>
                            <li>Servicios utilizados</li>
                            <li>Preferencias de usuario</li>
                            <li>Logs de acceso y actividad</li>
                        </ul>

                    </section>

                    <section className="mb-4">
                        <h2 className="h4 mb-3">4. Finalidad del Tratamiento de Datos</h2>
                        <p>Utilizamos sus datos personales para:</p>
                        <ul>
                            <li>Proporcionar y administrar el servicio de gestión de citas</li>
                            <li>Crear y mantener su cuenta de usuario</li>
                            <li>Procesar y confirmar reservas de citas</li>
                            <li>Enviar notificaciones y recordatorios por email</li>
                            <li>Generar reportes y análisis para su organización</li>
                            <li>Mejorar nuestros servicios y experiencia de usuario</li>
                            <li>Cumplir con obligaciones legales y regulatorias</li>
                            <li>Prevenir fraudes y garantizar la seguridad</li>
                            <li>Comunicarnos con usted sobre el servicio</li>
                            <li>Procesar pagos y facturación</li>
                        </ul>
                    </section>

                    <section className="mb-4">
                        <h2 className="h4 mb-3">5. Base Legal para el Tratamiento</h2>
                        <p>Procesamos sus datos personales con base en:</p>
                        <ul>
                            <li><strong>Consentimiento:</strong> Usted ha dado su consentimiento expreso al registrarse</li>
                            <li><strong>Ejecución de contrato:</strong> Para proporcionar el servicio contratado</li>
                            <li><strong>Obligación legal:</strong> Para cumplir con requisitos legales y fiscales</li>
                            <li><strong>Interés legítimo:</strong> Para mejorar nuestros servicios y prevenir fraudes</li>
                        </ul>
                    </section>

                    <section className="mb-4">
                        <h2 className="h4 mb-3">6. Compartir Datos con Terceros</h2>
                        <p>Podemos compartir sus datos con:</p>
                        <ul>
                            <li><strong>Proveedores de servicios:</strong> Hosting</li>
                            <li><strong>Autoridades:</strong> Cuando sea requerido por ley</li>
                        </ul>
                        <p>
                            <strong>No vendemos ni alquilamos sus datos personales a terceros.</strong>
                        </p>
                    </section>

                    <section className="mb-4">
                        <h2 className="h4 mb-3">7. Seguridad de los Datos</h2>
                        <p>Implementamos medidas de seguridad técnicas y organizativas para proteger sus datos:</p>
                        <ul>
                            <li>Encriptación de contraseñas (hash seguro)</li>
                            <li>Conexiones HTTPS/SSL</li>
                            <li>Acceso restringido a datos personales</li>
                            <li>Backups regulares</li>
                            <li>Monitoreo de seguridad continuo</li>
                        </ul>
                    </section>

                    <section className="mb-4">
                        <h2 className="h4 mb-3">8. Retención de Datos</h2>
                        <p>
                            Conservamos sus datos personales mientras su cuenta esté activa o según sea necesario para
                            proporcionar el servicio. Después de la cancelación de su cuenta, retendremos sus datos durante:
                        </p>
                        <ul>
                            <li><strong>Datos de cuenta:</strong> 90 días después de la cancelación</li>
                        </ul>
                    </section>

                    <section className="mb-4">
                        <h2 className="h4 mb-3">9. Sus Derechos (Ley 1581 de 2012)</h2>
                        <p>Como titular de datos personales, usted tiene derecho a:</p>
                        <ul>
                            <li><strong>Acceso:</strong> Conocer qué datos tenemos sobre usted</li>
                            <li><strong>Rectificación:</strong> Actualizar datos inexactos o incompletos</li>
                            <li><strong>Supresión:</strong> Solicitar la eliminación de sus datos</li>
                            <li><strong>Oposición:</strong> Oponerse al tratamiento de sus datos</li>
                            <li><strong>Revocación:</strong> Retirar su consentimiento en cualquier momento</li>
                            <li><strong>Portabilidad:</strong> Obtener una copia de sus datos en formato estructurado</li>
                            <li><strong>Presentar quejas:</strong> Ante la Superintendencia de Industria y Comercio</li>
                        </ul>
                        <p>
                            Para ejercer estos derechos, contáctenos en: <strong>privacidad@sistema-citas.com</strong>
                        </p>
                    </section>

                    <section className="mb-4">
                        <h2 className="h4 mb-3">10. Cookies y Tecnologías de Rastreo</h2>
                        <p>Utilizamos cookies y tecnologías similares para:</p>
                        <ul>
                            <li>Mantener su sesión activa</li>
                            <li>Recordar sus preferencias</li>
                            <li>Analizar el uso del servicio</li>
                            <li>Mejorar la seguridad</li>
                        </ul>
                        <p>
                            Puede configurar su navegador para rechazar cookies, pero esto puede afectar la funcionalidad
                            del servicio.
                        </p>
                    </section>

                    <section className="mb-4">
                        <h2 className="h4 mb-3">11. Transferencias Internacionales</h2>
                        <p>
                            Sus datos pueden ser transferidos y procesados en servidores ubicados fuera de Colombia.
                            Garantizamos que estas transferencias cumplan con las leyes de protección de datos aplicables
                            y que los proveedores mantengan estándares de seguridad adecuados.
                        </p>
                    </section>

                    <section className="mb-4">
                        <h2 className="h4 mb-3">12. Menores de Edad</h2>
                        <p>
                            Nuestro servicio no está dirigido a menores de 18 años. No recopilamos intencionalmente datos
                            personales de menores. Si un padre o tutor se da cuenta de que un menor ha proporcionado datos,
                            debe contactarnos para su eliminación inmediata.
                        </p>
                    </section>

                    <section className="mb-4">
                        <h2 className="h4 mb-3">13. Modificaciones a esta Política</h2>
                        <p>
                            Podemos actualizar esta Política de Privacidad ocasionalmente. Le notificaremos sobre cambios
                            significativos por email o mediante un aviso destacado en el servicio. La fecha de "última
                            actualización" al inicio del documento indicará cuándo se realizó el último cambio.
                        </p>
                    </section>

                    <section className="mb-4">
                        <h2 className="h4 mb-3">14. Contacto</h2>
                        <p>
                            Para preguntas sobre esta Política de Privacidad o el tratamiento de sus datos personales:
                        </p>
                        <ul>
                            <li><strong>Email de Privacidad:</strong>info@softexlab.com</li>
                            <li><strong>Email de Soporte:</strong> info@softexlab.com</li>
                            <li><strong>Teléfono:</strong> +57 319 363 6323</li>
                        </ul>
                    </section>

                    <div className="alert alert-success mt-4">
                        <h5 className="alert-heading">Consentimiento</h5>
                        <p className="mb-0">
                            Al utilizar nuestro servicio, usted declara haber leído y comprendido esta Política de Privacidad
                            y otorga su consentimiento libre, expreso e informado para el tratamiento de sus datos personales
                            conforme a lo establecido en este documento y en la Ley 1581 de 2012 de Colombia.
                        </p>
                    </div>

                    <div className="alert alert-info mt-3">
                        <strong>Referencias Legales:</strong>
                        <ul className="mb-0 mt-2">
                            <li>
                                <button
                                    onClick={() => setShowLegalModal(true)}
                                    className="btn btn-link p-0"
                                    style={{ textDecoration: 'none' }}
                                >
                                    Ley 1581 de 2012 - Protección de Datos Personales
                                </button>
                            </li>
                            <li>
                                <a href="https://www.sic.gov.co/" target="_blank" rel="noopener noreferrer">
                                    Superintendencia de Industria y Comercio (SIC)
                                </a>
                            </li>
                        </ul>
                    </div>
                </Card.Body>
            </Card>

            {/* Modal de Ley 1581 */}
            <LegalModal show={showLegalModal} onHide={() => setShowLegalModal(false)} />
        </Container>
    );
};

export default PrivacyPolicyPage;
