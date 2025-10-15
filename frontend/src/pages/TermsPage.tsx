import React from 'react';
import { Container, Card } from 'react-bootstrap';

const TermsPage: React.FC = () => {
    return (
        <Container className="my-5">
            <Card className="shadow-sm">
                <Card.Body className="p-5">
                    <h1 className="mb-4">Términos y Condiciones</h1>
                    <p className="text-muted">Última actualización: {new Date().toLocaleDateString('es-CO')}</p>

                    <section className="mb-4">
                        <h2 className="h4 mb-3">1. Aceptación de los Términos</h2>
                        <p>
                            Al acceder y utilizar el Sistema de Gestión de Citas (en adelante, "el Servicio"), usted acepta
                            cumplir con estos Términos y Condiciones. Si no está de acuerdo con alguna parte de estos términos,
                            no debe utilizar el Servicio.
                        </p>
                    </section>

                    <section className="mb-4">
                        <h2 className="h4 mb-3">2. Descripción del Servicio</h2>
                        <p>
                            El Servicio es una plataforma SaaS (Software como Servicio) que permite a las organizaciones gestionar
                            citas, servicios, colaboradores y clientes. El Servicio incluye:
                        </p>
                        <ul>
                            <li>Sistema de gestión de citas y calendario</li>
                            <li>Gestión de múltiples sedes y servicios</li>
                            <li>Portal para clientes y colaboradores</li>
                            <li>Reportes y análisis de datos</li>
                            <li>Notificaciones por correo electrónico</li>
                        </ul>
                    </section>

                    <section className="mb-4">
                        <h2 className="h4 mb-3">3. Registro y Cuenta de Usuario</h2>
                        <p>
                            Para utilizar ciertas funciones del Servicio, debe crear una cuenta. Usted es responsable de:
                        </p>
                        <ul>
                            <li>Mantener la confidencialidad de su contraseña</li>
                            <li>Todas las actividades que ocurran bajo su cuenta</li>
                            <li>Notificarnos inmediatamente sobre cualquier uso no autorizado</li>
                            <li>Proporcionar información precisa y actualizada</li>
                        </ul>
                    </section>

                    <section className="mb-4">
                        <h2 className="h4 mb-3">4. Uso Aceptable</h2>
                        <p>Usted se compromete a NO:</p>
                        <ul>
                            <li>Utilizar el Servicio para actividades ilegales o fraudulentas</li>
                            <li>Intentar acceder a sistemas o datos no autorizados</li>
                            <li>Interferir con el funcionamiento del Servicio</li>
                            <li>Transmitir virus, malware o código malicioso</li>
                            <li>Realizar ingeniería inversa del software</li>
                            <li>Revender o redistribuir el Servicio sin autorización</li>
                        </ul>
                    </section>

                    <section className="mb-4">
                        <h2 className="h4 mb-3">5. Planes y Pagos</h2>
                        <p>
                            El Servicio ofrece diferentes planes de suscripción. Los precios están sujetos a cambios con previo
                            aviso de 30 días. Los pagos se procesan de forma segura a través de proveedores de pago certificados.
                        </p>
                        <p>
                            <strong>Política de Cancelación:</strong> Puede cancelar su suscripción en cualquier momento.
                            No se realizan reembolsos por períodos parciales, pero mantendrá acceso hasta el final del período pagado.
                        </p>
                    </section>

                    <section className="mb-4">
                        <h2 className="h4 mb-3">6. Propiedad Intelectual</h2>
                        <p>
                            Todo el contenido, características y funcionalidad del Servicio son propiedad exclusiva de la empresa
                            y están protegidos por las leyes de propiedad intelectual de Colombia y tratados internacionales.
                        </p>
                        <p>
                            Los datos que usted introduce en el Servicio le pertenecen. Nos otorga una licencia para procesarlos
                            únicamente con el propósito de proporcionar el Servicio.
                        </p>
                    </section>

                    <section className="mb-4">
                        <h2 className="h4 mb-3">7. Protección de Datos</h2>
                        <p>
                            El tratamiento de sus datos personales se rige por nuestra{' '}
                            <a href="/privacy-policy">Política de Privacidad</a> y cumple con la Ley 1581 de 2012 de Colombia
                            sobre Protección de Datos Personales.
                        </p>
                    </section>

                    <section className="mb-4">
                        <h2 className="h4 mb-3">8. Disponibilidad del Servicio</h2>
                        <p>
                            Nos esforzamos por mantener el Servicio disponible 24/7, pero no garantizamos que estará libre de
                            interrupciones, retrasos o errores. Nos reservamos el derecho de:
                        </p>
                        <ul>
                            <li>Realizar mantenimiento programado con previo aviso</li>
                            <li>Modificar o discontinuar características del Servicio</li>
                            <li>Actualizar el software y la infraestructura</li>
                        </ul>
                    </section>

                    <section className="mb-4">
                        <h2 className="h4 mb-3">9. Limitación de Responsabilidad</h2>
                        <p>
                            El Servicio se proporciona "tal cual" y "según disponibilidad". En la máxima medida permitida por la ley,
                            no seremos responsables por:
                        </p>
                        <ul>
                            <li>Pérdida de datos o beneficios</li>
                            <li>Daños indirectos, incidentales o consecuentes</li>
                            <li>Interrupciones del servicio</li>
                            <li>Errores u omisiones en el contenido</li>
                        </ul>
                    </section>

                    <section className="mb-4">
                        <h2 className="h4 mb-3">10. Terminación</h2>
                        <p>
                            Podemos suspender o terminar su acceso al Servicio inmediatamente, sin previo aviso, si:
                        </p>
                        <ul>
                            <li>Viola estos Términos y Condiciones</li>
                            <li>No realiza los pagos correspondientes</li>
                            <li>Utiliza el Servicio de manera fraudulenta o abusiva</li>
                        </ul>
                    </section>

                    <section className="mb-4">
                        <h2 className="h4 mb-3">11. Modificaciones</h2>
                        <p>
                            Nos reservamos el derecho de modificar estos términos en cualquier momento. Las modificaciones
                            entrarán en vigor al publicarse en el Servicio. El uso continuado del Servicio después de las
                            modificaciones constituye su aceptación de los nuevos términos.
                        </p>
                    </section>

                    <section className="mb-4">
                        <h2 className="h4 mb-3">12. Ley Aplicable y Jurisdicción</h2>
                        <p>
                            Estos términos se rigen por las leyes de la República de Colombia. Cualquier disputa se resolverá
                            en los tribunales competentes de Colombia.
                        </p>
                    </section>

                    <section className="mb-4">
                        <h2 className="h4 mb-3">13. Contacto</h2>
                        <p>
                            Si tiene preguntas sobre estos Términos y Condiciones, puede contactarnos a través de:
                        </p>
                        <ul>
                            <li>Email: info@softexlab.com</li>
                            <li>Teléfono: +57 3193636323</li>
                        </ul>
                    </section>

                    <div className="alert alert-info mt-4">
                        <strong>Nota:</strong> Al utilizar este servicio, usted confirma que ha leído, comprendido y
                        aceptado estos Términos y Condiciones en su totalidad.
                    </div>
                </Card.Body>
            </Card>
        </Container>
    );
};

export default TermsPage;
