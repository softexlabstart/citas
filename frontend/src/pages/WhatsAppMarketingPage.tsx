import React, { useState, useEffect } from 'react';
import { Container, Form, Button, Spinner, Alert, Card, Image } from 'react-bootstrap';
import { useTranslation } from 'react-i18next';
import { toast } from 'react-toastify';
import { useApi } from '../hooks/useApi';
import { sendMarketingWhatsApp, getClients } from '../api';
import { Client } from '../interfaces/Client';

const WhatsAppMarketingPage: React.FC = () => {
    const { t } = useTranslation();
    const [message, setMessage] = useState('');
    const [image, setImage] = useState<File | null>(null);
    const [imagePreview, setImagePreview] = useState<string | null>(null);
    const [clients, setClients] = useState<Client[]>([]);
    const [selectedClientPhones, setSelectedClientPhones] = useState<string[]>([]);
    const [selectAll, setSelectAll] = useState(false);
    const [consentFilter, setConsentFilter] = useState<string>('all');
    const [sending, setSending] = useState(false);
    const { request: fetchClientsApi } = useApi(getClients);

    useEffect(() => {
        const fetchClients = async () => {
            try {
                const filterParam = consentFilter === 'all' ? undefined : consentFilter;
                const response = await fetchClientsApi(filterParam);
                type PaginatedResponse<T> = { results: T[] };
                const data = response.data as Client[] | PaginatedResponse<Client>;
                if (Array.isArray(data)) {
                    setClients(data);
                } else if ('results' in data && Array.isArray(data.results)) {
                    setClients(data.results);
                } else {
                    setClients([]);
                }
                setSelectedClientPhones([]);
                setSelectAll(false);
            } catch (err) {
                console.error('Error fetching clients:', err);
                toast.error('Error al cargar clientes');
            }
        };
        fetchClients();
    }, [fetchClientsApi, consentFilter]);

    const handleClientSelect = (phone: string) => {
        setSelectedClientPhones((prevSelected) =>
            prevSelected.includes(phone)
                ? prevSelected.filter((p) => p !== phone)
                : [...prevSelected, phone]
        );
    };

    const handleSelectAll = () => {
        if (selectAll) {
            setSelectedClientPhones([]);
        } else {
            const phonesWithNumber = clients
                .filter(client => client.telefono)
                .map(client => client.telefono);
            setSelectedClientPhones(phonesWithNumber);
        }
        setSelectAll(!selectAll);
    };

    const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            // Validar tamaño (max 5MB)
            if (file.size > 5 * 1024 * 1024) {
                toast.error('La imagen no puede superar 5MB');
                return;
            }

            // Validar tipo
            const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
            if (!allowedTypes.includes(file.type)) {
                toast.error('Tipo de archivo no permitido. Use JPG, PNG, GIF o WebP');
                return;
            }

            setImage(file);

            // Crear preview
            const reader = new FileReader();
            reader.onloadend = () => {
                setImagePreview(reader.result as string);
            };
            reader.readAsDataURL(file);
        }
    };

    const removeImage = () => {
        setImage(null);
        setImagePreview(null);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!message) {
            toast.error('El mensaje es requerido');
            return;
        }

        if (selectedClientPhones.length === 0) {
            toast.warning('Selecciona al menos un cliente');
            return;
        }

        setSending(true);

        try {
            const formData = new FormData();
            formData.append('message', message);

            if (image) {
                formData.append('image', image);
            }

            // Enviar solo los teléfonos seleccionados
            selectedClientPhones.forEach(phone => {
                formData.append('recipient_phones', phone);
            });

            const response = await sendMarketingWhatsApp(formData);

            if (response.data) {
                const { sent, failed, total } = response.data;
                toast.success(`WhatsApp enviado: ${sent} exitosos, ${failed} fallidos de ${total} total`);

                // Limpiar formulario
                setMessage('');
                setImage(null);
                setImagePreview(null);
                setSelectedClientPhones([]);
                setSelectAll(false);
            }
        } catch (error: any) {
            const errorMsg = error.response?.data?.error || 'Error al enviar WhatsApp';
            toast.error(errorMsg);
        } finally {
            setSending(false);
        }
    };

    return (
        <Container className="mt-5">
            <h2>📱 Marketing por WhatsApp</h2>
            <p>Envía mensajes promocionales por WhatsApp a tus clientes. Puedes incluir imágenes.</p>

            <Form onSubmit={handleSubmit}>
                <Form.Group className="mb-3" controlId="message">
                    <Form.Label>Mensaje</Form.Label>
                    <Form.Control
                        as="textarea"
                        rows={8}
                        value={message}
                        onChange={(e) => setMessage(e.target.value)}
                        placeholder="Escribe tu mensaje aquí..."
                        required
                    />
                    <Form.Text className="text-muted">
                        Puedes usar emojis y saltos de línea para darle formato.
                    </Form.Text>
                </Form.Group>

                <Form.Group className="mb-3" controlId="image">
                    <Form.Label>Imagen (opcional)</Form.Label>
                    <Form.Control
                        type="file"
                        accept="image/jpeg,image/jpg,image/png,image/gif,image/webp"
                        onChange={handleImageChange}
                        disabled={sending}
                    />
                    <Form.Text className="text-muted">
                        Formatos permitidos: JPG, PNG, GIF, WebP. Tamaño máximo: 5MB
                    </Form.Text>
                </Form.Group>

                {imagePreview && (
                    <Card className="mb-3" style={{ maxWidth: '400px' }}>
                        <Card.Body>
                            <Card.Title>Vista previa</Card.Title>
                            <Image src={imagePreview} fluid rounded />
                            <Button
                                variant="outline-danger"
                                size="sm"
                                className="mt-2"
                                onClick={removeImage}
                            >
                                Quitar imagen
                            </Button>
                        </Card.Body>
                    </Card>
                )}

                <Card className="mb-3">
                    <Card.Header>
                        <div className="d-flex justify-content-between align-items-center">
                            <span>Seleccionar destinatarios</span>
                            <Form.Select
                                value={consentFilter}
                                onChange={(e) => setConsentFilter(e.target.value)}
                                style={{ width: 'auto', marginLeft: '10px' }}
                                size="sm"
                            >
                                <option value="all">Todos los clientes</option>
                                <option value="true">Con consentimiento ✓</option>
                                <option value="false">Sin consentimiento ✗</option>
                            </Form.Select>
                        </div>
                    </Card.Header>
                    <Card.Body style={{ maxHeight: '300px', overflowY: 'auto' }}>
                        <Form.Check
                            type="checkbox"
                            id="selectAllClients"
                            label="Seleccionar todos los clientes con teléfono"
                            checked={selectAll}
                            onChange={handleSelectAll}
                            className="mb-2"
                        />
                        {clients.length === 0 ? (
                            <p className="text-muted text-center">No hay clientes con este filtro</p>
                        ) : (
                            clients.map((client) => {
                                const hasPhone = !!client.telefono;
                                return (
                                    <Form.Check
                                        type="checkbox"
                                        id={`client-${client.id}`}
                                        key={client.id}
                                        label={
                                            <span>
                                                {client.first_name} {client.last_name}
                                                {hasPhone ? (
                                                    <span className="text-muted ms-2">({client.telefono})</span>
                                                ) : (
                                                    <span className="text-danger ms-2">(Sin teléfono)</span>
                                                )}
                                                {client.has_consented_data_processing ? (
                                                    <span className="text-success ms-2" title="Aceptó políticas">✓</span>
                                                ) : (
                                                    <span className="text-warning ms-2" title="No aceptó políticas">⚠</span>
                                                )}
                                            </span>
                                        }
                                        checked={hasPhone && selectedClientPhones.includes(client.telefono)}
                                        onChange={() => hasPhone && handleClientSelect(client.telefono)}
                                        disabled={!hasPhone}
                                    />
                                );
                            })
                        )}
                    </Card.Body>
                    <Card.Footer className="text-muted">
                        {selectedClientPhones.length} cliente(s) seleccionado(s)
                    </Card.Footer>
                </Card>

                <Button variant="success" type="submit" disabled={sending}>
                    {sending ? (
                        <>
                            <Spinner as="span" animation="border" size="sm" className="me-2" />
                            Enviando...
                        </>
                    ) : (
                        '📤 Enviar WhatsApp'
                    )}
                </Button>
            </Form>
        </Container>
    );
};

export default WhatsAppMarketingPage;
