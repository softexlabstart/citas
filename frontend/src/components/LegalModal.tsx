import React from 'react';
import { Modal, Button } from 'react-bootstrap';

interface LegalModalProps {
    show: boolean;
    onHide: () => void;
}

const LegalModal: React.FC<LegalModalProps> = ({ show, onHide }) => {
    return (
        <Modal show={show} onHide={onHide} size="lg" scrollable>
            <Modal.Header closeButton>
                <Modal.Title>Ley 1581 de 2012 - Protección de Datos Personales</Modal.Title>
            </Modal.Header>
            <Modal.Body>
                <div className="legal-content">
                    <h5>Resumen de la Ley 1581 de 2012</h5>
                    <p>
                        La Ley 1581 de 2012 es la ley colombiana de protección de datos personales que establece
                        las disposiciones generales para la protección de datos personales en Colombia. Esta ley
                        regula cómo las empresas y organizaciones deben recolectar, almacenar, usar y proteger
                        la información personal de los ciudadanos.
                    </p>

                    <h6 className="mt-4">Tus Derechos como Titular de Datos</h6>
                    <p>Como titular de tus datos personales, la ley te otorga los siguientes derechos:</p>
                    <ul>
                        <li>
                            <strong>Derecho de Acceso:</strong> Conocer, actualizar y rectificar tus datos personales
                            frente a los responsables del tratamiento.
                        </li>
                        <li>
                            <strong>Derecho de Actualización:</strong> Solicitar la actualización de tu información
                            cuando esta sea inexacta, incompleta o haya sido actualizada.
                        </li>
                        <li>
                            <strong>Derecho de Rectificación:</strong> Solicitar la corrección de tus datos cuando
                            sean incorrectos.
                        </li>
                        <li>
                            <strong>Derecho de Supresión:</strong> Solicitar la eliminación de tus datos cuando
                            consideres que no están siendo tratados conforme a la ley.
                        </li>
                        <li>
                            <strong>Derecho de Revocación:</strong> Revocar la autorización otorgada para el
                            tratamiento de tus datos personales.
                        </li>
                        <li>
                            <strong>Derecho a Presentar Quejas:</strong> Presentar quejas ante la Superintendencia
                            de Industria y Comercio (SIC) por infracciones a la ley.
                        </li>
                    </ul>

                    <h6 className="mt-4">Cómo Aplicamos la Ley 1581 en Nuestra Plataforma</h6>
                    <p>En cumplimiento con la Ley 1581 de 2012, nuestra plataforma:</p>
                    <ul>
                        <li>
                            <strong>Obtiene tu Consentimiento:</strong> Solicitamos tu autorización expresa antes
                            de recolectar y procesar tus datos personales a través de nuestro formulario de registro
                            y las casillas de consentimiento.
                        </li>
                        <li>
                            <strong>Informa sobre el Uso:</strong> Te explicamos claramente qué datos recolectamos,
                            para qué los usamos, y con quién los compartimos en nuestra Política de Privacidad.
                        </li>
                        <li>
                            <strong>Protege tu Información:</strong> Implementamos medidas técnicas y administrativas
                            para proteger tus datos contra acceso no autorizado, pérdida, o uso indebido.
                        </li>
                        <li>
                            <strong>Respeta tus Derechos:</strong> Facilitamos mecanismos para que puedas ejercer
                            tus derechos de acceso, rectificación, actualización, y supresión de tus datos.
                        </li>
                        <li>
                            <strong>Limita el Uso:</strong> Solo usamos tus datos para los fines autorizados y
                            relacionados con la prestación de nuestros servicios de gestión de citas.
                        </li>
                        <li>
                            <strong>Establece Períodos de Retención:</strong> Conservamos tus datos solo durante
                            el tiempo necesario para cumplir con las finalidades para las cuales fueron recolectados.
                        </li>
                    </ul>

                    <h6 className="mt-4">Principios que Seguimos</h6>
                    <p>Nuestro tratamiento de datos personales se rige por los siguientes principios establecidos en la ley:</p>
                    <ul>
                        <li><strong>Legalidad:</strong> Cumplimos con todas las disposiciones legales vigentes.</li>
                        <li><strong>Finalidad:</strong> Recolectamos datos para propósitos específicos y legítimos.</li>
                        <li><strong>Libertad:</strong> Solo tratamos datos con tu consentimiento libre y voluntario.</li>
                        <li><strong>Veracidad:</strong> La información que tratamos debe ser completa, exacta y actualizada.</li>
                        <li><strong>Transparencia:</strong> Te informamos claramente sobre el tratamiento de tus datos.</li>
                        <li><strong>Seguridad:</strong> Protegemos tus datos con medidas técnicas y administrativas.</li>
                        <li><strong>Confidencialidad:</strong> Todas las personas que tienen acceso a tus datos están obligadas a mantener la confidencialidad.</li>
                    </ul>

                    <h6 className="mt-4">Datos que NO Recolectamos</h6>
                    <p>
                        En cumplimiento con los principios de minimización y finalidad, NO recolectamos datos
                        sensibles como información sobre tu origen racial, orientación sexual, opiniones políticas,
                        datos biométricos, o información de salud, salvo que sea estrictamente necesario para
                        la prestación del servicio específico que hayas solicitado y cuentes con tu autorización expresa.
                    </p>

                    <h6 className="mt-4">Cómo Ejercer tus Derechos</h6>
                    <p>
                        Si deseas ejercer cualquiera de tus derechos establecidos en la Ley 1581 de 2012, puedes:
                    </p>
                    <ul>
                        <li>Acceder a tu perfil de usuario y actualizar tu información directamente.</li>
                        <li>Enviarnos un correo electrónico a la dirección de contacto indicada en nuestra Política de Privacidad.</li>
                        <li>Solicitar la eliminación de tu cuenta y datos asociados desde la configuración de tu perfil.</li>
                    </ul>
                    <p>
                        Responderemos a tu solicitud en un plazo máximo de 15 días hábiles, según lo establece la ley.
                        Si tu solicitud no puede ser atendida en este plazo, te informaremos las razones y la
                        fecha estimada en que atenderemos tu solicitud.
                    </p>

                    <h6 className="mt-4">Autoridad de Control</h6>
                    <p>
                        La autoridad encargada de velar por el cumplimiento de la Ley 1581 de 2012 es la
                        <strong> Superintendencia de Industria y Comercio (SIC)</strong>. Si consideras que
                        tus derechos han sido vulnerados, puedes presentar una queja ante esta entidad a través
                        de su sitio web: <a href="https://www.sic.gov.co" target="_blank" rel="noopener noreferrer">www.sic.gov.co</a>
                    </p>

                    <div className="alert alert-info mt-4">
                        <strong>Nota:</strong> Esta información es un resumen educativo de la Ley 1581 de 2012
                        y cómo la aplicamos en nuestra plataforma. Para conocer el texto completo de la ley,
                        puedes consultar el sitio web de la Función Pública de Colombia. Nuestra Política de
                        Privacidad completa contiene información detallada sobre cómo tratamos tus datos personales.
                    </div>
                </div>
            </Modal.Body>
            <Modal.Footer>
                <Button variant="secondary" onClick={onHide}>
                    Cerrar
                </Button>
                <Button variant="primary" href="/privacy-policy">
                    Ver Política de Privacidad Completa
                </Button>
            </Modal.Footer>
        </Modal>
    );
};

export default LegalModal;
