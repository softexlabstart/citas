import React, { useState, useRef } from 'react';
import { Form, Dropdown, Badge, Button, Spinner } from 'react-bootstrap';

export interface Option {
    id: number | string;
    nombre: string;
    descripcion?: string;
}

interface MultiSelectDropdownProps {
    options: Option[];
    selected: string[];
    onChange: (selected: string[]) => void;
    label: string;
    placeholder: string;
    isLoading?: boolean;
    disabled?: boolean;
    searchPlaceholder?: string;
    showDescriptions?: boolean;
}

const MultiSelectDropdown: React.FC<MultiSelectDropdownProps> = ({
    options,
    selected,
    onChange,
    label,
    placeholder,
    isLoading = false,
    disabled = false,
    searchPlaceholder = 'Buscar...',
    showDescriptions = true
}) => {
    const [searchTerm, setSearchTerm] = useState('');
    const [show, setShow] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);

    const filteredOptions = options.filter(option =>
        option.nombre.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (showDescriptions && option.descripcion?.toLowerCase().includes(searchTerm.toLowerCase()))
    );

    const handleToggle = (id: string) => {
        if (selected.includes(id)) {
            onChange(selected.filter(s => s !== id));
        } else {
            onChange([...selected, id]);
        }
    };

    const handleClearAll = () => {
        onChange([]);
        setSearchTerm('');
    };

    const handleSelectAll = () => {
        onChange(filteredOptions.map(opt => String(opt.id)));
    };

    const selectedOptions = options.filter(s => selected.includes(String(s.id)));

    return (
        <div ref={dropdownRef}>
            <Form.Label>{label}</Form.Label>
            <Dropdown show={show} onToggle={(isOpen) => setShow(isOpen)}>
                <Dropdown.Toggle
                    variant="outline-secondary"
                    className="w-100 text-start d-flex justify-content-between align-items-center"
                    disabled={isLoading || disabled}
                >
                    <span className="text-truncate">
                        {isLoading ? (
                            <Spinner animation="border" size="sm" />
                        ) : selectedOptions.length > 0 ? (
                            `${selectedOptions.length} seleccionado(s)`
                        ) : (
                            placeholder
                        )}
                    </span>
                </Dropdown.Toggle>

                <Dropdown.Menu className="w-100" style={{ maxHeight: '400px', overflowY: 'auto' }}>
                    <div className="px-3 py-2" onClick={(e) => e.stopPropagation()}>
                        <Form.Control
                            type="text"
                            placeholder={searchPlaceholder}
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="mb-2"
                        />
                        <div className="d-flex gap-2 mb-2">
                            <Button
                                size="sm"
                                variant="outline-primary"
                                onClick={handleSelectAll}
                                disabled={filteredOptions.length === 0}
                            >
                                Seleccionar todos
                            </Button>
                            <Button
                                size="sm"
                                variant="outline-secondary"
                                onClick={handleClearAll}
                                disabled={selected.length === 0}
                            >
                                Limpiar
                            </Button>
                        </div>
                    </div>

                    <Dropdown.Divider />

                    {filteredOptions.length === 0 ? (
                        <div className="px-3 py-2 text-muted">
                            No se encontraron resultados
                        </div>
                    ) : (
                        filteredOptions.map((option) => (
                            <Dropdown.Item
                                key={option.id}
                                onClick={() => handleToggle(String(option.id))}
                                active={selected.includes(String(option.id))}
                            >
                                <Form.Check
                                    type="checkbox"
                                    id={`option-${option.id}`}
                                    checked={selected.includes(String(option.id))}
                                    onChange={() => {}}
                                    label={
                                        <div>
                                            <strong>{option.nombre}</strong>
                                            {showDescriptions && option.descripcion && (
                                                <>
                                                    <br />
                                                    <small className="text-muted">{option.descripcion}</small>
                                                </>
                                            )}
                                        </div>
                                    }
                                />
                            </Dropdown.Item>
                        ))
                    )}
                </Dropdown.Menu>
            </Dropdown>

            {/* Selected items badges */}
            {selectedOptions.length > 0 && (
                <div className="mt-2 d-flex flex-wrap gap-1">
                    {selectedOptions.map((option) => (
                        <Badge
                            key={option.id}
                            bg="primary"
                            className="d-flex align-items-center gap-1"
                            style={{ cursor: 'pointer' }}
                        >
                            {option.nombre}
                            <span
                                onClick={() => handleToggle(String(option.id))}
                                style={{ cursor: 'pointer', marginLeft: '4px' }}
                            >
                                ×
                            </span>
                        </Badge>
                    ))}
                </div>
            )}
        </div>
    );
};

export default MultiSelectDropdown;
