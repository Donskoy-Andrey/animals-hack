import React, {useContext, useState, useEffect, useMemo} from "react";
import {FilesContext} from "../../contexts/FilesContext";
import {PhotoBox} from "../PhotoBox/PhotoBox";
import './PhotoGallery.css';
import {useNavigate} from "react-router-dom";
import {DownloadPdfButton} from "../DownloadPdfButton/DownloadPdfButton";
import ServerErrorToast from "../serverErrorToast/ServerErrorToast";
import {StatsContainer} from "../StatsContainer/StatsContainer";
import {ConfidenceLevelInput} from "../ConfidenceLevelInput/ConfidenceLevelInput";

export const PhotoGallery = () => {
    const navigate = useNavigate();
    const {processedFiles, error, confidenceLevel, stats} = useContext(FilesContext);

    // Состояния сортировки и фильтрации
    const [sortOption, setSortOption] = useState('name-asc');
    const [classFilter, setClassFilter] = useState('all');
    const [animalsFilter, setAnimalsFilter] = useState(['all']);
    const [cameraFilter, setCameraFilter] = useState(['all']);
    const [filtersOpen, setFiltersOpen] = useState(false);

    // Опции для фильтров
    const [animalOptions, setAnimalOptions] = useState(['all']);
    const [cameraOptions, setCameraOptions] = useState(['all']);

    useEffect(() => {
        const animalNamesSet = new Set();
        processedFiles.forEach(file => {
            file.border.forEach(borderItem => {
                if (borderItem.animal_name) {
                    animalNamesSet.add(borderItem.animal_name);
                }
            });
        });

        const uniqueAnimalNames = ['all', ...Array.from(animalNamesSet).sort()];
        setAnimalOptions(uniqueAnimalNames);
    }, [processedFiles]);

    useEffect(() => {
        const cameraNamesSet = new Set();
        processedFiles.forEach(file => {
            if (file.camera) {
                cameraNamesSet.add(file.camera);
            }
        });

        const uniqueCameraNames = ['all', ...Array.from(cameraNamesSet).sort()];
        setCameraOptions(uniqueCameraNames);
    }, [processedFiles]);

    const filteredPhotos = useMemo(() => {
        if (!Array.isArray(processedFiles)) return [];

        const updatedPhotos = processedFiles.map(file => {
            // Фильтрация бордеров по классу и животным
            const filteredBorders = file.border.filter(borderItem => {
                const classMatch = classFilter === 'all' || borderItem.object_class === parseInt(classFilter);
                const animalMatch = animalsFilter.includes('all') || animalsFilter.includes(borderItem.animal_name);
                return classMatch && animalMatch;
            });

            const cameraMatch = cameraFilter.includes('all') || cameraFilter.includes(file.camera);

            if (cameraMatch && filteredBorders.length > 0) {
                return {...file, border: filteredBorders};
            } else {
                return null;
            }
        }).filter(file => file !== null);

        // Сортировка
        return updatedPhotos.sort((a, b) => {
            switch (sortOption) {
                case 'name-asc':
                    return a.filename.toLowerCase().localeCompare(b.filename.toLowerCase());
                case 'name-desc':
                    return b.filename.toLowerCase().localeCompare(a.filename.toLowerCase());
                case 'date-asc':
                    return new Date(a.created_at) - new Date(b.created_at);
                case 'date-desc':
                    return new Date(b.created_at) - new Date(a.created_at);
                default:
                    return a.filename.toLowerCase().localeCompare(b.filename.toLowerCase());
            }
        });
    }, [processedFiles, sortOption, classFilter, animalsFilter, cameraFilter]);

    // Обработчики событий
    const handleSortChange = (e) => setSortOption(e.target.value);

    const handleFilterByClass = (selectedClass) => setClassFilter(selectedClass);

    const handleFilterByAnimals = (animalName) => {
        if (animalName === 'all') {
            setAnimalsFilter(['all']);
        } else {
            setAnimalsFilter(prev => {
                if (prev.includes('all')) {
                    return [animalName];
                }
                if (prev.includes(animalName)) {
                    const newFilters = prev.filter(name => name !== animalName);
                    return newFilters.length > 0 ? newFilters : ['all'];
                } else {
                    return [...prev, animalName];
                }
            });
        }
    };

    const handleFilterByCamera = (cameraName) => {
        if (cameraName === 'all') {
            setCameraFilter(['all']);
        } else {
            setCameraFilter(prev => {
                if (prev.includes('all')) {
                    return [cameraName];
                }
                if (prev.includes(cameraName)) {
                    const newFilters = prev.filter(name => name !== cameraName);
                    return newFilters.length > 0 ? newFilters : ['all'];
                } else {
                    return [...prev, cameraName];
                }
            });
        }
    };

    const isAnimalSelected = (animalName) => animalsFilter.includes(animalName);
    const isAllAnimalsSelected = () => animalsFilter.includes('all');

    const isCameraSelected = (cameraName) => cameraFilter.includes(cameraName);
    const isAllCamerasSelected = () => cameraFilter.includes('all');

    const toggleFilters = () => setFiltersOpen(!filtersOpen);

    return (
        <div className="main-page">
            {error && <ServerErrorToast />}
            <div className="results-header-container">
            <h1 className="results-header">Результаты обработки</h1>
            <DownloadPdfButton />
            </div>
            <div className="photo-gallery">
                <ConfidenceLevelInput />
                <div className="controls">
                    <StatsContainer buttonClassName={"btn class-select sort-button"}/>

                    <select
                        className="btn class-select sort-button"
                        value={sortOption}
                        onChange={handleSortChange}
                        aria-label="Сортировка"
                    >
                        <option value="name-asc">Сортировать по имени (A-Z)</option>
                        <option value="name-desc">Сортировать по имени (Z-A)</option>
                        <option value="date-asc">Сортировать по дате (старые сначала)</option>
                        <option value="date-desc">Сортировать по дате (новые сначала)</option>
                    </select>

                    <button className="btn filter-button" onClick={toggleFilters} aria-label="Открыть фильтры">
                        Фильтры
                    </button>
                </div>

                {filtersOpen && (
                    <div className="filters-panel">
                        <div className="filter-section">
                            <h3>Камера:</h3>
                            {cameraOptions.map((camera) => (
                                <label key={camera}>
                                    <input
                                        type="checkbox"
                                        checked={isCameraSelected(camera)}
                                        onChange={() => handleFilterByCamera(camera)}
                                        aria-label={camera}
                                    />
                                    {camera}
                                </label>
                            ))}
                        </div>

                        <div className="filter-section">
                            <h3>Классы:</h3>
                            {animalOptions.map((animal) => (
                                <label key={animal}>
                                    <input
                                        type="checkbox"
                                        checked={isAnimalSelected(animal)}
                                        onChange={() => handleFilterByAnimals(animal)}
                                        aria-label={animal}
                                    />
                                    {animal}
                                </label>
                            ))}
                        </div>
                    </div>
                )}

                {/* Отображение отфильтрованных фотографий */}
                <div className="photo-gallery-content">
                    {filteredPhotos.length > 0 && stats.total_files_without_objects !== stats.total_files_uploaded ? (
                        filteredPhotos.map((photo, index) => (
                            <div className="photo-gallery-item" key={index}>
                                <PhotoBox id={photo.filename} key={photo.id || photo.filename} processedFile={photo}/>
                                <div className="photo-description-container"
                                >
                                    <div className="photo-description-animal">
                                        <div className="photo-description-animal-header">
                                            <div className="photo-description-filename">
                                                <h2><code>{photo.filename}</code></h2>
                                            </div>
                                            <div className="photo-description-created-time">
                                                Дата: {new Date(photo.created_at).toLocaleString('ru-RU', {
                                                hour12: false,
                                                year: 'numeric',
                                                month: '2-digit',
                                                day: '2-digit',
                                                hour: '2-digit',
                                                minute: '2-digit'
                                            })}
                                            </div>
                                        </div>


                                    </div>
                                </div>
                            </div>
                        ))
                    ) : (
                        <div className="no-photos-container">
                            {processedFiles.length === 0 ? <p className="no-photos">Загрузите фотографии</p>
                                :
                                <p className="no-photos">Объекты не распознанны</p>
                            }
                            <button className="btn btn-secondary" onClick={() => navigate('/')}>На главную</button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
