import React, { useState, useEffect } from 'react';
import { Dropdown, Spinner, Badge } from 'react-bootstrap';
import { useAuth } from '../contexts/AuthContext';
import { getUserOrganizations, switchOrganization } from '../api';
import { UserOrganization } from '../interfaces/Role';
import { toast } from 'react-toastify';
import RoleBadge from './RoleBadge';

const OrganizationSelector: React.FC = () => {
    const { selectedOrganization, selectOrganization } = useAuth();
    const [organizations, setOrganizations] = useState<UserOrganization[]>([]);
    const [loading, setLoading] = useState(true);
    const [switching, setSwitching] = useState(false);

    useEffect(() => {
        loadOrganizations();
    }, []);

    const loadOrganizations = async () => {
        setLoading(true);
        try {
            const response = await getUserOrganizations();
            if (response.data) {
                setOrganizations(response.data.organizations);
            }
        } catch (error: any) {
            console.error('Error loading organizations:', error);
            toast.error('Error al cargar las organizaciones');
        } finally {
            setLoading(false);
        }
    };

    const handleSwitchOrganization = async (org: UserOrganization) => {
        if (selectedOrganization?.id === org.id) {
            return; // Already selected
        }

        setSwitching(true);
        try {
            await switchOrganization(org.id);
            selectOrganization({
                id: org.id,
                nombre: org.nombre,
                slug: org.slug,
                perfil_id: 0 // This will be set by backend
            });
            toast.success(`Cambiado a organización: ${org.nombre}`);
            // Reload the page to refresh data for new organization
            window.location.reload();
        } catch (error: any) {
            console.error('Error switching organization:', error);
            toast.error('Error al cambiar de organización');
        } finally {
            setSwitching(false);
        }
    };

    if (loading) {
        return (
            <div className="d-flex align-items-center text-muted">
                <Spinner animation="border" size="sm" className="me-2" />
                <small>Cargando...</small>
            </div>
        );
    }

    // If user has only one organization, don't show selector
    if (organizations.length <= 1) {
        return null;
    }

    const currentOrg = selectedOrganization
        ? organizations.find(o => o.id === selectedOrganization.id)
        : organizations[0];

    return (
        <Dropdown align="end">
            <Dropdown.Toggle
                variant="outline-secondary"
                id="organization-selector"
                disabled={switching}
                className="d-flex align-items-center"
            >
                {switching ? (
                    <>
                        <Spinner animation="border" size="sm" className="me-2" />
                        Cambiando...
                    </>
                ) : (
                    <>
                        <i className="bi bi-building me-2"></i>
                        {currentOrg?.nombre || 'Seleccionar organización'}
                        {organizations.length > 1 && (
                            <Badge bg="secondary" className="ms-2">
                                {organizations.length}
                            </Badge>
                        )}
                    </>
                )}
            </Dropdown.Toggle>

            <Dropdown.Menu style={{ minWidth: '300px' }}>
                <Dropdown.Header>
                    <strong>Mis Organizaciones</strong>
                    <div className="text-muted small">
                        Selecciona para cambiar de contexto
                    </div>
                </Dropdown.Header>
                <Dropdown.Divider />

                {organizations.map((org) => (
                    <Dropdown.Item
                        key={org.id}
                        active={currentOrg?.id === org.id}
                        onClick={() => handleSwitchOrganization(org)}
                        className="py-2"
                    >
                        <div className="d-flex flex-column">
                            <div className="d-flex justify-content-between align-items-center mb-1">
                                <strong>{org.nombre}</strong>
                                {currentOrg?.id === org.id && (
                                    <i className="bi bi-check-circle-fill text-success"></i>
                                )}
                            </div>
                            <div className="small">
                                <RoleBadge
                                    role={org.role}
                                    additionalRoles={org.all_roles.filter(r => r !== org.role)}
                                    size="sm"
                                />
                            </div>
                        </div>
                    </Dropdown.Item>
                ))}

                <Dropdown.Divider />
                <Dropdown.Item disabled className="small text-muted">
                    <i className="bi bi-info-circle me-1"></i>
                    Tienes acceso a {organizations.length} organizaciones
                </Dropdown.Item>
            </Dropdown.Menu>
        </Dropdown>
    );
};

export default OrganizationSelector;
