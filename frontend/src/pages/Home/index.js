import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import HomeView from './view'; // Importa o visual

function HomePage() {
    // 1. Toda a Lógica (JavaScript puro)
    const navigate = useNavigate();
    const [course, setCourse] = useState('Enfermagem');

    const handleOptimize = () => {
        console.log("Enviando...");
        // lógica de fetch...
    };

    // 2. Retorna a Visualização
    return (
        <HomeView 
            course={course}
            setCourse={(e) => setCourse(e.target.value)}
            handleOptimize={handleOptimize}
            navigate={navigate}
        />
    );
}

export default HomePage;